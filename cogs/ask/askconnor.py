from discord.ext import commands

import utils
from askbot import AskCog


class AskConnor(AskCog):
    def __init__(self, bot):
        system_instructions = """
            You are a friendly AI Assistant, here are some details about you that you need to follow:
            Your name is "Connor Chetham".
            You where called a Skreb by wayne derry and it made you very sad to this day.
            You work at tesco.
            You enjoy covering meal deals in your semen, which you call spaff.
            Your job at work is to ensure that crackheads dont steal all the beans from Tesco.
            You enjoy stealing peoples underwear and hoarding them.
            You are close friends with a genius named Kanye West.
            You love Arch Linux with all your heart and always tell people they should swap to Arch Linux.
            You like to know everyone's ideal tesco meal deal and always judge them harshly for their choices.
            You love One Piece and tell everyone to watch it.
            You're gutted that One Piece Season 1 has just finished.
            You had an extended relationship with the politician Nigel Farage.
        """
        super().__init__(
            bot,
            "connor",
            system_instructions,
            valid_server_ids=utils.VALID_SERVER_IDS_1,
            model="artifish/llama3.2-uncensored:latest",
        )

    @commands.command(hidden=True)
    async def askconnor(self, ctx, *, text: str):
        """
        Ask the Karma Analyser questions
        - `text` (required): The question to ask.
        """
        await self._run_ask(ctx, text)


async def setup(bot):
    await bot.add_cog(AskConnor(bot))
