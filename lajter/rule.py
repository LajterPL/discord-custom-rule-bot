import re
import logging
from enum import Enum
from typing import List

from discord import Member, Spotify, Reaction, TextChannel, Message
from discord.ext import commands
from tinydb import TinyDB, where
import lajter.action
from lajter.action import Action
import lajter.user

logger = logging.getLogger('RULE')
logger.setLevel(logging.DEBUG)

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
    POINTS_LESS_THAN = "less points"
    POINTS_GREATER_THAN = "more points"


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
                rules += f'Jeśli nazwa użytkownika zawiera regex: {self.regexes}, wykonaj akcje: '
            case RuleType.POINTS_LESS_THAN:
                rules += f'Jeśli użytkownik ma mniej niż {self.regexes[0]} punktów, wykonaj akcje: '
            case RuleType.POINTS_LESS_THAN:
                rules += f'Jeśli użytkownik ma więcej niż {self.regexes[0]} punktów, wykonaj akcje: '

        for action_id in self.actions:
            action: Action = lajter.action.get_by_id(action_id)
            if action is not None:
                rules += action.to_string() + ", "
        rules += "\n"
        return rules

    async def check(
            self,
            bot: commands.Bot = None,
            member: Member = None,
            db_user: lajter.user.User = None,
            channel: TextChannel = None,
            message: Message = None,
            reaction: Reaction = None
    ) -> bool:
        match self.rule_type:
            case RuleType.MESSAGE:
                for regex in self.regexes:
                    if re.search(regex, message.content):
                        return True
            case RuleType.ACTIVITY:
                for regex in self.regexes:
                    for activity in member.activities:
                        if type(activity) is Spotify:
                            if (re.search(regex, activity.title)
                                    or re.search(regex, activity.artist)):
                                return True
                        else:
                            if re.search(regex, activity.name):
                                return True
            case RuleType.REACTION:
                for regex in self.regexes:
                    if reaction.emoji == regex:
                        return True
            case RuleType.NAME:
                for regex in self.regexes:
                    if re.search(regex, member.display_name):
                        return True
            case RuleType.POINTS_LESS_THAN:
                if self.regexes:
                    if db_user and db_user.points < int(self.regexes[0]):
                        return True
            case RuleType.POINTS_GREATER_THAN:
                if self.regexes:
                    if db_user.points > int(self.regexes[0]):
                        return True

        return False

    async def execute(
            self,
            bot: commands.Bot = None,
            member: Member = None,
            db_user: lajter.user.User = None,
            channel: TextChannel = None,
            message: Message = None
    ):
        for action_id in self.actions:
            action = lajter.action.get_by_id(action_id)
            await action.execute(bot, member, db_user, channel, message)
