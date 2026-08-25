import base64
import logging
from collections import OrderedDict
from inspect import cleandoc

import aiohttp
import discord
import regex
from bs4 import BeautifulSoup
from discord.ext import commands

from tools import AITools


class AskCog(commands.Cog):
    def __init__(
        self,
        bot,
        askbot_name,
        system_instructions,
        valid_server_ids=None,
        model=None,
    ):
        """
        :param bot: Discord bot object
        :param askbot_name: Name of the askbot instance
        :param system_instructions: System instructions for the askbot
        :param valid_server_ids: Optional server ID(s) for which the askbot will be limited to
        :param model: Optional model name for the askbot
        """
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.askbot_name = askbot_name.lower()
        self.system_instructions = cleandoc(system_instructions)
        self.valid_server_ids = valid_server_ids
        if isinstance(self.valid_server_ids, int):
            self.valid_server_ids = [self.valid_server_ids]
        self.tools = AITools(self.bot)
        self.model = model or self.tools.model
        self.message_cache = OrderedDict()
        self.cache_size = 1000

    async def _get_images(self, message):
        image_urls = await self._extract_image_urls(message)
        images_b64 = set()
        if image_urls:
            for url in image_urls:
                images_b64.add(await self._url_to_base64(url))
        return images_b64

    async def _handle_response(self, response, target):
        try:
            if response:
                reply = await target.reply(content=response[:2000])
                self.logger.debug(f"RESPONSE: {response[:2000]}")
                if response == "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE":
                    await reply.add_reaction("<:reddit_downvote:1266139651660447744>")
        except discord.HTTPException:
            self.logger.exception(f"Failed to send response to {target}")
        except Exception:
            self.logger.exception(f"Unexpected error handling response for {target}")

    async def _run_ask(self, ctx, text: str):
        if not ctx.guild:
            return

        if self.valid_server_ids and (ctx.guild.id not in self.valid_server_ids):
            self.logger.debug(f"IGNORING {self.askbot_name.upper()} REQUEST")
            return

        self.logger.debug(f"RESPONDING TO USER: {ctx.author.name}")

        images_b64 = await self._get_images(ctx.message)

        response = await self.tools.ollama_response(
            message=ctx.message,
            system_instructions=self.system_instructions,
            messages=[
                {
                    "role": "user",
                    "content": text,
                    "images": images_b64 or "",
                    "image": images_b64 or "",  # Support both for compatibility
                }
            ],
            model=self.model,
        )

        await self._handle_response(response, ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return

        if self.valid_server_ids and (message.guild.id not in self.valid_server_ids):
            return

        if message.author.bot:
            return

        if not message.reference or not message.reference.resolved:
            return

        bot_reply = await message.channel.fetch_message(message.reference.message_id)
        if not bot_reply.author.bot:
            return

        self.logger.debug(f"RESPONDING TO: {message.author.name}")

        messages = await self._populate_messages(message)

        prefixes = (
            self.bot.command_prefix
            if isinstance(self.bot.command_prefix, (list, tuple))
            else [self.bot.command_prefix]
        )

        if not any(
            f"{prefix}ask{self.askbot_name}" in messages[0]["content"].lower()
            for prefix in prefixes
        ):
            return

        response = await self.tools.ollama_response(
            message=message,
            system_instructions=self.system_instructions,
            messages=messages,
            model=self.model,
        )

        await self._handle_response(response, message)

    async def _populate_messages(self, payload):
        """
        Creates a message history from a single message,
        looking through all of it's replies
        :param payload: Message to start search from
        :return: Message history
        """
        messages = []
        current = await payload.channel.fetch_message(payload.reference.message_id)

        while current:
            image_urls = await self._extract_image_urls(current)
            images_b64 = set()
            if image_urls:
                for url in image_urls:
                    images_b64.add(await self._url_to_base64(url))

            messages.append(
                {
                    "role": "assistant" if current.author.bot else "user",
                    "content": regex.sub(
                        r"<@!?(\d+)>",
                        lambda m: (
                            (current.guild.get_member(int(m.group(1)))).name
                            if current.guild.get_member(int(m.group(1)))
                            else m.group(0)
                        ),
                        current.content,
                    ),
                    "images": images_b64 if images_b64 else "",
                }
            )

            if current.reference:
                current = await self._get_message(
                    current.channel, current.reference.message_id
                )

            else:
                break

        messages.reverse()

        image_urls = await self._extract_image_urls(payload)
        images_b64 = set()
        if image_urls:
            for url in image_urls:
                images_b64.add(await self._url_to_base64(url))
        messages.append(
            {
                "role": "user",
                "content": payload.content,
                "images": images_b64 if images_b64 else "",
            }
        )

        return list(messages)

    async def _get_message(self, channel: discord.TextChannel, message_id: int):
        """
        Helper function to find a message object, looks for a cached message
        first, falling back to the discord API if not found.
        :param channel: Channel to look in
        :param message_id: Message ID to look for
        :return: Message object
        """
        if message_id in self.message_cache:
            return self.message_cache[message_id]

        try:
            message = await channel.fetch_message(message_id)
            await self._cache_message(message_id, message)
            return message

        except (discord.NotFound, discord.Forbidden) as e:
            self.logger.error(f"FAILED TO GET MESSAGE: {e}")

    async def _cache_message(self, message_id, message):
        """
        Cache a message object
        :param message_id: message ID to cache
        :param message: message object to cache
        :return:
        """
        self.message_cache[message_id] = message
        if len(self.message_cache) > self.cache_size:
            self.message_cache.popitem(last=False)

    async def _url_to_base64(self, url: str) -> str:
        """
        Converts an image URL to a base64 encoded string.
        :param url: Image URL
        :return: Base64 encoded string
        """
        try:
            async with aiohttp.ClientSession() as session:
                tries = 0

                while url and tries < 5:
                    async with session.get(url, timeout=10) as response:
                        content_type = response.headers.get("Content-Type", "")
                        if "image" in content_type:
                            data = await response.read()
                            return base64.b64encode(data).decode("utf-8")

                        elif "text/html" in content_type:
                            self.logger.debug(f"HTML found: {url}")
                            html = await response.content.read()
                            soup = BeautifulSoup(html, "html.parser")

                            og_image = soup.find("meta", property="og:image")
                            if og_image and og_image.get("content"):
                                url = og_image["content"]
                                tries += 1
                                continue

                        else:
                            self.logger.debug(f"NO IMAGE IN URL: {url}")
                            return None

        except aiohttp.ClientError as e:
            self.logger.error(f"FAILED TO FETCH URL {url}: {e}")
            return None

    async def _extract_image_urls(self, message: discord.Message):
        """
        Extracts image URLs from a message and stores them in a set.
        :param message: Message object to extract image URLs from
        :return: Image URLs
        """
        image_urls = set()

        for attachment in message.attachments:
            if attachment.content_type == "image":
                image_urls.add(attachment.url)

        for embed in message.embeds:
            if embed.thumbnail.url:
                image_urls.add(embed.thumbnail.url)
            if embed.image.url:
                image_urls.add(embed.image.url)

        urls = regex.findall(
            r"https?://[^\s]+", message.content, flags=regex.IGNORECASE
        )
        for url in urls:
            if url.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                image_urls.add(url)

            else:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=10) as response:
                            content_type = response.headers.get("Content-Type", "")
                            if "text/html" in content_type:
                                html = await response.text()
                                soup = BeautifulSoup(html, "html.parser")

                                # og:image
                                og_image = soup.find("meta", property="og:image")
                                if og_image and og_image.get("content"):
                                    image_urls.add(og_image["content"])

                                elif (img := soup.find("img")) and img.get("src"):
                                    image_urls.add(img["src"])

                except aiohttp.ClientError:
                    self.logger.exception(f"Failed to fetch HTML page {url}")

        if not image_urls:
            self.logger.debug("NO IMAGE URLS FOUND")
            return None

        return image_urls
