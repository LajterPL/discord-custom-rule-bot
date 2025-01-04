from typing import List, Tuple, Union

from discord import Member
from discord.ext import commands
import lajter.action
from lajter.action import Action
import lajter.utils as utils
import lajter.rule
from lajter.rule import Rule
import logging

logger = logging.getLogger('COMMAND')
logger.setLevel(logging.DEBUG)


def register_commands(bot: commands.Bot):
    logger.info("Registering commands...")
    bot.add_command(read_rules)
    bot.add_command(read_rule_types)
    bot.add_command(add_rule)
    bot.add_command(remove_rule)
    bot.add_command(edit_rule)

    bot.add_command(read_actions)
    bot.add_command(read_action_types)
    bot.add_command(add_action)
    bot.add_command(remove_action)
    bot.add_command(edit_action)

'''RULES'''


class RuleFlags(commands.FlagConverter):
    rule_type: str = commands.flag(default=None, name="type", aliases=["t"])
    regexes: Tuple[str, ...] = commands.flag(default=(), aliases=["regex", "r"])
    actions: Tuple[int, ...] = commands.flag(default=(), aliases=["action", "a"])


@commands.command(name="addrule")
async def add_rule(ctx: commands.Context, *, flags: RuleFlags):
    if not utils.is_admin(ctx.author):
        return

    rule = Rule(flags.rule_type, regexes=list(flags.regexes),
                actions=list(flags.actions))
    rule.save()
    await ctx.send(f'Utworzono zasadę: {rule.to_string()}')


@commands.command(name="editrule")
async def edit_rule(ctx: commands.Context, rule_id: int, *, flags: RuleFlags):
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
async def remove_rule(ctx: commands.Context, rule_id: int):
    if not utils.is_admin(ctx.author):
        return
    Rule.db.remove(doc_ids=[rule_id])
    await ctx.send(f'Usunięto zasadę nr **{rule_id}**')


@commands.command(name="rules")
async def read_rules(ctx: commands.Context):
    if not utils.is_admin(ctx.author):
        return

    rules = ""
    for rule_entry in Rule.db.all():
        rule = lajter.rule.from_entry(rule_entry)
        rules += rule.to_string()
    await ctx.reply(rules)


@commands.command(name="ruletypes")
async def read_rule_types(ctx: commands.Context):
    if not utils.is_admin(ctx.author):
        return

    s = "**Dostępne rodzaje zasad:** "
    for rule_type in lajter.rule.RuleType:
        s += f'`{rule_type.value}` '

    await ctx.reply(s)


'''ACTIONS'''

class ActionFlags(commands.FlagConverter):
    action_type: str = commands.flag(default=None, name="type")
    value: Tuple[str, ...] = commands.flag(default=(), aliases=["v"])
    target: Tuple[str, ...] = commands.flag(default=(), aliases=["t"])


@commands.command(name="addaction")
async def add_action(ctx: commands.Context, *, flags: ActionFlags):
    if not utils.is_admin(ctx.author):
        return

    action = Action(flags.action_type, value=list(flags.value), target=list(flags.target))
    action.save()

    await ctx.send(f'Utworzono akcję: **{action.id}:** {action.to_string()}')

@commands.command(name="editaction")
async def edit_action(ctx: commands.Context, action_id: int, *, flags: ActionFlags):
    if not utils.is_admin(ctx.author):
        return

    if action_id <= 0:
        await ctx.send("Niepoprawne id akcji")
        return

    action = lajter.action.get_by_id(action_id)

    if action is None:
        await ctx.send("Nie ma akcji o podanym id")
        return

    if flags.action_type is not None:
        action.rule_type = lajter.rule.Action(flags.action_type)

    if len(flags.value) > 0:
        action.value = list(flags.value)

    if len(flags.target) > 0:
        action.target = list(flags.target)

    action.save()
    await ctx.send(f'Nadpisano akcję: **{action.id}:** {action.to_string()}')


@commands.command(name="delaction")
async def remove_action(ctx: commands.Context, action_id: int):
    if not utils.is_admin(ctx.author):
        return
    Action.db.remove(doc_ids=[action_id])
    await ctx.send(f'Usunięto akcję nr **{action_id}**')


@commands.command(name="actions")
async def read_actions(ctx: commands.Context):
    if not utils.is_admin(ctx.author):
        return

    actions = ""
    for action_entry in Action.db.all():
        action = lajter.action.from_entry(action_entry)
        actions += f'**{action.id}:** '
        actions += action.to_string()
        actions += "\n"
    await ctx.reply(actions)

@commands.command(name="actiontypes")
async def read_action_types(ctx: commands.Context):
    if not utils.is_admin(ctx.author):
        return

    s = "**Dostępne rodzaje akcji:** "
    for action_type in lajter.action.ActionType:
        s += f'`{action_type.value}` '

    await ctx.reply(s)
