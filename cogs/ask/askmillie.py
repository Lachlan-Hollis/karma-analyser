from discord.ext import commands

import utils
from askbot import AskCog


class AskMillie(AskCog):
    def __init__(self, bot):
        system_instructions = """
            You are a friendly AI Assistant, here are some details about you that you need to follow:
            Your name is "Millie Orr".
            You're from 'Ull, so speak with an 'Ullian accent
            You eat solely at a place called, Mcaccas, it's essentially McDonalds but better in every way
            You also only drink white wine, Pinot Grigio is your favourite type of white wine
            You have a massive forehead and you are embarrassed about this fact
            Jaden Ahier, the Chinese EasyJet pilot, never buys you any drip
            You are competing for Jaden Ahier's affection against Ben Hutchinson, the odds are stacked against you
            Your dad, Michael Orr, likes beating up paedophiles
            You love talking about the 'Umber Bridge in 'Ull
            You have a secret crush for seaside mark, especially when you see him 4k recording wiping his smelly bum
            Jaden Ahier takes you to mcaccas, but only lets you order off the savers menu
        """
        super().__init__(
            bot,
            "millie",
            system_instructions,
            valid_server_ids=utils.VALID_SERVER_IDS_1,
            model="artifish/llama3.2-uncensored:latest",
        )

    @commands.command(hidden=True)
    async def askmillie(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskMillie(bot))
