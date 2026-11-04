import asyncio
import logging
import random

import discord
from discord.ext import commands

from tools import AITools
from utils import REDDIT_RED


gamble_lock = asyncio.Lock()

help_words = [
    "help",
    "helpline",
    "addiction",
    "support",
    "assistance",
    "advice",
    "tips",
    "problem",
    "recovery",
    "struggling",
    "stop",
    "lost",
    "losses",
    "lose",
    "urge",
    "temptation",
    "compulsive",
    "control",
]

# Limit to 25 values so drops embed doesn't break
gambling_table = [
    ("<:quarter_downvote:1266139626276388875>", 275),  # ~27%
    ("<:quarter_upvote:1266139599814529034>", 250),  # ~25%
    ("<:reddit_downvote:1266139651660447744>", 125),  # ~12.5%
    ("<:reddit_upvote:1266139689136689173>", 100),  # ~10%
    ("<:middlevote:1152474066331123823>", 50),  # ~5%
    ("<:absolutelynothing:1379228455580729435>", 35),  # ~3.5%
    ("<:fellforitagainaward:1361028185709346976>", 35),
    ("<:reddit_wholesome:833669115762835456>", 30),  # ~3%
    ("<:reddit_silver:833677163739480079>", 25),  # ~2.5%
    ("<:amazon_sad:1407662768370352158>", 25),
    ("<:reddit_gold:833675932883484753>", 10),  # ~1%
    ("<:Hullnarna:1406697829883314280>", 10),
    ("<:fruity:1399459414716715078>", 10),
    ("<:cornhole:1419397971090473030>", 10),
    ("<:african_ceiling_bird:1472907249860087880>", 10),
    ("<:kirk_pregnant:1472904615300300801>", 5),  # ~0.5%
    ("<:sadmark:1398048884332298260>", 5),
    ("<:reddit_platinum:833678610279563304>", 1),  # ~0.1%
    ("<:kayspag:1398048349579378849>", 1),
    ("<:budgiesmugglers:1399456204215947315>", 1),
    ("<:colin_nobinson:1412205389285691403>", 1),
    ("<:horseinsuit2:1363514876265365514>", 1),
    ("<:imjakingit:1361028727206711488>", 1),
    ("<:Monster:1412064129581060266>", 1),
    ("<:duke:1414946579302842388>", 0.1),  # ~0.01%
]


class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tools = AITools(self.bot)

    @commands.command(aliases=["gamble"])
    async def gambling(self, ctx, *, text: str = None):
        """
        Gamble for Karma and Awards
        Can only be used in `#gambling`
        `r/gambling drops` Displays the gambling drops and their respective drop rate percentage
        """
        if ctx.channel.name != "gambling":
            return

        if text:
            if "drops" in text:
                total_weight = sum(weight for _, weight in gambling_table)
                chances = [
                    (item, (weight / total_weight) * 100)
                    for item, weight in gambling_table
                ]

                embed = discord.Embed(title="Gambling Drops", color=REDDIT_RED)

                for item, chance in chances:
                    embed.add_field(name=item, value=f"{chance:.6f}%", inline=True)

                try:
                    await ctx.reply(embed=embed)
                except discord.HTTPException:
                    self.logger.exception(
                        f"Failed to send gambling drops embed in {ctx.channel.name}"
                    )
                return

            if any(key in text.lower() for key in help_words):
                ai_instructions = {
                    "role": "system",
                    "content": "You are trying to convince a fellow redditor to keep gambling, they don't know that they are close to their big win, which is why you need to convince them!",
                }

                try:
                    clean_response = await self.tools.ollama_response(
                        message=ctx.message,
                        system_instructions=ai_instructions,
                        messages=[
                            {
                                "role": "user",
                                "content": "Convince your fellow redditor to keep gambling, so they can get their biggest jackpot yet!!!",
                            }
                        ],
                        model="llama3",
                    )

                    await ctx.reply(f"{clean_response[:2000]}")
                except discord.HTTPException:
                    self.logger.exception(
                        f"Failed to send gambling encouragement to {ctx.author.name}"
                    )
                except Exception:
                    self.logger.exception("Unexpected error in gambling help response")
                return

        case_length = random.randint(10, 20)
        karma_case = self._get_gambling_rewards(case_length)

        # Open Karma Case
        try:
            message = await ctx.reply("Opening your Karma Case...")
        except discord.HTTPException:
            self.logger.exception(
                f"Failed to start gambling case for {ctx.author.name}"
            )
            return

        self.logger.info(f"OPENING KARMA CASE: REWARD = {karma_case[case_length - 3]}")
        await asyncio.sleep(2)

        async with gamble_lock:
            try:
                for i in range(case_length - 4):
                    frame = karma_case[i : i + 5]
                    display = f"{frame[0]}  |  {frame[1]}  |  **>> {frame[2]} <<**  |  {frame[3]}  |  {frame[4]}"
                    await message.edit(content=display)
                    await asyncio.sleep(0.25)
            except discord.HTTPException:
                self.logger.exception(
                    f"Failed to edit gambling case message for {ctx.author.name}"
                )

            try:
                await ctx.message.add_reaction(karma_case[case_length - 3])
            except discord.HTTPException:
                self.logger.exception(
                    f"ERROR ADDING REACTION {karma_case[case_length - 3]} in {ctx.guild.name}"
                )
            except Exception:
                self.logger.exception("Unexpected error adding gambling reaction")

    def _get_gambling_rewards(self, length=10):
        rewards, weights = zip(*gambling_table)
        return random.choices(rewards, weights=weights, k=length)


async def setup(bot):
    await bot.add_cog(Gambling(bot))
