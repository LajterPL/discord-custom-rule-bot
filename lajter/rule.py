import re
import logging
from enum import Enum
from typing import List

import discord
from discord import Member, Spotify, Reaction
from discord.ext import commands
from tinydb import TinyDB, where
import lajter.action
from lajter.action import Action


logger = logging.getLogger('RULE')
logger.setLevel(logging.DEBUG)

async def handle_message_rules(bot: commands.Bot, message: discord.Message):
    # Look for message rules that have matched with a regex
    results = Rule.db.search(where('type') == RuleType.MESSAGE.value)
    broken_rules = []
    for res in results:
        for regex in res['regexes']:
            if re.search(regex, message.content):
                broken_rules.append(res['id'])
                break

    if len(broken_rules) > 0:
        logger.info(
            f'Message from {message.author} triggered some rules: {message.content}')

    # Execute all actions related to matched rules
    for rule_id in broken_rules:
        rule = get_by_id(rule_id)
        await rule.execute(bot, message.author, message.channel, message)

async def handle_activity_rules(bot: commands.Bot, member: Member):
    # Look for message rules that have matched with a regex
    results = Rule.db.search(where('type') == RuleType.ACTIVITY.value)
    broken_rules = []
    for res in results:
        for regex in res['regexes']:
            for activity in member.activities:
                if type(activity) is Spotify:
                    if re.search(regex, activity.title) or re.search(regex, activity.artist):
                        broken_rules.append(res['id'])
                        break
                else:
                    if re.search(regex, activity.name):
                        broken_rules.append(res['id'])
                        break

    if len(broken_rules) > 0:
        logger.info(
            f'Activity from {member} triggered some rules: {member.activities}')

    # Execute all actions related to matched rules
    for rule_id in broken_rules:
        rule = get_by_id(rule_id)
        await rule.execute(bot, member)

async def handle_reaction_rules(bot: commands.Bot, member: Member, reaction: Reaction):
    # Look for message rules that have matched with a regex
    results = Rule.db.search(where('type') == RuleType.REACTION.value)
    broken_rules = []
    for res in results:
        for regex in res['regexes']:
            if reaction.emoji == regex:
                broken_rules.append(res['id'])
                break

    if len(broken_rules) > 0:
        logger.info(
            f'Reaction from {member} triggered some rules: {reaction}')

    # Execute all actions related to matched rules
    for rule_id in broken_rules:
        rule = get_by_id(rule_id)
        await rule.execute(bot, member, reaction.message.channel, reaction.message)

async def handle_user_name_rules(bot: commands.Bot, member: Member):
    # Look for message rules that have matched with a regex
    results = Rule.db.search(where('type') == RuleType.NAME.value)
    broken_rules = []
    for res in results:
        for regex in res['regexes']:
            if re.search(regex, member.display_name):
                broken_rules.append(res['id'])
                break

    if len(broken_rules) > 0:
        logger.info(
            f'User name of {member} triggered some rules: {member.display_name}')

    # Execute all actions related to matched rules
    for rule_id in broken_rules:
        rule = get_by_id(rule_id)
        await rule.execute(bot, member)

def get_by_id(rule_id):
    entries = Rule.db.search(where('id') == rule_id)
    if len(entries) > 0:
        return from_entry(entries[0])
    return None

def from_entry(entry):
    return Rule(
        entry['type'],
        entry['id'],
        entry['regexes'],
        entry['actions']
    )

class RuleType(Enum):
    MESSAGE = "message"
    ACTIVITY = "activity"
    REACTION = "reaction"
    NAME = "name"

class Rule:
    db = TinyDB("rules.json")

    def __init__(self, rule_type, rule_id=None, regexes=None, actions=None):
        self.id: int = rule_id

        if type(rule_type) is str:
            self.rule_type: RuleType = RuleType(rule_type)

        if regexes is None:
            self.regexes: List[str] = []
        else:
            self.regexes: List[str] = regexes

        if actions is None:
            self.actions: List[int] = []
        else:
            self.actions: List[int] = actions

    def save(self):
        if self.id is None:
            self.id = Rule.db.insert({
                'id': 'null',
                'type': self.rule_type.value,
                'regexes': self.regexes,
                'actions': self.actions
            })

            Rule.db.update({'id': self.id}, doc_ids=[self.id])
        else:
            Rule.db.upsert({
                'id': self.id,
                'type': self.rule_type.value,
                'regexes': self.regexes,
                'actions': self.actions
            }, where('id') == self.id)

    def to_string(self) -> str:
        rules = f'**{self.id}**: '

        match self.rule_type:
            case RuleType.MESSAGE:
                rules += f'Jeśli wiadomość zawiera regex: {self.regexes}, wykonaj akcje: '
            case RuleType.ACTIVITY:
                rules += f'Jeśli aktywność zawiera regex: {self.regexes}, wykonaj akcje: '
            case RuleType.REACTION:
                rules += f'Jeśli użytkownik użyje reakcji: {self.regexes}, wykonaj akcje: '
            case RuleType.NAME:
                rules += f'Jeśli nazwa użytkownika zawiera regex: {self.regexes}, wykonaj akcję: '

        for action_id in self.actions:
            action: Action = lajter.action.get_by_id(action_id)
            if action is not None:
                rules += action.to_string() + ", "
        rules += "\n"
        return rules

    async def execute(
            self,
            client,
            user=None,
            channel=None,
            message=None,
    ):
        for action_id in self.actions:
            action = lajter.action.get_by_id(action_id)
            await action.execute(client, user, channel, message)
