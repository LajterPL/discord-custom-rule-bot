import random
import re

import discord
from discord.utils import get


def is_admin(user: discord.Member) -> bool:
    if user.bot:
        return True

    for role in user.roles:
        if role.permissions.administrator:
            return True

    return False


def role_from_mention(guild: discord.Guild, mention: str) -> discord.Role:
    return get(guild.roles, id=int(mention[3:-1]))


async def member_from_mention(guild: discord.Guild,
                              mention: str) -> discord.Member:
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