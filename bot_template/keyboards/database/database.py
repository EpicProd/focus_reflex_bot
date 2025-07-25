import os
import pickle
import random
import time
from base64 import b64encode
from datetime import datetime, timedelta
from pathlib import Path
from string import ascii_letters
from typing import Optional, Union

from loguru import logger
from sqlalchemy import NullPool

try:
    import sqlalchemy
    from sqlalchemy import delete, exc, select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from bot_template.keyboards.database.models import Base, Callback
except ImportError:
    Base = None

from bot_template import config, loop

if Base:

    async def init_database():
        if not Path("static").exists():
            cgroup = Path("/proc/self/cgroup")
            if not (
                Path("/.dockerenv").is_file()
                or cgroup.is_file()
                and cgroup.read_text(encoding="utf-8").find("docker") > -1
            ):  # Check if NOT running in a docker container
                os.makedirs("static")
            else:
                logger.error(
                    "static directory not available on a host machine!"
                )
        async with db.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    if config.get_item("features", "use_modern_callback"):
        db = create_async_engine(
            sqlalchemy.engine.URL.create(
                drivername=config.get_item(
                    "features.modern_callback", "driver"
                ),
                username=config.get_item(
                    "features.modern_callback", "username"
                ),
                password=config.get_item(
                    "features.modern_callback", "password"
                ),
                host=config.get_item("features.modern_callback", "addr"),
                port=config.get_item("features.modern_callback", "port"),
                database=config.get_item(
                    "features.modern_callback", "database_name"
                ),
            ),
            future=True,
            pool=NullPool
            if config.get_item("features.modern_callback", "driver")
            != "sqlite+aiosqlite"
            else None,
        )  # noqa: e126

        Session: AsyncSession = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=db,
            future=True,
            class_=AsyncSession,
        )

        loop.create_task(init_database())

    async def delete_callback(data: str) -> bool:
        async with Session() as conn:
            await conn.execute(delete(Callback).where(Callback.query == data))
            await conn.commit()

    async def add_callback(data: str, additional_data: dict) -> Callback:
        async with Session() as session:
            key = "".join([random.choice(ascii_letters) for _ in range(12)])
            callback = Callback(
                query=key,
                original_query=data,
                data=b64encode(pickle.dumps(additional_data)).decode(),
                die_time=(datetime.utcnow() + timedelta(days=7)).timestamp(),
            )
            session.add(callback)
            await session.commit()
        return callback

    async def get_callback(data: str) -> Optional[Union[Callback, str]]:
        async with Session() as session:
            try:
                callback: Callback = (
                    (
                        await session.execute(
                            select(Callback).filter_by(query=data)
                        )
                    )
                    .unique()
                    .scalar_one()
                )
            except exc.NoResultFound:
                return None
            if callback.die_time < time.time():
                await delete_callback(data)
                return "died"
        return callback
