import logging
import random
from typing import Tuple

from discord.ext import commands

logger = logging.getLogger('FUN')
logger.setLevel(logging.DEBUG)

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))

class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(
            self,
            ctx: commands.Context,
            error: commands.CommandError
    ):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(f'Musisz podać argument: {error.param.name}')
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f'Musisz chwilę poczekać')
        elif isinstance(error, commands.BadArgument):
            await ctx.reply(f'Niepoprawny argument')

    @commands.command(name="gay", brief="Sprawdź swój poziom nikczemnictwa")
    @commands.cooldown(3, 10)
    async def gay_meter(self, ctx: commands.Context):
        percent = random.randrange(100)
        await ctx.reply(f'Jesteś gejowx w {percent}%')

    @commands.command(name="dick", brief="Sprawdź swój poziom siurka")
    @commands.cooldown(3, 10)
    async def dick_size(self, ctx: commands.Context):
        size = random.randrange(1, 8)
        dick = "3"
        for i in range(size):
            dick += "="
        dick += "D"
        await ctx.reply(f'Zdjęcie twojego siurka: {dick}')
