import logging
import random
from datetime import datetime

import discord
from discord import Member, Message, User
from discord.ext import commands
import lajter.action
import lajter.rule
import lajter.user
import lajter.utils
from lajter.cogs.rules import handle_rules

logger = logging.getLogger('POINTS')
logger.setLevel(logging.DEBUG)

async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guild: discord.Guild = await lajter.utils.get_default_guild(self.bot)

        for member in guild.members:
            if not member.bot and lajter.user.get_by_id(member.id) is None:
                db_user = lajter.user.User(member.id)
                db_user.save()

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        if not member.bot and lajter.user.get_by_id(member.id) is None:
            db_user = lajter.user.User(member.id)
            db_user.save()

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or type(message.author) is User:
            return

        user = lajter.user.get_by_id(message.author.id)
        if not user:
            user = lajter.user.User(message.author.id)
        user.last_activity = datetime.now()
        user.points += lajter.utils.rate_message(message.content)
        user.save()

    @commands.command(name="points", brief="Wyświetl posiadane punkty")
    async def read_points(self, ctx: commands.Context):
        user = lajter.user.get_by_id(ctx.author.id)

        await ctx.reply(f'Posiadasz **{user.points}** punktów')

    @commands.command(name="give", brief="Przekaż komuś punkty")
    @commands.guild_only()
    async def give_points(
            self,
            ctx: commands.Context,
            target: Member = commands.parameter(description="Komu punkty zostaną przekazane"),
            value: int = commands.parameter(description="Kwota jaka zostanie przekazana")):

        if value < 0:
            await ctx.reply(f'Niewłaściwa liczba punktów')
            return

        giver = lajter.user.get_by_id(ctx.author.id)
        receiver = lajter.user.get_by_id(target.id)

        if value > giver.points:
            await ctx.reply(f'Masz za mało punktów na koncie')
            return

        if giver and receiver:
            giver.points -= value
            giver.save()

            receiver.points += value
            receiver.save()

            logger.info(f'{ctx.author} przekazał {target} {value} punktów')
            await ctx.reply(f'Oddajesz {target.mention} **{value}** punktów')
            await handle_rules(
                [
                    lajter.rule.RuleType.POINTS_LESS_THAN,
                    lajter.rule.RuleType.POINTS_GREATER_THAN
                ],
                bot=self.bot,
                member=ctx.author,
                db_user=giver,
                channel=ctx.channel,
                message=ctx.message
            )
            await handle_rules(
                [
                    lajter.rule.RuleType.POINTS_LESS_THAN,
                    lajter.rule.RuleType.POINTS_GREATER_THAN
                ],
                bot=self.bot,
                member=target,
                db_user=receiver,
                channel=ctx.channel,
                message=ctx.message
            )

    @commands.command(name="top", aliases=["leaderboard"], brief="Wyświetl tabelę punktów")
    @commands.guild_only()
    async def point_leaderboard(self, ctx: commands.Context):

        users = lajter.user.User.db.all()
        users.sort(key=lambda user: user['points'], reverse=True)

        s = ""
        for user in users:
            try:
                member: Member = await ctx.guild.fetch_member(user["id"])
                s += f'**{member.name}:** {user["points"]} punktów\n'
            except Exception:
                pass
        await ctx.reply(s)

    @commands.command(name="coinflip", brief="Rzuć monetą, żeby wygrać punkty")
    @commands.guild_only()
    async def coin_flip(self, ctx: commands.Context, amount):
        user = lajter.user.get_by_id(ctx.author.id)

        try:
            amount = int(amount)
        except ValueError:
            amount = user.points

        if amount <= 0 or amount > user.points:
            await ctx.reply("Niewłaściwa liczba punktów")
            return

        if bool(random.getrandbits(1)):
            user.points += amount
            await ctx.reply(f'Wygrywasz **{amount}** punktów')
        else:
            user.points -= amount
            await ctx.reply(f'Tracisz **{amount}** punktów')

        user.save()

        await handle_rules(
            [
                lajter.rule.RuleType.POINTS_LESS_THAN,
                lajter.rule.RuleType.POINTS_GREATER_THAN
            ],
            bot=self.bot,
            member=ctx.author,
            db_user=user,
            channel=ctx.channel,
            message=ctx.message
        )
