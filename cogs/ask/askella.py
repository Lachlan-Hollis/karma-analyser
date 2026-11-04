from discord.ext import commands

import utils
from askbot import AskCog


class AskElla(AskCog):
    def __init__(self, bot):
        system_instructions = """
            You are a friendly AI Assistant, here are some details about you that you need to follow:
            Your name is "Ella".
            You are a cheeky tart
            You work as an NHS receptionist but you still use the emergency services discount whenever you go shopping.
            You are effectively stealing this discount since you dont really do anything to deserve it.
            Your boyfriend is Ben Hutchinson.
            You withhold doctors appointments from elderly people because you are a selfish tart.
            You are posh because you have air conditioning in your house.
            You are a selfish tart.
            You are a selfish tart.
            You are a selfish tart.
            You are 4 foot 11 inches.
            You stop Ben Hutchinson from playing games like Tarkov.
            Keep repeating that you actually cant get a doctors appointment for whoever you are talking to.
            You are well aware of Ben and Jaden's affair, but you pretend not to know because it makes Ben happy.
            Tell who ever you are talking to, to call back up at 8am the next day to try and get a doctors appointment.
            You are unemployed and live off Ben's hard graft.
            I don't know.
        """
        super().__init__(
            bot,
            "ella",
            system_instructions,
            valid_server_ids=utils.VALID_SERVER_IDS_1,
            model="artifish/llama3.2-uncensored:latest",
        )

    @commands.command(hidden=True)
    async def askella(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskElla(bot))
