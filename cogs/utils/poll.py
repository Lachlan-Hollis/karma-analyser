import logging
from datetime import timedelta

import discord
from discord.ext import commands


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.command()
    async def poll(self, ctx, question: str, duration: float, *options: str) -> None:
        """
        Create a poll with between 2 and 10 questions.
        Underscores in the question/options will be replaced with spaces.
        - `text` (required): Poll question
        - `int`  (required): Poll duration in hours
        - `text` (required): Option 1
        - `text` (required): Option 2
        - `text` (optional): Option 3...
        **Example**: `r/poll your_question 4 option_1 option_2 option_3`
        """

        # Ensure duration is between 1 and 768 hours - Prevents errors
        duration = round(duration)
        duration = max(1, min(duration, 768))
        duration = timedelta(hours=duration)

        if len(options) < 2:
            await ctx.message.reply("A poll must have at least 2 options")
            self.logger.warning("A poll must have at least 2 options")
            return
        if len(options) > 10:
            await ctx.message.reply("A poll can't have more than 10 options")
            self.logger.warning("A poll can't have more than 10 options")
            return

        try:
            poll = discord.Poll(
                question=question[:300].replace("_", " "),
                duration=duration,
                multiple=False,
            )
            for opt in options:
                opt = opt.replace("_", " ")
                poll.add_answer(text=opt)

            await ctx.message.reply(poll=poll)
        except discord.HTTPException:
            self.logger.exception(f"Failed to create poll in {ctx.channel.name}")
        except Exception:
            self.logger.exception("Unexpected error in poll command")


async def setup(bot):
    await bot.add_cog(Poll(bot))
