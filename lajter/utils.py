import os
import random
import re

import discord
from discord import Guild, TextChannel, Role, Member, User
from discord.ext.commands import check, Context
from discord.utils import get
from discord.ext import commands

def immune(member: Member) -> bool:
    if not member or type(member) is User:
        return True

    if member.bot or is_banned(member):
        return True

    if member.guild.owner is member:
        return True

    for role in member.roles:
        if role.permissions.administrator:
            return True

    return False


def role_from_mention(guild: Guild, mention: str) -> Role:
    return get(guild.roles, id=int(mention[3:-1]))


async def member_from_mention(guild: Guild,mention: str) -> Member:
    return await guild.fetch_member(int(mention[2:-1]))


def rate_message(message: str) -> int:

    if message.startswith(("!", "http")):
        return 0

    points = random.randrange(20)

    words = message.split(" ")

    # Average Polish word is 6 around letters, if someone is spamming
    # one big string of text, they will start losing points
    if len(message) / len(words) > 15:
        points -= 100

    # If someone is spamming very short words,
    # they are gonna get punished as well
    if len(words) > 3:
        if len(message) / len(words) < 4:
            points -= 100

    # Checking for puncation
    for match in re.finditer("([.,?!] [a-zA-Z])+", message):
        points += 10

    return min(points, 100)

async def get_default_guild(bot: commands.Bot) -> Guild | None:
    guild_id = os.getenv("DEFAULT_GUILD")
    if guild_id:
        return bot.get_guild(int(guild_id))
    return None

async def get_default_channel(bot: commands.Bot) -> TextChannel | None:
    channel_id = os.getenv("DEFAULT_CHANNEL")
    if channel_id:
        return await bot.fetch_channel(int(channel_id))
    return None

async def get_ban_role(bot: commands.Bot) -> Role | None:
    role_id = os.getenv("BAN_ROLE")
    if role_id:
        guild: Guild = await get_default_guild(bot)
        return guild.get_role(int(role_id))
    return None

def is_banned(member: Member) -> bool:
    role_id = os.getenv("BAN_ROLE")
    for role in member.roles:
        if role.id == int(role_id):
            return True
    return False

def not_banned():
    async def predicate(ctx: Context):
        return not is_banned(ctx.author)
    return check(predicate)