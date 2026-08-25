import logging

from discord.ext import commands

import tools


class Riddle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

        self.tools = tools.AITools(self.bot)
        self.message = [
            {
                "role": "user",
                "content": "give me a riddle, containing only the riddle and no other filler "
                "text explaining that it is a riddle",
            }
        ]
        self.instructions = (
            "You are a helpful assistant that gives riddles. "
            "Your responses should be riddles only and no other filler text "
            "or referencing the fact that your message is a riddle. "
            "RIDDLE CONTENT ONLY"
        )

    @commands.command(aliases=["rddle", "ddl"])
    async def riddle(self, ctx):
        """
        Riddle me this
        """
        riddle = await self.tools.ollama_response(
            ctx.message, self.instructions, self.message, model="gpt-oss:120b-cloud"
        )
        print(riddle)
        await ctx.reply(content=riddle)


async def setup(bot):
    await bot.add_cog(Riddle(bot))
