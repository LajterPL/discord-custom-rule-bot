import traceback
from datetime import timedelta

from discord.utils import get
from tinydb import TinyDB, where
import discord
import logging
from enum import Enum

from lajter.utils import role_from_mention, member_from_mention

logger = logging.getLogger('ACTION')
logger.setLevel(logging.DEBUG)


def get_by_id(id):
    entries = Action.db.search(where('id') == id)
    if len(entries) > 0:
        return from_entry(entries[0])
    return None


def from_entry(entry):
    return Action(
        entry['type'],
        entry['id'],
        entry['value'],
        entry['target']
    )

class ActionType(Enum):
    SEND_MESSAGE = "send message"
    DELETE_MESSAGE = "delete message"
    KICK = "kick"
    TIMEOUT = "timeout"
    BAN = "ban"
    GIVE_ROLE = "give role"
    REMOVE_ROLE = "remove role"
    CHANGE_NAME = "change name"

class Action:
    db = TinyDB("actions.json")

    def __init__(self, action_type, action_id=None, value=None, target=None):
        self.id = action_id

        if type(action_type) is str:
            self.action_type: ActionType = ActionType(action_type)

        if value is None:
            self.value = []
        else:
            self.value = value

        if target is None:
            self.target = []
        else:
            self.target = target

    def save(self):
        if self.id is None:
            self.id = Action.db.insert({
                'id': 'null',
                'type': self.action_type.value,
                'value': self.value,
                'target': self.target
            })

            Action.db.update({'id': self.id}, doc_ids=[self.id])
        else:
            Action.db.upsert({
                'id': self.id,
                'type': self.action_type.value,
                'value': self.value,
                'target': self.target
            }, where('id') == self.id)

    def to_string(self) -> str:
        s = ""
        match self.action_type:
            case ActionType.SEND_MESSAGE:
                s += f'Wyślij wiadomość o treści "{self.value[0]}"'
                if self.target:
                    s += f' na kanał {self.target}'
            case ActionType.DELETE_MESSAGE:
                s += "Usuń wiadomość"
                if self.value:
                    s += f' po {self.value[0]} sekundach'
            case ActionType.GIVE_ROLE:
                s += f'Daj rolę {self.value[0]}'
                if self.target:
                    s += f' użytkownikowi {self.target[0]}'
            case ActionType.REMOVE_ROLE:
                s += f'Zabierz rolę {self.value[0]}'
                if self.target:
                    s += f' użytkownikowi {self.target[0]}'
            case ActionType.TIMEOUT:
                s += "Wyślij użytkownika"
                if self.target:
                    s += f' {self.target[0]}'
                s += f' na przerwę przez {self.value[0]} sekund'
            case ActionType.KICK:
                s += "Zkickuj użytkownika"
                if self.target:
                    s += f' {self.target[0]}'
            case ActionType.BAN:
                s += "Zbanuj użytkownika"
                if self.target:
                    s += f' {self.target[0]}'
            case ActionType.CHANGE_NAME:
                s += "Zmień nazwę użytkownika"
                if self.target:
                    s += f' {self.target[0]}'
                s += f' na {self.value[0]}'
        return s
    async def execute(
            self,
            client: discord.Client,
            user: discord.Member = None,
            channel: discord.TextChannel = None,
            message: discord.Message = None
    ):
        match self.action_type:
            case ActionType.SEND_MESSAGE:
                try:
                    if self.target:
                        for target in self.target:
                            target_channel = await client.fetch_channel(target)
                            await target_channel.send(self.value)
                    if channel is not None:
                        await channel.send(self.value)
                except Exception:
                    logger.warning(f'Failed to send a message: {traceback.format_exc()}')
            case ActionType.DELETE_MESSAGE:
                if message is not None:
                    try:
                        if self.value:
                            await message.delete(delay=float(self.value[0]))
                        else:
                            await message.delete()
                    except Exception:
                        logger.warning(f'Failed to remove a message: {traceback.format_exc()}')
            case ActionType.GIVE_ROLE:
                if self.value:
                    try:
                        role = role_from_mention(user.guild, self.value[0])
                        target = user
                        if self.target:
                            target = await member_from_mention(user.guild, self.target[0])
                        await target.add_roles(role)
                    except Exception:
                        logger.warning(f'Failed to add a role: {traceback.format_exc()}')
            case ActionType.REMOVE_ROLE:
                if self.value:
                    try:
                        role = role_from_mention(user.guild, self.value[0])
                        target = user
                        if self.target:
                            target = await member_from_mention(user.guild, self.target[0])
                        await target.remove_roles(role)
                    except Exception:
                        logger.warning(f'Failed to remove a role: {traceback.format_exc()}')
            case ActionType.TIMEOUT:
                if self.value:
                    try:
                        target = user
                        if self.target:
                            target = await member_from_mention(user.guild, self.target[0])
                        await target.timeout(timedelta(seconds=float(self.value[0])))
                    except Exception:
                        logger.warning(f'Failed to timeout an user: {traceback.format_exc()}')
            case ActionType.KICK:
                try:
                    target = user
                    if self.target:
                        target = await member_from_mention(user.guild, self.target[0])
                    await target.kick()
                except Exception:
                    logger.warning(f'Failed to kick an user: {traceback.format_exc()}')
            case ActionType.BAN:
                try:
                    target = user
                    if self.target:
                        target = await member_from_mention(user.guild, self.target[0])
                    await target.ban(delete_message_seconds=0)
                except Exception:
                    logger.warning(f'Failed to ban an user: {traceback.format_exc()}')
            case ActionType.CHANGE_NAME:
                try:
                    target = user
                    if self.target:
                        target = await member_from_mention(user.guild, self.target[0])
                    await target.edit(nick=self.value[0])
                except Exception:
                    logger.warning(f'Failed to change name: {traceback.format_exc()}')


