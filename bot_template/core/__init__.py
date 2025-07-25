import asyncio
from asyncio import AbstractEventLoop
from typing import Awaitable, List

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)
from aiohttp import web

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ImportError:
    pass
from loguru import logger

from bot_template.core.config_manager import ConfigManager
from bot_template.core.loader import ModuleLoader
from bot_template.core.task_manager import (
    BaseCoreTask,
    BaseSchedulerTask,
    TaskManager,
)


class BotCore:
    __slots__ = [
        "project_name",
        "is_prod",
        "dp",
        "bots",
        "loop",
        "config",
        "webhook",
        "task_manager",
        "webhook_paths",
    ]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        project_name: str,
        is_prod: bool,
        dp: Dispatcher,  # pylint: disable=invalid-name
        bot: List[Bot] | Bot,
        loop: AbstractEventLoop,
        config: ConfigManager,
        scheduler: "AsyncIOScheduler" = None,
    ) -> None:
        logger.info(f"Initializing {project_name}...")
        self.project_name = project_name
        self.is_prod = is_prod
        self.dp = dp  # pylint: disable=invalid-name
        self.bots = [bot] if not isinstance(bot, list) else bot
        self.loop = loop
        self.config = config
        self.webhook = config.get_item("features", "use_webhook")
        self.task_manager = TaskManager(self.loop, scheduler)
        self.webhook_paths = self.config.get_item("telegram", "bots")
        self.webhook_paths = [
            _bot.get("webhook_path") for _bot in self.webhook_paths
        ]

        if self.dp is not None:
            self.dp["core"] = self

    def add_core_task(self, task: BaseCoreTask):
        """Add core task to run. Core tasks running once on startup

        Args:
            task (BaseCoreTask): Task object
        """
        self.task_manager.add_core_task(task)

    def add_core_tasks(self, *args: BaseCoreTask):
        """Add multiple core tasks. Core tasks running once on startup"""
        self.task_manager.add_core_tasks(*args)

    def __run_core_tasks(self):
        """Run core tasks"""
        return self.task_manager.run_core_tasks()

    def add_scheduler_task(self, task: BaseSchedulerTask):
        """Add scheduler task to run

        Args:
            task (BaseSchedulerTask): Task object
        """
        self.task_manager.add_scheduler_task(task)

    def add_scheduler_tasks(self, *args: BaseSchedulerTask):
        """Add multiple scheduler tasks"""
        self.task_manager.add_scheduler_tasks(*args)

    def push_pending_scheduler_tasks(self):
        """Push pending scheduler tasks to scheduler

        Raises:
            FeatureUnavailableError: feature use_apscheduler required in order to call this method
        """
        return self.task_manager.push_pending_scheduler_tasks()

    def cancel_scheduler_task(self, task_name: str) -> bool:
        """Cancel scheduler task

        Args:
            task_name (str): task name

        Raises:
            FeatureUnavailableError: feature use_apscheduler required in order to call this method

        Returns:
            bool: success
        """
        return self.task_manager.cancel_scheduler_task(task_name)

    async def _startup(self, dispatcher: Dispatcher):
        """Main startup logic

        Args:
            dispatcher (Dispatcher): aiogram dispatcher object
        """
        if self.config.get_item("features", "use_modern_callback"):
            from bot_template.keyboards.middlewares import (  # pylint: disable=import-outside-toplevel
                CallbackButtonMiddleware,
            )

            dispatcher.callback_query.outer_middleware(
                CallbackButtonMiddleware()
            )
        if self.config.get_item("features", "use_sulguk"):
            from sulguk import (  # pylint: disable=import-outside-toplevel
                AiogramSulgukMiddleware,
            )

            for bot in self.bots:
                bot.session.middleware(AiogramSulgukMiddleware())

        ModuleLoader(self.project_name, self.is_prod, self.config).load_all()

        try:
            from bot_template.keyboards.models.base import (  # pylint: disable=import-outside-toplevel
                ButtonRegistry,
            )

            ButtonRegistry.register_buttons()
        except ImportError as e:
            logger.exception(e)

        if self.config.get_item("features", "use_database"):
            from bot_template import (  # pylint: disable=import-outside-toplevel
                db,
            )

            await db.init_database()

        if self.task_manager and self.task_manager.scheduler:
            self.task_manager.scheduler.start()
            self.push_pending_scheduler_tasks()

        self.__run_core_tasks()

    async def _shutdown(self, dispatcher: Dispatcher):
        """Main shutdown logic

        Args:
            dispatcher (Dispatcher): aiogram dispatcher object
        """
        logger.warning("Closing Redis instance...")
        await dispatcher.storage.close()
        logger.info("Redis instance closed!")

    async def _startup_webhook(self, dispatcher: Dispatcher) -> Awaitable:
        """Startup logic for webhook

        Args:
            dispatcher (Dispatcher): aiogram dispatcher object

        Returns:
            Awaitable: main startup logic
        """

        skip_updates = self.config.get_item("telegram", "skip_updates")

        async def set_bot_settings(bot: Bot, webhook_path: str):
            if skip_updates:
                await bot.delete_webhook(True)

            webhook_url = f"{self.config.get_item('features.webhook', 'host')}{webhook_path}"
            webhook_info = await bot.get_webhook_info()
            # print(webhook_info)
            if (
                webhook_url != webhook_info.url
                or webhook_info.max_connections != 100
            ):
                await bot.set_webhook(
                    webhook_url,
                    max_connections=100,
                    drop_pending_updates=skip_updates,
                )

        await asyncio.gather(
            *[
                set_bot_settings(bot, self.webhook_paths[index])
                for index, bot in enumerate(self.bots)
            ]
        )

        return await self._startup(dispatcher)

    async def _startup_polling(self, dispatcher: Dispatcher) -> Awaitable:
        """Startup logic for polling

        Args:
            dispatcher (Dispatcher): aiogram dispatcher object

        Returns:
            Awaitable: main startup logic
        """

        skip_updates = self.config.get_item("telegram", "skip_updates")

        async def set_bot_settings(bot: Bot):
            # print(await bot.me())
            webhook_info = await bot.get_webhook_info()

            if webhook_info.url or skip_updates:
                await bot.delete_webhook(
                    self.config.get_item("telegram", "skip_updates")
                )

        await asyncio.gather(*[set_bot_settings(bot) for bot in self.bots])

        return await self._startup(dispatcher)

    def start(self):
        """Start bot"""
        logger.info(f"Starting {self.project_name}...")
        if self.webhook:
            self.dp.startup.register(self._startup_webhook)
            self.dp.shutdown.register(self._shutdown)
            app = web.Application()
            for index, bot in enumerate(self.bots):
                webhook_requests_handler = SimpleRequestHandler(self.dp, bot)
                webhook_requests_handler.register(
                    app, path=self.webhook_paths[index]
                )
                setup_application(app, self.dp, bot=bot)
            web.run_app(
                app=app,
                host=self.config.get_item("features.webhook", "webapp_host"),
                port=self.config.get_item("features.webhook", "webapp_port"),
            )
        else:
            self.dp.startup.register(self._startup_polling)
            self.dp.shutdown.register(self._shutdown)
            self.loop.run_until_complete(self.dp.start_polling(*self.bots))
