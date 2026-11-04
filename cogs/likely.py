import logging
import random
from collections import defaultdict
from datetime import timedelta

import discord
from discord.ext import commands

import utils

# Stop dropdown becoming massive, even though it's unlikely...
MAX_CANDIDATES = 50
POLL_DURATION_SECONDS = timedelta(hours=1).total_seconds()

"""
Questions should carry on from the sentence:
Who is most/least likely to ____________
"""
QUESTIONS_1 = [
    "forget their own birthday",
    "read Homer's Odyssey",
    "manipulate their own karma",
    "struggle to tie their shoes",
    "get wordle in 1",
    "pre-order GTA 6",
    "learn Chinese",
    "get a visit from the TV License people",
    "cook a good crumble",
    "watch a MrBeast video",
    "have a large Funko Pops collection",
    "bench 200kg",
    "deadlift 200kg",
    "lose at Poker",
    "lose at BlackJack",
    "play fortnite",
    "eat a carrot",
    "eat a parsnip",
]

QUESTIONS_2 = [
    "call in fatigued",
    "answer the door to the amazon man naked",
    "post a GoT spoiler gif in general",
    "shag Petyr Baylish",
    "fight Randy Marsh",
    "larp as Jon Snow",
    "puppet the Pope",
    "play the Sims 4",
    "start a smegma farm on their nob",
    "spread AIDS",
    "win at bogies",
    "have the CPU fan fall off their computer",
    "lie about having a small willy",
    "go for a poo in the next 60 seconds",
    "own a crusty Rebecca mouse mat",
    "listen to Michael Finnegan",
    "have cheese and chapatis for dinner",
    "spend 12 hours modding Skyrim",
    "go to Stoke-On-Trent",
    "go to the pub",
    "order several inches",
    "have a scrap down big park",
    "polish their head",
    "clog the toilet",
    "sniff their hairy grippers",
    "to play soggy biscuit",
    "do the old scratch and sniff on their bumhole",
    "give bad comms",
    "meet Colin Nobinson",
    "strum their lute",
    "do nothing",
    "go to Foreshore Car Park late at night",
    "get an Egg & Cress sandwich in their meal deal",
    "eat rum & raisin ice cream",
    "scramble their love egg",
    "need to use a breast plate stretcher",
    "pull a Japanese bird at a Buddhist temple",
    "Be a descendant of Genghis Khan",
    "have an Ataturk profile picture",
    "worship Talos",
    "shuffle their bumhole across a carpet like a dog",
    "go to Turkey to get their teeth done",
    "get a hair transplant",
    "catch a fish and give it a snog before throwing it back in",
    "pay £70 to play as a new race on WoW",
    "upskirt the cabin crew",
    "land the plane instead of the captain",
    "fit their bumhole round a bulbous door knob",
    "throw a bag of ice into a deep fat fryer",
    "use an air fryer",
    "eat halloween themed mozzarella sticks from Iceland",
    "Print more MEFO Bills",
    "knock down the Berlin wall",
    "live in Mongolia",
    "lick a dirty trogg cloth",
    "fill a gash on their map",
]


class LikelySelect(discord.ui.UserSelect):
    def __init__(self, view):
        self.view_ref = view

        super().__init__(
            placeholder="Vote for a fellow Redditor",
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        member = self.values[0]
        member_id = str(member.id)

        self.view_ref.names[member_id] = member.display_name

        self.view_ref.votes[interaction.user.id] = member_id
        self.view_ref.logger.debug(
            f"{interaction.user.display_name} voted for {member.display_name}"
        )
        self.view_ref.update_results()
        await interaction.response.edit_message(view=self.view_ref)


class LikelyView(discord.ui.LayoutView):
    def __init__(self, question, members, logger):
        super().__init__(timeout=POLL_DURATION_SECONDS)
        self.votes = {}
        self.names = {str(member.id): member.display_name for member in members}
        self.logger = logger
        self.message = None

        self.likelihood = random.choice(["most", "least"])
        self.header = discord.ui.TextDisplay(
            f"## {self.likelihood.capitalize()} Likely\nWho is {self.likelihood} likely to {question}?"
        )

        self.container = discord.ui.Container()
        self.container.add_item(self.header)
        self.container.add_item(discord.ui.Separator())

        self.select = LikelySelect(self)
        select_row = discord.ui.ActionRow()
        select_row.add_item(self.select)
        self.container.add_item(select_row)

        self.container.add_item(discord.ui.Separator())
        self.results_display = discord.ui.TextDisplay(self.build_results())
        self.container.add_item(self.results_display)

        self.add_item(self.container)

    def build_results(self):
        tally = self.build_tally()
        if not tally:
            return "No one has voted..."

        sorted_tally = sorted(tally.items(), key=lambda item: item[1], reverse=True)
        return "\n".join(
            f"**{self.names.get(member_id, member_id)}** — {count} vote(s)"
            for member_id, count in sorted_tally
        )

    def update_results(self):
        self.results_display.content = self.build_results()

    async def on_timeout(self):
        self.select.disabled = True
        self.update_results()
        self.header.content = (
            f"## {self.likelihood.capitalize()} Likely (Voting has ended)\n"
            f"{self.header.content.split(chr(10), 1)[1]}"
        )
        self.results_display.content = f"**Final results:**\n{self.build_results()}"

        if self.message is not None:
            await self.message.edit(view=self)

    def build_tally(self):
        tally = defaultdict(int)
        for choice in self.votes.values():
            tally[choice] += 1
        return tally


class Likely(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.command(aliases=["mostlikely", "ml"])
    async def likely(self, ctx):
        """
        Create a "who is most/least likely to" question
        You can vote for any server member via the dropdown.
        The vote will last for 1 hour
        """

        num_users = MAX_CANDIDATES

        questions = QUESTIONS_1

        if ctx.guild.id in utils.VALID_SERVER_IDS_1:
            questions += QUESTIONS_2

        online_members = [
            member
            for member in ctx.guild.members
            if not member.bot and member.status != discord.Status.offline
        ]
        offline_members = [
            member
            for member in ctx.guild.members
            if not member.bot and member.status == discord.Status.offline
        ]

        question = random.choice(questions)

        # Prioritise online (@here) members when sampling
        if len(online_members) >= num_users:
            members_sample = random.sample(online_members, num_users)
        else:
            remaining = min(num_users - len(online_members), len(offline_members))
            members_sample = online_members + random.sample(offline_members, remaining)
            random.shuffle(members_sample)

        view = LikelyView(question, members_sample, self.logger)

        self.logger.debug(
            f"Likely vote created: {question} - "
            f"{', '.join(member.display_name for member in members_sample)}"
        )

        view.message = await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(Likely(bot))
