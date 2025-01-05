import asyncio
import traceback
from datetime import timedelta

from discord import Member, TextChannel, Message
from discord.ext import commands
from tinydb import TinyDB, where
import logging
from enum import Enum

import lajter.user
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
    ADD_POINTS = "add points"
    POLL = "poll"

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
            case ActionType.ADD_POINTS:
                s += f'Dodaj {self.value[0]} punktów'
                if self.target:
                    s += f' użytkownikowi {self.target[0]}'
            case ActionType.POLL:
                s += f'Rozpocznij głosowanie przeciwko użytkownikowi'
                if len(self.target) > 1:
                    s += f' {self.target[1]}'
                if self.target:
                    s += f' na kanale {self.target[0]}'
                s += "."
                if self.value:
                    s += f' Jeśli głosowanie przejdzie, wykonaj akcję nr {self.value[0]}.'
                if len(self.value) > 1:
                    s += f' Głosowanie będzie trwało {self.value[1]} sekund.'

        return s
    async def execute(
            self,
            bot: commands.Bot = None,
            member: Member = None,
            db_user: lajter.user.User = None,
            channel: TextChannel = None,
            message: Message = None,
    ):
        if channel is None:
            channel = await lajter.utils.get_default_channel(bot)

        match self.action_type:
            case ActionType.SEND_MESSAGE:
                try:
                    if self.target:
                        for target in self.target:
                            target_channel = await bot.fetch_channel(target)
                            await target_channel.send(self.value[0])
                    if channel is not None:
                        await channel.send(self.value[0])
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
                        role = role_from_mention(member.guild, self.value[0])
                        target = member
                        if self.target:
                            target = await member_from_mention(member.guild, self.target[0])
                        await target.add_roles(role)
                    except Exception:
                        logger.warning(f'Failed to add a role: {traceback.format_exc()}')
            case ActionType.REMOVE_ROLE:
                if self.value:
                    try:
                        role = role_from_mention(member.guild, self.value[0])
                        target = member
                        if self.target:
                            target = await member_from_mention(member.guild, self.target[0])
                        await target.remove_roles(role)
                    except Exception:
                        logger.warning(f'Failed to remove a role: {traceback.format_exc()}')
            case ActionType.TIMEOUT:
                if self.value:
                    try:
                        target = member
                        if self.target:
                            target = await member_from_mention(member.guild, self.target[0])
                        await target.timeout(timedelta(seconds=float(self.value[0])))
                    except Exception:
                        logger.warning(f'Failed to timeout an user: {traceback.format_exc()}')
            case ActionType.KICK:
                try:
                    target = member
                    if self.target:
                        target = await member_from_mention(member.guild, self.target[0])
                    await target.kick()
                except Exception:
                    logger.warning(f'Failed to kick an user: {traceback.format_exc()}')
            case ActionType.BAN:
                try:
                    target = member
                    if self.target:
                        target = await member_from_mention(member.guild, self.target[0])
                    await target.ban(delete_message_seconds=0)
                except Exception:
                    logger.warning(f'Failed to ban an user: {traceback.format_exc()}')
            case ActionType.CHANGE_NAME:
                try:
                    target = member
                    if self.target:
                        target = await member_from_mention(member.guild, self.target[0])
                    if target.guild.owner is not target:
                        await target.edit(nick=self.value[0])
                except Exception:
                    logger.warning(f'Failed to change name: {traceback.format_exc()}')
            case ActionType.ADD_POINTS:
                try:
                    target = db_user
                    if self.target:
                        target = await member_from_mention(member.guild, self.target[0])
                        target = lajter.user.get_by_id(target.id)

                    target.points += int(self.value[0])
                    target.save()
                except Exception:
                    logger.warning(
                        f'Failed to change name: {traceback.format_exc()}')
            case ActionType.POLL:
                try:
                    target = member
                    target_channel = channel

                    if self.target:
                        target_channel = await bot.fetch_channel(
                            self.target[0][2:-1])

                    if len(self.target) > 1:
                        target = await member_from_mention(member.guild,
                                                           self.target[1])

                    timeout = timedelta(minutes=5)
                    action_to_execute = None

                    if self.value:
                        action_to_execute = get_by_id(int(self.value[0]))
                    if len(self.value) > 1:
                        timeout = timedelta(seconds=int(self.value[1]))

                    s = f'Rozpoczęto głosowanie przeciwko {target.mention}.\nPotrzeba powyżej 50% głosów'
                    if action_to_execute:
                        s += f', żeby wykonać akcję: {action_to_execute.to_string()}'
                    s += ".\n"
                    s += f' Głosowanie potrwa: `{timeout}`'

                    poll = await target_channel.send(s)
                    await poll.add_reaction("👍")
                    await poll.add_reaction("👎")

                    await asyncio.sleep(timeout.seconds)

                    poll = await target_channel.fetch_message(poll.id)

                    result = 0

                    for reaction in poll.reactions:
                        if reaction.emoji == "👍":
                            result += reaction.count
                        elif reaction.emoji == "👎":
                            result -= reaction.count

                    if result > 0:
                        await poll.reply(f'Głosowanie przeciwko {target.mention} przeszło większością głosów.')
                        if action_to_execute:
                            if target != member:
                                db_user = lajter.user.get_by_id(target.id)
                            await action_to_execute.execute(bot, target, db_user, channel)
                    else:
                        await poll.reply(f'Głosowanie przeciwko {target.mention} nie uzyskało większości głosów.')


                except Exception:
                    logger.warning(
                        f'Failed to change name: {traceback.format_exc()}')