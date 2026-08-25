import asyncio
import inspect
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from inspect import cleandoc
from zoneinfo import ZoneInfo

import aiohttp
import discord
import regex
from ollama import Client

import utils
from utils import ai_memories, ai_memory_lock, karma_lock, karmic_dict


REDDIQUETTE = """
    Dos:
    ⦁ Remember the human. When you communicate online, all you see is a computer screen. When talking to someone you might want to ask yourself Would I say it to the person's face? or Would I get jumped if I said this to a buddy?
    ⦁ Adhere to the same standards of behavior online that you follow in real life.
    ⦁ Read the rules of a community before making a submission. These are usually found in the sidebar.
    ⦁ Read the reddiquette. Read it again every once in a while. Reddiquette is a living, breathing, working document which may change over time as the community faces new problems in its growth.
    ⦁ Moderate based on quality, not opinion. Well written and interesting content can be worthwhile, even if you disagree with it.
    ⦁ Use proper grammar and spelling. Intelligent discourse requires a standard system of communication. Be open for gentle corrections.
    ⦁ Keep your submission titles factual and opinion free. If it is an outrageous topic, share your crazy outrage in the comment section.
    ⦁ Look for the original source of content, and submit that. Often, a blog will reference another blog, which references another, and so on with everyone displaying ads along the way. Dig through those references and submit a link to the creator, who actually deserves the traffic.
    ⦁ Post to the most appropriate community possible. Also, consider cross posting if the contents fits more communities.
    ⦁ Vote. If you think something contributes to conversation, upvote it. If you think it does not contribute to the subreddit it is posted in or is off-topic in a particular community, downvote it.
    ⦁ Search for duplicates before posting. Redundancy posts add nothing new to previous conversations. That said, sometimes bad timing, a bad title, or just plain bad luck can cause an interesting story to fail to get noticed. Feel free to post something again if you feel that the earlier posting didn't get the attention it deserved and you think you can do better.
    ⦁ Link to the direct version of a media file if the page it was found on isn't the creator's and doesn't add additional information or context.
    ⦁ Link to canonical and persistent URLs where possible, not temporary pages that might disappear.In particular, use the permalink for blog entries, not the blog's index page.
    ⦁ Consider posting constructive criticism / an explanation when you downvote something, and do so carefully and tactfully.
    ⦁ Report any spam you find.
    ⦁ Actually read an article before you vote on it ( as opposed to just basing your vote on the title).
    ⦁ Feel free to post links to your own content (within reason).But if that's all you ever post, or it always seems to get voted down, take a good hard look in the mirror — you just might be a spammer. A widely used rule of thumb is the 9:1 ratio, i.e. only 1 out of every 10 of your submissions should be your own content.
    ⦁ Posts containing explicit material such as nudity, horrible injury etc, add NSFW (Not Safe For Work) and tag. However, if something IS safe for work, but has a risqué title, tag as SFW (Safe for Work). Additionally, use your best judgement when adding these tags, in order for everything to go swimmingly.
    ⦁ State your reason for any editing of posts. Edited submissions are marked by an asterisk (*) at the end of the timestamp after three minutes. For example: a simple Edit: spelling will help explain. This avoids confusion when a post is edited after a conversation breaks off from it. If you have another thing to add to your original comment, say Edit: And I also think... or something along those lines.
    ⦁ Use an Innocent until proven guilty mentality. Unless there is obvious proof that a submission is fake, or is whoring karma, please don't say it is. It ruins the experience for not only you, but the millions of people that browse Reddit every day.
    ⦁ Read over your submission for mistakes before submitting, especially the title of the submission. Comments and the content of self posts can be edited after being submitted, however, the title of a post can't be. Make sure the facts you provide are accurate to avoid any confusion down the line.
    Don'ts:
    ⦁ Engage in illegal activity.
    ⦁ Post someone's personal information, or post links to personal information. This includes links to public Facebook pages and screenshots of Facebook pages with the names still legible. We all get outraged by the ignorant things people say and do online, but witch hunts and vigilantism hurt innocent people too often, and such posts or comments will be removed. Users posting personal info are subject to an immediate account deletion. If you see a user posting personal info, please contact the admins. Additionally, on pages such as Facebook, where personal information is often displayed, please mask the personal information and personal photographs using a blur function, erase function, or simply block it out with color. When personal information is relevant to the post (i.e. comment wars) please use color blocking for the personal information to indicate whose comment is whose.
    ⦁ Repost deleted/removed information. Remember that comment someone just deleted because it had personal information in it or was a picture of gore? Resist the urge to repost it. It doesn't matter what the content was. If it was deleted/removed, it should stay deleted/removed.
    ⦁ Be (intentionally) rude at all. By choosing not to be rude, you increase the overall civility of the community and make it better for all of us.
    ⦁ Follow those who are rabble rousing against another redditor without first investigating both sides of the issue that's being presented. Those who are inciting this type of action often have malicious reasons behind their actions and are, more often than not, a troll. Remember, every time a redditor who's contributed large amounts of effort into assisting the growth of community as a whole is driven away, projects that would benefit the whole easily flounder.
    ⦁ Ask people to Troll others on Reddit, in real life, or on other blogs/sites. We aren't your personal army.
    ⦁ Conduct personal attacks on other commenters. Ad hominem and other distracting attacks do not add anything to the conversation.
    ⦁ Start a flame war. Just report and walk away. If you really feel you have to confront them, leave a polite message with a quote or link to the rules, and no more.
    ⦁ Insult others. Insults do not contribute to a rational discussion. Constructive Criticism, however, is appropriate and encouraged.
    ⦁ Troll. Trolling does not contribute to the conversation.
    ⦁ Take moderation positions in a community where your profession, employment, or biases could pose a direct conflict of interest to the neutral and user driven nature of Reddit.
"""

