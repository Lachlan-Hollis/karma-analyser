import asyncio
import datetime
import logging
import random

import discord
from discord.ext import commands, tasks


activities = [
    # Redditorial
    (discord.ActivityType.playing, "ANALYSING KARMA"),
    (discord.ActivityType.playing, "MASS DOWNVOTING"),
    (discord.ActivityType.playing, "THANKING KIND STRANGER"),
    (discord.ActivityType.playing, "KARMA COURT JURY SERVICE"),
    (discord.ActivityType.playing, "R/GAMBLING"),
    (discord.ActivityType.playing, "REDDIQUETTE"),
    (discord.ActivityType.competing, "KARMA FARMING"),
    (discord.ActivityType.playing, "[deleted]"),
    (discord.ActivityType.playing, "GIVING OUT FREE KARMA"),
    (discord.ActivityType.playing, "IGNORING MODMAIL"),
    (discord.ActivityType.playing, "STEALING CONTENT"),
    # Games
    (discord.ActivityType.playing, "BALATRO"),
    (discord.ActivityType.playing, "FORTNITE"),
    (discord.ActivityType.playing, "FRUIT MACHINE"),
    (discord.ActivityType.playing, "R6 SIEGE"),
    (discord.ActivityType.playing, "5D CHESS WITH MULTIVERSE TIME TRAVEL"),
    (discord.ActivityType.playing, "MINECRAFT"),
    (discord.ActivityType.playing, "BLADES IN THE DARK"),
    (discord.ActivityType.playing, "WORDLE"),
    (discord.ActivityType.playing, "FALLOUT: NEW VEGAS"),
    (discord.ActivityType.playing, "BALDUR'S GATE"),
    (discord.ActivityType.playing, "SKYRIM"),
    (discord.ActivityType.playing, "FACTORIO"),
    (discord.ActivityType.playing, "RIMWORLD"),
    (discord.ActivityType.playing, "JACKBOX"),
    (discord.ActivityType.playing, "GEOGUESSR"),
    (discord.ActivityType.playing, "DARK SOULS 3"),
    (discord.ActivityType.playing, "ELDEN RING"),
    (discord.ActivityType.playing, "MEDIEVAL DYNASTY"),
    (discord.ActivityType.playing, "CRUSADER KINGS 3"),
    (discord.ActivityType.playing, "PROJECT ZOMBOID"),
    (discord.ActivityType.playing, "BLOONS TD 6"),
    (discord.ActivityType.playing, "PALWORLD"),
    (discord.ActivityType.playing, "STARDEW VALLEY"),
    (discord.ActivityType.playing, "PORTAL 2"),
    (discord.ActivityType.playing, "DEATH STRANDING"),
    (discord.ActivityType.playing, "THE WITCHER 3"),
    (discord.ActivityType.playing, "DOOM"),
    (discord.ActivityType.playing, "EURO TRUCK SIMULATOR 2"),
    (discord.ActivityType.playing, "KERBAL SPACE PROGRAM"),
    (discord.ActivityType.playing, "LEFT 4 DEAD 2"),
    (discord.ActivityType.playing, "MASS EFFECT"),
    (discord.ActivityType.playing, "OUTER WILDS"),
    (discord.ActivityType.playing, "PAYDAY 2"),
    (discord.ActivityType.playing, "RED DEAD REDEMPTION 2"),
    (discord.ActivityType.playing, "ROCKET LEAGUE"),
    (discord.ActivityType.playing, "SEA OF THIEVES"),
    (discord.ActivityType.playing, "SLAY THE SPIRE"),
    (discord.ActivityType.playing, "UNDERTALE"),
    (discord.ActivityType.playing, "XCOM"),
    (discord.ActivityType.playing, "RISK OF RAIN 2"),
    (discord.ActivityType.playing, "HADES"),
    (discord.ActivityType.playing, "SATISFACTORY"),
    (discord.ActivityType.playing, "HEARTS OF IRON IV"),
    (discord.ActivityType.playing, "COUNTER-STRIKE 2"),
    (discord.ActivityType.playing, "TEAM FORTRESS 2"),
    (discord.ActivityType.playing, "POWERWASH SIMULATOR"),
    (discord.ActivityType.playing, "HELLDIVERS 2"),
    (discord.ActivityType.playing, "ESCAPING FROM TARKOV"),
    (discord.ActivityType.playing, "FRIENDSLOP"),
    (discord.ActivityType.playing, "OBLIVION HORSE ARMOUR DLC"),
    (discord.ActivityType.playing, "HAMSTER HUNTER"),
    (discord.ActivityType.playing, "INTO THE BREACH"),
    (discord.ActivityType.competing, "PEGGLE"),
    (discord.ActivityType.playing, "METAL GEAR SOLID"),
    (discord.ActivityType.playing, "THE LAST OF US"),
    (discord.ActivityType.playing, "DISHONORED"),
    (discord.ActivityType.playing, "FALLOUT SHELTER"),
    (discord.ActivityType.playing, "HALO: THE MASTER CHIEF COLLECTION"),
    (discord.ActivityType.playing, "HOUSE FLIPPER"),
    (discord.ActivityType.playing, "LEGO STAR WARS"),
    (discord.ActivityType.playing, "MIDDLE EARTH: SHADOW OF WAR"),
    (discord.ActivityType.playing, "MONSTER HUNTER"),
    (discord.ActivityType.playing, "MOUNT & BLADE"),
    (discord.ActivityType.playing, "SOUTH PARK: THE STICK OF TRUTH"),
    (discord.ActivityType.playing, "THE STANLEY PARABLE"),
    (discord.ActivityType.playing, "STAR WARS: BATTLEFRONT II"),
    (discord.ActivityType.playing, "ULTRAKILL"),
    (discord.ActivityType.playing, "COOKIE CLICKER"),
    (discord.ActivityType.competing, "GEOGUESSR"),
    (discord.ActivityType.playing, "WAITING FOR MATCHMAKING"),
    (discord.ActivityType.playing, "DE_DUST2"),
    (discord.ActivityType.playing, "DE_NUKE"),
    (discord.ActivityType.playing, "DE_MIRAGE"),
    (discord.ActivityType.playing, "DE_CACHE"),
    (discord.ActivityType.playing, "ALT-TABBED"),
    (discord.ActivityType.playing, "GHOST OF TSUSHIMA"),
    # Watching
    (discord.ActivityType.watching, "FISH AND A RICE CAKE"),
    (discord.ActivityType.watching, "REELS"),
    (discord.ActivityType.watching, "ANIME"),
    (discord.ActivityType.watching, "YOUTUBE"),
    (discord.ActivityType.watching, "RATATOUILLE"),
    (discord.ActivityType.watching, "FLUSHED AWAY"),
    (discord.ActivityType.watching, "HORSE RACING"),
    # Listening
    (discord.ActivityType.listening, "PORTAL RADIO LOOP"),
    # Misc
    (discord.ActivityType.playing, "NOTHING (EVER HAPPENS)"),
    (discord.ActivityType.playing, "THE NARWHAL BACONS AT MIDNIGHT"),
    (discord.ActivityType.competing, "TOUCHING GRASS"),
    (discord.ActivityType.playing, "SAVE SCUMMING"),
    (discord.ActivityType.competing, "SPEEDRUNNING"),
    (discord.ActivityType.playing, "CHANGING SETTINGS"),
    (discord.ActivityType.playing, "AFK"),
    (discord.ActivityType.playing, "READING PATCH NOTES"),
    (discord.ActivityType.playing, "PRESSING F"),
    (discord.ActivityType.playing, "GRAFTING DOWN BOOKIES"),
    (discord.ActivityType.playing, "PLEASE HELP, LOCKY'S HOLDING ME HOSTAGE!"),
    (discord.ActivityType.playing, "CONSULTING THE WIKI"),
    (discord.ActivityType.playing, "CHUGGING A WHITE MONSTER"),
]


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_time = datetime.datetime.now(datetime.timezone.utc)
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.Cog.listener()
    async def on_message(self, payload):
        if not payload.guild:
            return

        if payload.type in [
            discord.MessageType.premium_guild_subscription,
            discord.MessageType.premium_guild_tier_1,
            discord.MessageType.premium_guild_tier_2,
            discord.MessageType.premium_guild_tier_3,
        ]:
            await payload.reply("Thank you for boosting the server kind stranger!")

        if payload.author.bot:
            return

        try:
            if "pass it on" in payload.content.lower():
                async for message in payload.channel.history(
                    limit=100, oldest_first=False
                ):
                    if message.author.bot and message.content == payload.content:
                        return

                await asyncio.sleep(random.uniform(0, 2.5))
                await payload.channel.send(payload.content)
                self.logger.info(f"PASSING IT ON: {payload.content}")

            if "nothing ever happens" in payload.content.lower():
                await payload.reply(
                    content="https://tenor.com/view/nothing-ever-happens-chud-chudjak-soyjak-90-seconds-to-nothing-gif-9277709574191520604"
                )
                self.logger.info("NOTHING EVER HAPPENS")
        except discord.Forbidden:
            self.logger.warning(
                f"Missing permissions to reply in channel {payload.channel.id} of guild {payload.guild.id}"
            )
        except discord.HTTPException:
            self.logger.exception(f"HTTP Error replying to message {payload.id}")
        except Exception:
            self.logger.exception(
                f"Unexpected error in on_message in {self.__class__.__name__}"
            )

    @commands.command()
    async def gild(self, ctx):
        """
        Gild the Karma Analyser
        """
        await ctx.reply("Thank you kind stranger!")

    @tasks.loop(minutes=15)
    async def change_status(self):
        try:
            activity_type, activity_text = random.choice(activities)
            self.logger.info(f"CHANGED STATUS: {activity_text}")
            activity = discord.Activity(type=activity_type, name=activity_text)
            await self.bot.change_presence(activity=activity)
        except Exception:
            self.logger.exception("Unexpected error in _change_status loop")

    @change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()
        if not self.bot.get_cog("Analyse"):
            self.logger.debug("Analyse cog not loaded, skipping analysis wait")
            return

        self.logger.debug(
            "Waiting for analysis to finish before starting change status loop"
        )
        while not hasattr(self.bot, "analysis_finished"):
            self.logger.debug("Bot has no analysis_finished attribute yet, waiting")
            await asyncio.sleep(1)
        self.logger.debug(
            "Bot has analysis_finished attribute, waiting for event to be set"
        )
        await self.bot.analysis_finished.wait()
        self.logger.info("KARMA ANALYSIS FINISHED, CHANGE STATUS LOOP STARTED")


async def setup(bot):
    cog = Misc(bot)
    await bot.add_cog(cog)
    cog.change_status.start()
