import asyncio
import datetime
import random
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
    try:
        return Action(
            entry['type'],
            entry['id'],
            entry['value'],
            entry['target'],
            entry['public']
        )
    except KeyError:
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
    RANDOM = "random"
    CHAIN = "chain"

class Action:
    db = TinyDB("actions.json")

    def __init__(self, action_type: ActionType | str, action_id=None,
                 value=None, target=None, public=False):
        self.id = action_id

        if type(action_type) is str:
            self.action_type: ActionType = ActionType(action_type)
        else:
            self.action_type = action_type

        if value is None:
            self.value = []
        else:
            self.value = value

        if target is None:
            self.target = []
        else:
            self.target = target

        if type(public) is bool:
            self.public = public
        else:
            self.public = bool(public)

    def save(self):
        if self.id is None:
            self.id = Action.db.insert({
                'id': 'null',
                'type': self.action_type.value,
                'value': self.value,
                'target': self.target,
                'public': self.public
            })

            Action.db.update({'id': self.id}, doc_ids=[self.id])
        else:
            Action.db.upsert({
                'id': self.id,
                'type': self.action_type.value,
                'value': self.value,
                'target': self.target,
                'public': self.public
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
                    s += " Jeśli głosowanie przejdzie, wykonaj akcję: "
                    action_to_execute = get_by_id(int(self.value[0]))
                    if action_to_execute:
                        s += action_to_execute.to_string()
                    else:
                        s += "Błędna akcja"
                    s += "."
                if len(self.value) > 1:
                    s += f' Głosowanie będzie trwało {self.value[1]} sekund.'
            case ActionType.RANDOM:
                s += "Wybierz losową akcję spośród: "
                for value in self.value:
                    s += f'{value}, '
            case ActionType.CHAIN:
                s += "Wykonaj po kolei akcje: "
                for value in self.value:
                    action_to_execute = get_by_id(int(value))
                    if action_to_execute:
                        s += action_to_execute.to_string()
                    else:
                        s += "Błędna akcja"
                    s += ", "

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

        if db_user is None and member:
            db_user = lajter.user.get_by_id(member.id)

        try:
            match self.action_type:
                case ActionType.SEND_MESSAGE:
                    if self.target:
                        for target in self.target:
                            target_channel = await bot.fetch_channel(target)
                            await target_channel.send(self.value[0])
                    elif channel:
                        await channel.send(self.value[0])
                case ActionType.DELETE_MESSAGE:
                    if message:
                        if self.value:
                            await message.delete(delay=float(self.value[0]))
                        else:
                            await message.delete()
                case ActionType.GIVE_ROLE:
                    if member and self.value:
                        role = role_from_mention(member.guild, self.value[0])
                        target = member
                        if self.target:
                            target = await member_from_mention(
                                member.guild, self.target[0])
                        await target.add_roles(role)
                case ActionType.REMOVE_ROLE:
                    if member and self.value:
                        role = role_from_mention(member.guild, self.value[0])
                        target = member
                        if self.target:
                            target = await member_from_mention(
                                member.guild, self.target[0])
                        await target.remove_roles(role)
                case ActionType.TIMEOUT:
                    if member and self.value:
                        time = float(self.value[0])
                        target = member
                        if self.target:
                            target = await member_from_mention(
                                member.guild, self.target[0])
                        await target.timeout(timedelta(seconds=time))
                case ActionType.KICK:
                    if member:
                        target = member
                        if self.target:
                            target = await member_from_mention(
                                member.guild, self.target[0])
                        await target.kick()
                case ActionType.BAN:
                    if member:
                        target = member
                        ban_role = await lajter.utils.get_ban_role(bot)
                        if self.target:
                            target = await member_from_mention(
                                member.guild, self.target[0])
                        await target.add_roles(ban_role)
                        await channel.send(f'{member.mention} Bardzo się '
                                           f'starałeś, ale z gry wyleciałeś. '
                                           f'punkty: {db_user.points}')
                        print(lajter.user.User.db.remove(where('id') == db_user.id))
                        db_user = None
                case ActionType.CHANGE_NAME:
                    if member and self.value:
                        target = member
                        if self.target:
                            target = await member_from_mention(
                                member.guild, self.target[0])
                        await target.edit(nick=self.value[0])
                case ActionType.ADD_POINTS:
                    if db_user and self.value:
                        target = db_user
                        if self.target:
                            target = await member_from_mention(
                                member.guild, self.target[0])
                            target = lajter.user.get_by_id(target.id)
                        target.points += int(self.value[0])
                case ActionType.POLL:
                    if member and channel:
                        target = member
                        target_channel = channel

                        if self.target:
                            target_channel = await bot.fetch_channel(
                                self.target[0][2:-1])

                        if len(self.target) > 1:
                            target = await member_from_mention(
                                member.guild,self.target[1])

                        timeout = timedelta(minutes=5)
                        action_to_execute = None

                        if self.value:
                            action_to_execute = get_by_id(int(self.value[0]))
                        if len(self.value) > 1:
                            timeout = timedelta(seconds=int(self.value[1]))

                        vote_until = datetime.datetime.now() + timeout

                        s = "Rozpoczęto głosowanie przeciwko "
                        s += target.mention
                        s += ".\nPotrzeba powyżej 50% głosów"
                        if action_to_execute:
                            s += (f', żeby wykonać akcję: '
                                  f'{action_to_execute.to_string()}')
                        s += ".\n"
                        s += f' Głosowanie potrwa do `{vote_until.hour}:{vote_until.minute}`'

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
                            await poll.reply(f'Głosowanie przeciwko '
                                             f'{target.mention} przeszło '
                                             f'większością głosów.')
                            if action_to_execute:
                                if target != member:
                                    db_user = lajter.user.get_by_id(target.id)
                                await action_to_execute.execute(
                                    bot, target, db_user, channel)
                        else:
                            await poll.reply(f'Głosowanie przeciwko '
                                             f'{target.mention} nie uzyskało '
                                             f'większości głosów.')
                case ActionType.RANDOM:
                    if self.value:
                        random_action = random.choice(self.value)
                        random_action = get_by_id(int(random_action))
                        await random_action.execute(bot, member, db_user,
                                                    channel, message)
                case ActionType.CHAIN:
                    if self.value:
                        for action_id in self.value:
                            action = get_by_id(int(action_id))
                            await action.execute(bot, member, db_user,
                                                 channel,message)

        except Exception:
            logger.error(f'Failed to execute action: {traceback.format_exc()}')
        if db_user:
            db_user.save()