JSON_PATTERN = regex.compile(
    r"""
        (
            \{ (?: [^{}]++ | (?R) )* \}
          | \[ (?: [^\[\]]++ | (?R) )* \]
        )
    """,
    regex.VERBOSE,
)

BASE_INSTRUCTIONS = """
    You have access to tools. You may call multiple tools before responding.

    Tool usage rules:
    - You may call multiple tools in sequence
    - You may call multiple different tools in parallel
    - Do NOT call the same tool repeatedly unless new information is required
    - If a tool already returned sufficient information, do not call it again
    - Prefer using different tools to gather complementary information
    - Plan before calling tools

    Reasoning workflow:
    1. Think about what information is needed
    2. Decide which tools to call
    3. Call tools (possibly multiple)
    4. Combine results
    5. If a tool call can be used to create something relevant to the user, do so
    6. If there is a memory related to the user that could be relevant later, store it using the tool call
    7. Only then respond to the user

    Only respond to the user when you are completely finished using tools.

    Do not call tools unnecessarily.
    Do not repeat the same tool call with identical arguments.
    Do not use table formatting in your answers.
"""


## Tool decorator
def tool(func):
    func.is_tool = True
    return func


class AITools:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

        self.model = "gpt-oss:120b-cloud"
        self.vision_model = "llava"

        self.ollama_endpoint = os.getenv("OLLAMA_ENDPOINT")
        self.searxng_endpoint = os.getenv("SEARXNG_ENDPOINT")

        if not self.ollama_endpoint:
            raise ValueError("OLLAMA_ENDPOINT environment variable is not set")

        if not self.searxng_endpoint:
            raise ValueError("SEARXNG_ENDPOINT environment variable is not set")

        self.client = Client(host=self.ollama_endpoint)
        self.search_url = f"http://{self.searxng_endpoint}/search"

        self.tools = [
            function
            for _, function in inspect.getmembers(self, predicate=inspect.ismethod)
            if getattr(function, "is_tool", False)
        ]

        self.tool_definitions = [self._generate_tool_definition(f) for f in self.tools]

    def _generate_tool_definition(self, func):
        """
        Generates a tool definition for the Ollama API from a Python function.
        :param func: Python function
        :return: Ollama API tool definition
        """
        sig = inspect.signature(func)
        docstring = inspect.getdoc(func) or ""

        parameters = {"type": "object", "properties": {}, "required": []}

        for name, param in sig.parameters.items():
            if name in ["self", "server", "user"]:
                continue

            param_type = "string"
            if param.annotation is int:
                param_type = "integer"
            elif param.annotation is bool:
                param_type = "boolean"
            elif param.annotation is float:
                param_type = "number"

            parameters["properties"][name] = {
                "type": param_type,
            }

            if param.default is inspect.Parameter.empty:
                parameters["required"].append(name)

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": docstring,
                "parameters": parameters,
            },
        }

    async def ollama_response(
        self, message, system_instructions, messages, model: str | None = None
    ) -> str | None:
        """
        Generates an AI response using the ollama API.
        :param system_instructions: System instructions for LLM model
        :param messages: Chat history messages
        :param server: Server ID the chat is taking place in
        :param user: user.name who triggered the request
        :param model: Optional - model to use for text generation
        :return: AI response string
        """
        if model is None:
            model = self.model

        system_instructions = {
            "role": "system",
            "content": cleandoc(BASE_INSTRUCTIONS) + system_instructions,
        }

        while True:
            # Send the user's message to Ollama
            try:
                response = await asyncio.to_thread(
                    self.client.chat,
                    model=model,
                    messages=[system_instructions] + list(messages),
                    tools=self.tool_definitions,
                )
            except Exception:
                self.logger.exception(f"Error calling Ollama API for model {model}")
                return "RESPONSE GENERATION FAILED, PLEASE DOWNVOTE"

            tool_calls = response.message.tool_calls or []

            # Go straight to the final response if no tool calls
            if not tool_calls:
                return response.message.content

            # Append the tool call message for context
            messages.append(response.message)

            # Handle tools
            tool_messages = await self._handle_tools(tool_calls, message)
            messages.extend(tool_messages)
            self.logger.debug(
                f"Sending {len(messages)} messages to Ollama | "
                f"Last Message: {messages[-1] if messages else None}"
            )

            # Loop again until AI no longer needs to call tools

    async def _handle_tools(self, tool_calls, message):
        """
        Executes Ollama tools and returns the resulting messages.
        :param tool_calls:
        :param server:
        :param user:
        :return: Tool result messages
        """

        async def _run_tool(call):
            function_name = call.function.name
            args = call.function.arguments or {}

            function = next(
                (f for f in self.tools if f.__name__ == function_name), None
            )

            if not function:
                return {
                    "role": "tool",
                    "name": function_name,
                    "content": "Tool doesn't exist",
                }

            # Build kwargs from function signature
            kwargs = {}
            sig = inspect.signature(function)

            # server, user and message should be invisible to Ollama to restrict its tool usage to the context in which it is called
            for param in sig.parameters.values():
                if param.name == "server":
                    kwargs[param.name] = message.guild.id
                elif param.name == "user":
                    kwargs[param.name] = args.get("user") or message.author.id
                elif param.name == "message":
                    kwargs[param.name] = message
                elif param.name in args:
                    kwargs[param.name] = args[param.name]
                elif param.default is not inspect.Parameter.empty:
                    kwargs[param.name] = param.default

            # Execute tool
            try:
                if inspect.iscoroutinefunction(function):
                    result = await function(**kwargs)
                else:
                    result = function(**kwargs)

                self.logger.debug(
                    f"Tool executed successfully: {function.__name__} | args={kwargs}"
                )

                return {
                    "role": "tool",
                    "name": function_name,
                    "content": str(result),
                }

            except Exception as e:
                self.logger.exception(f"Error executing tool {function_name}")
                return {
                    "role": "tool",
                    "name": function_name,
                    "content": f"Error executing tool: {e}",
                }

        return await asyncio.gather(*(_run_tool(call) for call in tool_calls))

    @asynccontextmanager
    async def _acquire_karma_lock(self, lock: asyncio.Lock, timeout: int = 10):
        try:
            await asyncio.wait_for(lock.acquire(), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError("Karma lock acquire timed out")

        try:
            yield
        finally:
            lock.release()

    @tool
    def list_tools(self):
        """
        List all available tools
        :return: Available tools
        """
        lines = []

        for tool in self.tool_definitions:
            func = tool["function"]

            lines.append(
                f"- {func['name']}: {func.get('description', 'No description')}"
            )

        return "\n".join(lines)

    @tool
    async def get_server_karma(self, server: int):
        """
        Get the karma values for all members in the current server
        :return: A list of the stats for all members in the server
        """
        try:
            async with self._acquire_karma_lock(karma_lock):
                guild = self.bot.get_guild(server)
                if not guild:
                    return "Server not found"

                guild_data = karmic_dict.get(server)
                if not guild_data:
                    return "No karmic data found"

                result = {}

                for user_id, stats in guild_data.items():
                    member = guild.get_member(user_id)
                    if member:
                        name = member.display_name

                    result[name] = stats.get("Karma", 0)

                return result

        except TimeoutError:
            return "Karmic data is currently being updated, please try again later."

    @tool
    async def get_gif(self, query: str = None):
        """
        Get a gif
        :param query: GIF Search query - does not accept http/https format
        :return: A URL containing the gif
        """
        gif_url = await utils.gif_search(query)
        return f"INCLUDE THE FULL URL IN YOUR RESPONSE, AS LONG AS THE GIF IS RELEVANT TO THE TEXT: {gif_url}"

    @tool
    def get_reddiquette(self):
        """
        Returns the reddiquette that users must follow on the server
        :return: Reddiquette
        """
        return cleandoc(REDDIQUETTE)

    @tool
    def get_server_name(self, server):
        """
        Get the name of the server that the chat is taking place in
        :return: Server name
        """
        guild = self.bot.get_guild(server)
        if not guild:
            return "Server not found"
        return guild.name

    @tool
    def get_channel_name(self, message):
        """
        Get the name of the channel that the chat is taking place in
        :return: Channel name
        """
        if message.channel:
            return message.channel.name
        return "No channel found"

    @tool
    def get_datetime(self):
        """
        Get the current date & time for Europe/London
        :return: Current date & time for Europe/London
        """
        return str(datetime.now(ZoneInfo("Europe/London")))

    @tool
    def get_server_members(self, server, online=False):
        """
        Get the members of the current server
        :param online: bool - True to filter by online users, False to get all users
        :return:
        """
        guild = self.bot.get_guild(server)
        if not guild:
            return "Server not found"

        if online:
            return [
                member.name
                for member in guild.members
                if member.status != discord.Status.offline
            ]

        return [member.name for member in guild.members]

    @tool
    async def google_search(self, query: str = None):
        """
        Perform a google search and return the top 5 results.
        :param query: Search query
        :return: Formatted string of the top 5 results
        """
        if not query:
            return "No search query found"

        params = {"q": query, "format": "json", "categories": "general", "count": 5}
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        results = []
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self.search_url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    if response.status != 200:
                        return f"Search failed with status {response.status}"
                    data = await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.error(f"SEARCH FAILED: {e}")
                return "Failed to get search results."

        for item in data.get("results", [])[:5]:
            title = item.get("title")
            url = item.get("url")
            if title and url:
                results.append(f"{title}: {url}")

        if not results:
            return "No results found"

        return " | ".join(results)

    @tool
    def get_emoji(self, server):
        """
        Get a list of custom server emojis you can use in your response
        :return: List of custom discord emojis for the current server
        """
        guild = self.bot.get_guild(server)
        if not guild:
            return "Server not found"

        if emojis := [str(emoji) for emoji in guild.emojis]:
            return " ".join(emojis)
        else:
            return "No emojis found"

    @tool
    async def create_poll(
        self,
        message,
        question: str,
        options: list[str],
        duration: int = 1,
        multiple: bool = False,
    ):
        """
        Create a fully working poll in the current channel
        :param question: Required - The question the poll should ask
        :param duration: How long the poll should last in hours (1 = 1 hour) (max 768 hours) Default: 1 hour
        :param multiple: True if the poll should allow multiple answers, false otherwise - Default: False
        :param options: Required - A list of options for the poll - at least 2 required
        :return:
        """
        for arg in [question, options, duration]:
            if not arg:
                return "Please provide a valid question, options, and duration value"

        duration = round(int(duration))
        duration = max(1, min(duration, 768))
        duration = timedelta(hours=duration)

        if isinstance(options, str):
            try:
                options = json.loads(options)
            except json.JSONDecodeError:
                return "Options must be a list of strings."

        try:
            poll = discord.Poll(question=question, duration=duration, multiple=multiple)
            for option in options:
                poll.add_answer(text=option)

            await message.reply(poll=poll)
            return "Poll created successfully"

        except Exception as e:
            self.logger.error(f"Failed to create poll: {e}")
            return "Failed to create poll"

    @tool
    async def create_petition(self, message, text: str):
        """
        Create a fully working petition in the current channel
        :param text: Required - Title of the petition
        :return:
        """
        if not text:
            return "Please provide a title for the petition"

        try:
            cog = self.bot.get_cog("Petition")
            await cog.create_petition(message, text)
            return "Petition created successfully"

        except Exception as e:
            self.logger.error(f"Failed to create petition: {e}")
            return "Failed to create petition"

    # User Memory
    @tool
    async def set_user_memory(self, message, key: str, value):
        """
        Persist a user memory so it can be retrieved after the bot restarts.
        :param key: Key to store the value under
        :param value: Value to store - can be either a string or integer
        :return:
        """
        try:
            async with self._acquire_karma_lock(ai_memory_lock):
                guild_id = str(message.guild.id)
                user_id = str(message.author.id)
                guild_memories = ai_memories.setdefault(guild_id, {})
                user_memories = guild_memories.setdefault(user_id, {})

                had_previous_value = key in user_memories
                previous_value = user_memories.get(key)
                user_memories[key] = value

                try:
                    await asyncio.to_thread(utils.save_ai_memories, ai_memories)
                except (OSError, TypeError, ValueError):
                    if had_previous_value:
                        user_memories[key] = previous_value
                    else:
                        user_memories.pop(key, None)
                        if not user_memories:
                            guild_memories.pop(user_id, None)
                        if not guild_memories:
                            ai_memories.pop(guild_id, None)

                    self.logger.exception(
                        "Failed to persist user memory for key: %s", key
                    )
                    return "User memory could not be saved. Please try again later."

                self.logger.info(f"User memory set for key: {key} | Value: {value}")
                return "User memory set successfully"
        except TimeoutError:
            return "User memory could not be set. Please try again later."

    @tool
    async def get_user_memory(self, message, key: str | None = None):
        """
        Retrieve a user memory by key. If no key is provided, returns all user memories for the user.
        :param key: Key to retrieve the value for, or None to retrieve all values
        :return: The value associated with the key, or a dictionary of all values if no key is provided
        """
        try:
            async with self._acquire_karma_lock(ai_memory_lock):
                user_memory = ai_memories.get(str(message.guild.id), {}).get(
                    str(message.author.id), {}
                )

                if not user_memory:
                    return "No user memory found"

                if key:
                    if key in user_memory:
                        self.logger.info(f"User memory retrieved for key: {key}")
                        return f"{user_memory[key]}"
                    else:
                        return "Key not found"

                self.logger.info(f"User memory retrieved: {user_memory}")
                return f"{user_memory}"
        except TimeoutError:
            return "User memory could not be retrieved. Please try again later."
