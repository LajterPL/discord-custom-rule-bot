import os
import logging

from discord import Intents, Message, Member, Reaction
from discord.ext import commands
from dotenv import load_dotenv

import lajter.utils as utils
from lajter.commands import register_commands
from lajter.rule import (
    handle_message_rules,
    handle_activity_rules,
    handle_reaction_rules,
    handle_user_name_rules
)

logger = logging.getLogger('EVENT')
logger.setLevel(logging.DEBUG)

load_dotenv()
bot_key = os.getenv("BOT_KEY")

intents = Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')

@bot.event
async def on_message(message: Message):
    if not utils.is_admin(message.author):
        await handle_message_rules(bot, message)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before: Message, after: Message):
    if not utils.is_admin(after.author):
        await handle_message_rules(bot, after)

@bot.event
async def on_presence_update(before: Member, after: Member):
    if not utils.is_admin(after):
        if len(before.activities) > 0:
            await handle_activity_rules(bot, before)
        if len(after.activities) > 0:
            await handle_activity_rules(bot, after)

@bot.event
async def on_reaction_add(reaction: Reaction, user: Member):
    if not utils.is_admin(user):
        await handle_reaction_rules(bot, user, reaction)
@bot.event
async def on_member_join(user: Member):
    if not utils.is_admin(user):
        await handle_user_name_rules(bot, user)

@bot.event
async def on_member_update(before: Member, after: Member):
    if not utils.is_admin(after):
        await handle_user_name_rules(bot, before)
        await handle_user_name_rules(bot, after)

register_commands(bot)

bot.run(bot_key, root_logger=True)