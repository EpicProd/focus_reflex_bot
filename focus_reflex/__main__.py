from loguru import logger

from focus_reflex import (
    PROJECT_NAME,
    bots,
    config,
    dp,
    features,
    is_custom_server,
    is_prod,
    loop,
    scheduler,
)
from focus_reflex.core import BotCore
from focus_reflex.daemons import SendQuestionsTask, CheckLinkedChannelsTask

logger.info(
    f"Using features: {', '.join([x.split('_', maxsplit=1)[1] for x, _ in features if x.startswith('use')])}"
)
if is_prod:
    logger.warning("Running in production!")
if is_custom_server:
    logger.warning(
        f"Using custom BotAPI server: {config.get_item('features.custom_server', 'server')}"
    )

core = BotCore(PROJECT_NAME, is_prod, dp, bots, loop, config, scheduler)

core.add_scheduler_task(SendQuestionsTask())
core.add_scheduler_task(CheckLinkedChannelsTask())

core.start()
