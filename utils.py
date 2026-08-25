import asyncio
import json
import logging
import os
import random
from collections import defaultdict
from pathlib import Path

import aiohttp
import discord


logger = logging.getLogger("UTILS")

INTENTS = discord.Intents.none()
INTENTS.guilds = True
INTENTS.members = True
INTENTS.expressions = True
INTENTS.invites = True
INTENTS.voice_states = True
INTENTS.presences = True
INTENTS.guild_messages = True
INTENTS.guild_reactions = True
INTENTS.message_content = True
INTENTS.guild_polls = True

REDDIT_RED = 0xED001C
REDDIT_ORANGE = 0xFF8700
REDDIT_GREEN = 0x3BCB56
REDDIT_BLUE = 0x149EF0
REDDIT_GRAY = 0xA5A4A4

VALID_SERVER_IDS_1 = [683033503834963978, 1361336155169226792, 1184181874592063528]

karmic_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
karma_lock = asyncio.Lock()

AI_MEMORY_DIR = Path(os.getenv("AI_MEMORY_DIR") or "data")
AI_MEMORY_FILE = AI_MEMORY_DIR / "ai_memories.json"
ai_memory_lock = asyncio.Lock()


def load_ai_memories():
    try:
        with AI_MEMORY_FILE.open("r", encoding="utf-8") as file:
            memories = json.load(file)
    except FileNotFoundError:
        return {}
    except (OSError, json.JSONDecodeError):
        logger.exception("Failed to load AI memories from %s", AI_MEMORY_FILE)
        return {}

    if not isinstance(memories, dict):
        logger.error("Ignoring invalid AI memory data in %s", AI_MEMORY_FILE)
        return {}

    logger.info("Loaded AI memories from %s", AI_MEMORY_FILE)
    return memories


def save_ai_memories(memories):
    AI_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    temporary_file = AI_MEMORY_FILE.with_suffix(".json.tmp")

    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(memories, file, indent=2, sort_keys=True)
            file.flush()
            os.fsync(file.fileno())

        temporary_file.replace(AI_MEMORY_FILE)
    except Exception:
        temporary_file.unlink(missing_ok=True)
        raise


ai_memories = load_ai_memories()


async def gif_search(query: str):
    api_key = os.getenv("KLIPY_KEY")
    if not api_key:
        logger.warning("KLIPY_KEY environment variable is not set")
        return None

    url = f"https://api.klipy.com/api/v1/{api_key}/gifs/search"
    params = {
        "q": query or "reddit",
        "page": 1,
        "per_page": 8,
        "customer_id": 0,
        "locale": "GB",
        "content_filter": "off",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                resp.raise_for_status()
                data = await resp.json()
    except Exception:
        logger.exception(f"Failed to fetch GIF for query: {query}")
        return None

    gifs = data.get("data", {}).get("data", [])
    if not gifs:
        return None

    gif = random.choice(gifs)
    return gif.get("file", {}).get("md", {}).get("gif", {}).get("url")
