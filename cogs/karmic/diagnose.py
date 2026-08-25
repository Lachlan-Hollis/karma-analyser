import logging

import discord
from discord.ext import commands

from tools import AITools, REDDIQUETTE
from utils import karmic_dict


class Diagnose(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tools = AITools(self.bot)

    @commands.command(aliases=["diagnosis"])
    async def diagnose(self, ctx, user: discord.Member = None):
        """
        Get a user's karmic diagnosis
        - `user` (optional): Mention the user(s) to diagnose.
        """
        if user is None:
            user = ctx.author

        self.logger.info(f"DIAGNOSING {user.name}")

        karma = karmic_dict[ctx.guild.id][user.id]["Karma"]

        try:
            reply = await ctx.reply("DIAGNOSING...")
        except discord.HTTPException:
            self.logger.exception(
                f"Failed to send initial diagnosis message to {ctx.author.name}"
            )
            return

        try:
            message_log = []
            prefixes = (
                self.bot.command_prefix
                if isinstance(self.bot.command_prefix, (list, tuple))
                else [self.bot.command_prefix]
            )
            async for msg in ctx.channel.history(limit=200):
                if (
                    msg.author == user
                    and not any(
                        msg.content.startswith(prefix) for prefix in prefixes
                    )  # Ignore bot commands
                    and "http" not in msg.content  # Ignore links
                ):
                    message_log.append(msg.content)

            ai_instructions = {
                "role": "system",
                "content": "You are a reddit moderation bot...\n" + REDDIQUETTE,
            }
            prompt = (
                f"The user has {karma} karma, you need to suggest how they can improve their karma \n"
                f"by analysing these messages: \n"
            ) + "\n".join(message_log)

            clean_response = await self.tools.ollama_response(
                message=ctx.message,
                system_instructions=ai_instructions,
                messages=[{"role": "user", "content": prompt}],
                model="artifish/llama3.2-uncensored",
            )

            await reply.edit(content=f"{user.mention}: {clean_response[:1950]}")
            self.logger.debug(f"RESPONSE: {clean_response[:1950]}")
        except discord.HTTPException:
            self.logger.exception(f"Failed to edit diagnosis message for {user.name}")
        except Exception:
            self.logger.exception(f"Unexpected error diagnosing user {user.name}")


async def setup(bot):
    await bot.add_cog(Diagnose(bot))
