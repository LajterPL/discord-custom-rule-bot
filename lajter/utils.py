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

async def member_from_mention(guild: discord.Guild, mention: str) -> discord.Member:
    return await guild.fetch_member(int(mention[2:-1]))