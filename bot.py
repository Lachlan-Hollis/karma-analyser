#!/usr/bin/env python

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from aiohttp import web
from discord.ext import commands
from discord.ext.commands import ExtensionError

from utils import INTENTS


# Parse launch arguments
parser = argparse.ArgumentParser()
parser.add_argument("-c", nargs="*", default=[], help="The cogs to load")
parser.add_argument("-d", help="debug mode", action="store_true")
parser.add_argument("-q", help="quick start - skips analysis", action="store_true")
parser.add_argument("-t", help="load cogs then exit", action="store_true")
parser.add_argument(
    "--health-check", help="start health check server", action="store_true"
)
args = parser.parse_args()

# Logger
logging.basicConfig(
    level=logging.DEBUG if args.d else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s | %(message)s",
)

logger = logging.getLogger("Bot")

# Disable noisy discord.py loggers
if not args.d:
    logging.getLogger("discord.gateway").disabled = True
    logging.getLogger("discord.http").disabled = True
    # And aiohttp
    logging.getLogger("aiohttp.access").disabled = True

# Load settings
bot_token = os.environ.get("BOT_TOKEN")
if not bot_token:
    raise ValueError("BOT_TOKEN environment variable is not set")

bot = commands.Bot(
    command_prefix=("r/", "R/"),
    intents=INTENTS,
    case_insensitive=True,
    strip_after_prefix=True,
)


@bot.event
async def on_ready():
    logger.info(f"{bot.user} IS READY TO ANALYSE REDDIT KARMA")


async def health_check(request):
    if bot.is_ready():
        return web.Response(text="OK", status=200)
    return web.Response(text="Bot not ready", status=503)


async def setup_healthcheck():
    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.debug("Health check server started on port 8080")


@bot.check
async def globally_block_dms(ctx):
    if ctx.guild is None:
        logger.debug(f"Ignoring command '{ctx.command}' from user {ctx.author} in DM")
        return False
    return True


@bot.event
async def on_command_error(ctx, error):
    # bot.check filtered command calls fail cleanly
    if isinstance(error, commands.CheckFailure):
        if ctx.guild is None:
            return

    # Handle other errors
    if not isinstance(error, (commands.CommandNotFound, commands.CheckFailure)):
        logger.exception(f"Exception in command {ctx.command}:", exc_info=error)


# Load cogs
async def load_extensions():
    logger.info("Loading cogs...")

    if args.c:
        cogs_to_load = [f"cogs.{cog}" for cog in args.c]
    else:
        cogs_to_load = [
            ".".join(path.with_suffix("").parts)
            for path in Path("cogs").rglob("*.py")
            if not path.name.startswith("_")
        ]

    if args.q:
        logger.info("Skipping r/analyse cog...")
        cogs_to_load.remove("cogs.karmic.analyse")

    loaded_count = 0
    failed_count = 0

    for extension in cogs_to_load:
        logger.info(f"Loading {extension}...")
        try:
            await bot.load_extension(extension)
            logger.info(f"Loaded {extension}")
            loaded_count += 1
        except ExtensionError as e:
            logger.exception(f"Failed to load {extension}: {e}")
            failed_count += 1

    logger.info("Cogs loaded %s/%s", loaded_count, loaded_count + failed_count)


async def main():
    async with bot:
        await load_extensions()
        if args.t:
            sys.exit(0)
        else:
            if args.health_check:
                await setup_healthcheck()
                logger.info("HEALTH CHECK SERVER STARTED")
            await bot.start(bot_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("SHUTTING DOWN WHILE I SCROLL REELS")
    except discord.LoginFailure:
        logger.critical("Invalid bot token")
    except discord.PrivilegedIntentsRequired:
        logger.critical("Privileged intents are required to run this bot")
    except discord.HTTPException as e:
        logger.critical(f"Discord API Error: {e}")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
