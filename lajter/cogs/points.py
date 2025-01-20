import logging
import os.path
import random
from datetime import datetime

import discord
from discord import Member, Message, User, Reaction
from discord.ext import commands
from tinydb import where

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
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        guild: discord.Guild = await lajter.utils.get_default_guild(self.bot)

        for member in guild.members:
            if lajter.user.get_by_id(member.id) is None:
                if not member.bot or not lajter.utils.is_banned(member):
                    db_user = lajter.user.User(member.id)
                    db_user.save()
            if member.bot or lajter.utils.is_banned(member):
                if lajter.user.get_by_id(member.id) is not None:
                    lajter.user.User.db.remove(where('id') == member.id)


    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        if not member.bot and lajter.user.get_by_id(member.id) is None:
            db_user = lajter.user.User(member.id)
            db_user.save()

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if (
                message.author.bot
                or lajter.utils.is_banned(message.author)
                or type(message.author) is User
        ):
            return

        user = lajter.user.get_by_id(message.author.id)
        if not user:
            user = lajter.user.User(message.author.id)
        user.last_activity = datetime.now()
        user.points += lajter.utils.rate_message(message.content)
        user.save()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: User):
        if reaction.message.author.id == user.id:
            return

        db_user = lajter.user.get_by_id(reaction.message.author.id)
        if not db_user:
            return

        db_user.points += 10
        db_user.save()

        await handle_rules(
            [
                lajter.rule.RuleType.POINTS_LESS_THAN,
                lajter.rule.RuleType.POINTS_GREATER_THAN
            ],
            bot=self.bot,
            member=reaction.message.author,
            db_user=db_user,
            channel=reaction.message.channel,
            message=reaction.message
        )

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

    @commands.command(name="points", brief="Wyświetl posiadane punkty")
    @lajter.utils.not_banned()
    async def read_points(self, ctx: commands.Context):
        user = lajter.user.get_by_id(ctx.author.id)

        await ctx.reply(f'Posiadasz **{user.points}** punktów')

    @commands.command(name="give", brief="Przekaż komuś punkty")
    @commands.guild_only()
    @lajter.utils.not_banned()
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

        if giver.id == receiver.id:
            await ctx.reply(f'Nie możesz dawać pieniędzy sobie samemu')
            return

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

            if not lajter.utils.immune(ctx.author):
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

            if not lajter.utils.immune(target):
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
    @commands.cooldown(1, 30)
    async def point_leaderboard(self, ctx: commands.Context):
        async with ctx.typing():
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
    @lajter.utils.not_banned()
    async def coin_flip(self, ctx: commands.Context, amount):
        user = lajter.user.get_by_id(ctx.author.id)

        try:
            amount = int(amount)
        except ValueError:
            amount = user.points

        if (amount == 0 or (amount > 0 and amount > user.points)
                or (amount < 0 and amount < user.points)):
            await ctx.reply("Niewłaściwa liczba punktów")
            return

        if amount < 0:
            tax = -1 * int(amount * 0.25)
            user.points -= tax
            await ctx.reply(f'Pobrano podatek w wysokości {tax} punktów')

        if bool(random.getrandbits(1)):
            amount *= -1

        if amount > 0:
            await ctx.reply(f'Wygrywasz **{amount}** punktów')
        else:
            await ctx.reply(f'Tracisz **{amount}** punktów')

        user.points += amount
        user.save()

        if not lajter.utils.immune(ctx.message.author):
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

    @commands.command(name="word", brief="Powiedz słowo, żeby wygrać punkty")
    @commands.guild_only()
    @commands.cooldown(3, 10)
    @lajter.utils.not_banned()
    async def say_word(self, ctx: commands.Context):
        default_channel = await lajter.utils.get_default_channel(self.bot)
        if ctx.channel.id == default_channel.id:
            await ctx.reply("Idź na spam kanał!!!")
            return

        word = ""
        with open("slowa.txt", "rb") as f:
            seek_range = os.path.getsize("slowa.txt")
            while seek_range > 100:
                seek_range = int(seek_range/2)
                if bool(random.getrandbits(1)):
                    f.seek(seek_range, 1)
            bytes = f.read(100).split(b'\n')
            words = []
            for byte_word in bytes:
                try:
                    words.append(byte_word.decode())
                except UnicodeDecodeError:
                    pass
            word = random.choice(words)
            word = word.strip()

        await ctx.reply(f'Powiedz: *{word}*')

        def check(message: Message):
            return (message.channel == ctx.channel and
            (message.author == ctx.author or word in message.content.lower()))

        reply = await self.bot.wait_for("message", check=check)

        if word in reply.content.lower():
            db_user = lajter.user.get_by_id(reply.author.id)
            points = random.randrange(10, 30)

            db_user.points += points
            db_user.save()
            await reply.reply(f'Otrzymujesz **{points}** punktów')

            await handle_rules(
                [
                    lajter.rule.RuleType.POINTS_LESS_THAN,
                    lajter.rule.RuleType.POINTS_GREATER_THAN
                ],
                bot=self.bot,
                member=ctx.author,
                db_user=db_user,
                channel=ctx.channel,
                message=reply
            )
        else:
            await reply.reply("Zła odpowiedź")
