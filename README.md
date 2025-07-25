# rf0x3d's telegram bot template
not so slight, but really fast

## mainly used libraries:
* aiogram - heart of a bot
* sqlalchemy w/ asyncpg & aiosqlite - memory of a bot
* apscheduler - task scheduler of a bot
* loguru - mouth of a bot

## features:
* automatic module loader - modular system has always been the most convenient to develop
* core tasks - code that can be executed on startup (for example, web server)
* scheduler tasks - apscheduler wrapper
* improved keyboards module - slight, fast, extended
* important utils and middlewares out of the box

project is being developed for personal use, so any suggestions aren't accepted if they're not necessary. by the way - you can add what you need to your fork.

## installing:
you can install only packages that you need, but also you can install a whole project (~80 packages):
```sh
poetry install --with dev,uvloop,sentry,redis,keyboards,database,scheduler,sulguk-parsemode
```

### optional packages:
* dev - development dependencies, such as yapf, pycodestyle, pytest, etc.
* uvloop - dependency for use_uvloop flag
* sentry - dependency for use_sentry flag
* redis - dependency for use_redis_fsm flag
* keyboards - dependency for use_modern_callback flag
* database - dependency for use_database flag
* scheduler - dependency for use_apscheduler flag
* sulguk-parsemode - dependency for use_sulguk flag. [sulguk](https://github.com/Tishka17/sulguk) is a html to telegram entities converter
* windows - dependencies for windows platform
