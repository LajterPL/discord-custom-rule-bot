import logging

from lajter.action import Action, ActionType
from discord.ext import commands
from discord import Member

logger = logging.getLogger('ADMIN')
logger.setLevel(logging.DEBUG)

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))

class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def ban(self, ctx: commands.Context, member: Member):
        action = Action(ActionType.BAN)
        await action.execute(self.bot, member)
