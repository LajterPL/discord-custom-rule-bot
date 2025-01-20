import logging
from typing import Tuple

from discord.ext import commands
from tinydb import where

import lajter.action
from lajter.action import Action
import lajter.utils as utils
import lajter.rule
import lajter.user

logger = logging.getLogger('ACTION')
logger.setLevel(logging.DEBUG)


async def setup(bot: commands.Bot):
    await bot.add_cog(Actions(bot))


class Actions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class ActionFlags(commands.FlagConverter):
        action_type: str = commands.flag(default=None, name="type")
        value: Tuple[str, ...] = commands.flag(default=(), aliases=["v"])
        target: Tuple[str, ...] = commands.flag(default=(), aliases=["t"])
        public: bool = commands.flag(default=(False), aliases=["p"])

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
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply("Nie masz uprawnień do tej komendy")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.reply("Nie ma takiej komendy")


    @commands.command(
        name="addaction",
        brief="Dodaj akcję",
        help="type: <typ akcji> value: <wartość> target: <wartość>"
    )
    @commands.has_guild_permissions(administrator=True)
    async def add_action(self, ctx: commands.Context, *, flags: ActionFlags):
        if not utils.immune(ctx.author):
            return

        action = Action(flags.action_type, value=list(flags.value),
                        target=list(flags.target), public=flags.public)
        action.save()
        logger.info(f'{ctx.author} utworzył akcję: {action.to_string()}')
        await ctx.send(
            f'Utworzono akcję: **{action.id}:** {action.to_string()}')

    @commands.command(name="editaction")
    @commands.has_guild_permissions(administrator=True)
    async def edit_action(self, ctx: commands.Context, action_id: int, *,
                          flags: ActionFlags):
        if action_id <= 0:
            await ctx.send("Niepoprawne id akcji")
            return

        action = lajter.action.get_by_id(action_id)

        if action is None:
            await ctx.send("Nie ma akcji o podanym id")
            return

        if flags.public:
            action.public = flags.public

        if flags.action_type is not None:
            action.rule_type = lajter.rule.Action(flags.action_type)

        if len(flags.value) > 0:
            action.value = list(flags.value)

        if len(flags.target) > 0:
            action.target = list(flags.target)

        action.save()
        logger.info(f'{ctx.author} nadpisał akcję: {action.to_string()}')
        await ctx.send(
            f'Nadpisano akcję: **{action.id}:** {action.to_string()}')

    @commands.command(name="delaction")
    @commands.has_guild_permissions(administrator=True)
    async def remove_action(self, ctx: commands.Context, action_id: int):
        Action.db.remove(doc_ids=[action_id])
        logger.info(f'{ctx.author} usunął akcję: {action_id}')
        await ctx.send(f'Usunięto akcję nr **{action_id}**')

    @commands.command(name="actions", brief="Wyświetl akcje")
    @commands.has_guild_permissions(administrator=True)
    async def read_actions(self, ctx: commands.Context):
        actions = ""
        for action_entry in Action.db.all():
            action = lajter.action.from_entry(action_entry)
            actions += f'**{action.id}:** '
            actions += action.to_string()
            actions += "\n"
        await ctx.reply(actions)

    @commands.command(name="publicactions", brief="Wyświetl publiczne akcje")
    @commands.cooldown(3, 30)
    async def read_public_actions(self, ctx: commands.Context):
        actions = ""
        for action_entry in Action.db.search(where('public') == True):
            action = lajter.action.from_entry(action_entry)
            actions += f'**{action.id}:** '
            actions += action.to_string()
            actions += "\n"
            if len(actions) > 1500:
                await ctx.reply(actions)
                actions = ""

        if actions:
            await ctx.reply(actions)

    @commands.command(name="actiontypes", brief="Wyświetl typy akcji")
    @commands.has_guild_permissions(administrator=True)
    async def read_action_types(self, ctx: commands.Context):
        s = "**Dostępne rodzaje akcji:** "
        for action_type in lajter.action.ActionType:
            s += f'`{action_type.value}` '

        await ctx.reply(s)
