import logging
import random
from datetime import timedelta

import discord
from discord.ext import commands

import utils


QUESTIONS_1 = [
    "Go to the job centre",
    "Speak in a chinese accent for the rest of your life",
    "Avoid paying tax",
    "Be vegan",
    "Cut your left hand off",
    "Cut your right hand off",
    "Cut your left foot off",
    "Cut your right foot off",
    "Lower your IQ points by 40",
    "Fight in a trial of seven",
    "Eat Indian street food",
    "Cook Crumble",
    "Cheese",
    "Petril",
    "Go to a pub and order inches",
    "Have all the games",
    "Have no games",
    "Dance, walk and rearrange furniture",
    "Let the cat out of the bag",
    "Play Tarkov",
    "Play Minecraft",
    "Play Fortnite",
    "Play League of Legends",
    "Play Valorant",
    "Play Overwatch",
    "Be chained to a radiator for 24 hours",
    "Be in a Mr Beast Video",
    "Watch The Office",
    "Watch The Matrix",
    "Work for Amazon",
    "Work for Tesco",
    "Work for McDonalds",
    "Call it a 'cob'",
    "Call it a 'bap'",
    "Call it a 'breadcake'",
    "Call it a 'bread roll'",
    "Accept fate",
    "Dye your hair ginger",
    "Scroll Facebook reels",
    "Scroll TikTok",
    "Scroll Instagram reels",
    "Live in Avernus",
    "Watch Stranger Things",
    "Fight a Demogorgon",
    "Collect Funko pops",
    "Get punched in the mouth",
    "Shit in your hands and clap",
    "Play a game of chess",
    "Play Dark Souls",
    "Chew on a cockroach",
    "Catch Hantavirus",
    "Watch Disney+",
]

QUESTIONS_2 = [
    "Rip your foreskin off with rusty pliers",
    "Goon to Toni Ahier",
    "Polish Ben's big bald head",
    "Shave your belly with a rusty razor",
    "Spend a night in a 'Ullian Premier Inn",
    "Get in a plane when Jaden is the pilot",
    "Move to Mongoria",
    "Wear a slug outfit near chandy",
    "Order a Cheng's garden then get a dominos instead",
    "Shove a pencil up your arse",
    "Clog Taz's toilet",
    "Finger your bum",
    "Bum your finger",
    "Be Indian",
    "Be Chinese",
    "Be Japanese",
    "Be Korean",
    "Brown butter",
    "Deliver an amazon parcel",
    "Show your nob to Beth Varly",
    "Cut your nob off",
    "Vote Reform UK",
    "Move to Skeggy",
    "Sniff Wayney's hairy toes",
    "Take a hit from Carol's electric bong",
    "Recreate 9/11",
    "Let the Tazmin out of the inside",
    "Be paralysed from the waist down",
    "Be paralysed from the neck down",
    "Get abducted by P Diddy",
    "Down an entire bottle of vodka",
    "Milk Ben's teets into a bucket",
    "Watch Barnyard",
    "Watch Hotel Rwanda",
    "Watch The Lord of the Rings",
    "Watch all of One Piece without sleeping",
    "Pass a GCSE maths test",
    "Lick Jaden's armpits",
    "Move to 'Ull",
    "Goon to the fish in the deep aquarium in 'Ull",
    "Drink Taz's bong water",
    "Eat out Bonnie Blue",
    "Drive a VW Passat",
    "Own an unreliable Datsun",
    "Finger James May",
    "Play Wordspud",
    "Play WynnCraft",
    "Play Soggy Biscuit",
    "'Lose' Soggy Biscuit",
    "'Win' Soggy Biscuit",
    "Never play Jackbox again",
    "Live in the white & blue house on Little St James",
    "Work in a sports bar",
    "Live in a universe without food trucks",
    "Sprinkle nob cheese over your pasta",
    "Put repeaters in your special Tarkov slot",
    "List your item for sale on the flea market",
    "Cover for your missus when she clogs the toilet",
    "Give your nob a bath",
    "Give your nob a shower",
    "Give your nob a bath and shower",
    "Spend an hour playing wordle",
    "Get on your knees and show it to ben sexual style",
    "Eat the nut crust off your goon sock",
    "Be an extra on 'Ullraisers",
    "Clean your butt crust off",
    "Adapt an Israeli TV Show, and set it in Hull",
    "Go to the pub with Wayne Derry",
    "Teach Wayne how to read",
    "Give bad comms",
    "Get an ace and teamkill",
    "Miss GTA and that",
    "Put a piece of rolled up cloth in your vest",
    "Buy more friendslop",
    "Have a plague doctor sniff your bumhole",
    "Replace 4 road wheels on your tiger tank",
    "Tear people's tarmac up with your tank",
    "Get creampied by Colin Nobinson",
    "Get a blowjob from a goat",
    "Give a blowjob to a goat",
    "Walk right through a door",
    "Eat ginger chips",
    "Call Gemma a fat slag",
    "Play Dead by Daylight",
    "Goon to Hotel Chocolat",
    "Wash your clothes but only with fabric softener",
    "Polish your forehead",
    "Spank ben",
    "Pussy Wagon, Chicken Nugget",
    "Work for EasyJet",
    "Work for RyanAir",
    "Strum your lute",
    "Hit the Sea Lion",
    "Eat a cold and soggy MrBeast Burger",
    "Clap Ben's cheeks",
    "Suckle on Jeff Bezos' bollocks",
    "Rub Elon Musk's big toe",
    "Play Assassins creed on a keyboard",
    "Play Futa Runner",
    "Stroke your keyboard",
    "Subscribe to Razer Software",
    "Own nothing and be happy",
    "Eat a schnitzel stick",
    "Wait for GTA 6",
    "Be French",
    "Nothing",
    "Fill a river with starving and invasive leeches",
    "Waffle stomp in your shower",
    "Get a dessert ubered after salt and pepper club",
    "Have a scrap down big park",
    "Get in a bare knuckle at the White Horse",
    "Have a private jet",
    "Have a smelly sket",
    "Have a smelly bum",
    "Run the Sneakers O'Tool",
    "Be fired from your job",
    "Be a smelly ginger",
    "Kick a ginger",
    "Be ginger on the 5th of November",
    "Steal undies",
    "Do a 9/11",
    "Drax them sklounst",
    "Sit next to terries up in here",
    "Sit in the combat seat",
    "Have a cheesy nob",
    "Take Sneakers O'Toole's sneakers off",
    "Go dogging at foreshore car park",
    "Scrape the cheese off your nob",
    "Sea of thieves nuts fit in your mouth",
]


class WouldYouRather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @commands.command(aliases=["wyr"])
    async def wouldyourather(self, ctx):
        """
        Create a would you rather question
        The poll will last for 1 hour
        """

        questions = QUESTIONS_1

        if ctx.guild.id in utils.VALID_SERVER_IDS_1:
            questions += QUESTIONS_2

        poll = discord.Poll(
            question="Would you rather:",
            duration=timedelta(hours=1),
            multiple=False,
        )

        option_a = random.choice(questions)
        option_b = random.choice(questions)
        while option_a == option_b:
            option_b = random.choice(questions)

        poll.add_answer(text=option_a)
        poll.add_answer(text=option_b)

        self.logger.debug(f"Would you rather poll created: {option_a} or {option_b}")

        await ctx.reply(poll=poll)


async def setup(bot):
    await bot.add_cog(WouldYouRather(bot))


if __name__ == "__main__":
    questions = QUESTIONS_1 + QUESTIONS_2
    print(f"number of questions: {len(questions)}")
    for question in questions:
        if len(question) > 55:
            print(f"question too long: {question}")
