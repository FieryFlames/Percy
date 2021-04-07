import argparse

import discord
import toml
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.utils import manage_commands
from sqlalchemy.ext.asyncio import create_async_engine

from cogs.utils.models import Base

# define some stuff
parser = argparse.ArgumentParser(description="Percy Launcher")

# add arguments
parser.add_argument(
    "--config", help="Use a differect config other than the default one.", default="percy.ini")
parser.add_argument(
    "--debug", help="Drops all existing DB tables & disables nitro boosting requirement.", default=False)
# parse
args = parser.parse_args()
# read conf
with open(args.config) as conf_file:
    config = toml.load(conf_file)

token = config["Discord"]["Token"]
url = config["SQLAlchemy"]["URL"]
color = config["Bot"]["Color"]
version = config["Bot"]["Version"]
cogs = config["Bot"]["Cogs"]
if args.debug is not None: 
    debug = args.debug 
else:
    debug = False
# actual bot


class BBot(commands.Bot):
    def __init__(self, url, color, version, cogs, debug):
        # set intents
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents, command_prefix=commands.when_mentioned)

        # Remove help command
        self.remove_command('help')

        # Database load
        self.engine = create_async_engine(url)

        # color
        self.color = color

        # add slash commands
        SlashCommand(self, sync_commands=True)

        self.debug = debug
        
        for cog in cogs:
            self.load_extension(cog)

    async def on_connect(self):
        # Create the table if it doesn't exist
        async with self.engine.begin() as conn:
            if self.debug:
                await conn.run_sync(Base.metadata.drop_all)
                await manage_commands.remove_all_commands_in(734485213304062053)
            await conn.run_sync(Base.metadata.create_all)

        # set the activity
        activity = discord.Activity(
            type=discord.ActivityType.listening, name=f"boost events | v{version}")
        await self.change_presence(status=discord.Status.idle, activity=activity)

    async def on_ready(self):
        print("Ready!")


bot = BBot(url, color, version, cogs, debug)

bot.run(token)
