import asyncio
import os
import logging

from discord import Intents, Message, Member, Reaction
from discord.ext import commands
from dotenv import load_dotenv

logger = logging.getLogger('EVENT')
logger.setLevel(logging.DEBUG)

load_dotenv()
bot_key = os.getenv("BOT_KEY")

intents = Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')

async def load_commands(bot):
    await bot.load_extension("lajter.cogs.rules")
    await bot.load_extension("lajter.cogs.actions")
    await bot.load_extension("lajter.cogs.points")

asyncio.run(load_commands(bot))

bot.run(bot_key, root_logger=True)

