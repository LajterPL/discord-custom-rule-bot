import logging
from typing import Tuple, List

from discord import Member, TextChannel, Message, Reaction
from discord.ext import commands
from tinydb import where

import lajter.action
import lajter.rule
from lajter.rule import RuleType
from lajter.rule import Rule
import lajter.user
import lajter.utils as utils


logger = logging.getLogger('RULES')
logger.setLevel(logging.DEBUG)
async def setup(bot: commands.Bot):
    await bot.add_cog(Rules(bot))

async def handle_rules(
            rule_types: List[RuleType],
            bot: commands.Bot = None,
            member: Member = None,
            db_user: lajter.user.User = None,
            channel: TextChannel = None,
            message: Message = None,
            reaction: Reaction = None
):
    if member:
        db_user = lajter.user.get_by_id(member.id)
    broken_rules = []

    for rule_type in rule_types:
        rules = Rule.db.search(where('type') == rule_type.value)
        rules = [lajter.rule.from_entry(entry) for entry in rules]
        broken_rules.extend([rule for rule in rules if await rule.check(bot, member, db_user, channel, message, reaction)])

    for rule in broken_rules:
        await rule.execute(bot, member, db_user, channel, message)


class Rules(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    class RuleFlags(commands.FlagConverter):
        rule_type: str = commands.flag(default=None, name="type", aliases=["t"])
        regexes: Tuple[str, ...] = commands.flag(default=(), aliases=["regex", "r"])
        actions: Tuple[int, ...] = commands.flag(default=(), aliases=["action", "a"])

    @commands.Cog.listener()
    async def on_presence_update(self, before: Member, after: Member):
        if lajter.utils.is_admin(after):
            return

        if before.activities:
            await handle_rules([RuleType.ACTIVITY], bot=self.bot, member=before)
        if after.activities:
            await handle_rules([RuleType.ACTIVITY], bot=self.bot, member=after)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if not utils.is_admin(message.author):
            await handle_rules(
                [
                    RuleType.MESSAGE,
                    RuleType.POINTS_LESS_THAN,
                    RuleType.POINTS_GREATER_THAN
                ],
                bot=self.bot,
                member=message.author,
                message=message,
                channel=message.channel
            )


    @commands.Cog.listener()
    async def on_message_edit(self, before: Message, after: Message):
        if not utils.is_admin(after.author):
            await handle_rules([RuleType.MESSAGE], bot=self.bot, message=after)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, member: Member):
        if not utils.is_admin(member):
            await handle_rules([RuleType.REACTION], bot=self.bot, member=member, reaction=reaction)

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        if not utils.is_admin(member):
            await handle_rules([RuleType.NAME], bot=self.bot, member=member)

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        if not utils.is_admin(after):
            await handle_rules([RuleType.NAME], bot=self.bot, member=before)
            await handle_rules([RuleType.NAME], bot=self.bot, member=after)

    @commands.command(name="addrule")
    async def add_rule(self, ctx: commands.Context, *, flags: RuleFlags):
        if not utils.is_admin(ctx.author):
            return

        rule = Rule(flags.rule_type, regexes=list(flags.regexes),
                    actions=list(flags.actions))
        rule.save()
        await ctx.send(f'Utworzono zasadę: {rule.to_string()}')


    @commands.command(name="editrule")
    async def edit_rule(self, ctx: commands.Context, rule_id: int, *, flags: RuleFlags):
        if not utils.is_admin(ctx.author):
            return

        if rule_id <= 0:
            await ctx.send("Niepoprawne id zasady")
            return

        rule = lajter.rule.get_by_id(rule_id)

        if rule is None:
            await ctx.send("Nie ma zasady o podanym id")
            return

        if flags.rule_type is not None:
            rule.rule_type = lajter.rule.RuleType(flags.rule_type)

        if len(flags.regexes) > 0:
            rule.regexes = list(flags.regexes)

        if len(flags.actions) > 0:
            rule.actions = list(flags.actions)

        rule.save()
        await ctx.send(f'Nadpisano zasadę: {rule.to_string()}')


    @commands.command(name="delrule")
    async def remove_rule(self, ctx: commands.Context, rule_id: int):
        if not utils.is_admin(ctx.author):
            return
        Rule.db.remove(doc_ids=[rule_id])
        await ctx.send(f'Usunięto zasadę nr **{rule_id}**')


    @commands.command(name="rules")
    async def read_rules(self, ctx: commands.Context):
        if not utils.is_admin(ctx.author):
            return

        rules = ""
        for rule_entry in Rule.db.all():
            rule = lajter.rule.from_entry(rule_entry)
            rules += rule.to_string()
        await ctx.reply(rules)


    @commands.command(name="ruletypes")
    async def read_rule_types(self, ctx: commands.Context):
        if not utils.is_admin(ctx.author):
            return

        s = "**Dostępne rodzaje zasad:** "
        for rule_type in lajter.rule.RuleType:
            s += f'`{rule_type.value}` '

        await ctx.reply(s)