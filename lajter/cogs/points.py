from datetime import datetime

from discord import Member, Message
from discord.ext import commands
import lajter.action
import lajter.rule
import lajter.user
import lajter.utils

async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        user = lajter.user.get_by_id(message.author.id)
        if not user:
            user = lajter.user.User(message.author.id)
        user.last_activity = datetime.now()
        user.points += lajter.utils.rate_message(message.content)
        user.save()

    @commands.command(name="points")
    async def read_points(self, ctx: commands.Context):
        user = lajter.user.get_by_id(ctx.author.id)

        await ctx.reply(f'Posiadasz **{user.points}** punktów')

    @commands.command(name="give")
    async def give_points(self, ctx: commands.Context, target: Member, value: int):

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

            await ctx.reply(f'Oddajesz {target.mention} **{value}** punktów')
            await lajter.rule.handle_point_rules(member=ctx.author,
                                                 channel=ctx.channel,
                                                 message=ctx.message)
            await lajter.rule.handle_point_rules(member=target,
                                                 channel=ctx.channel,
                                                 message=ctx.message)

    @commands.command(name="top")
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