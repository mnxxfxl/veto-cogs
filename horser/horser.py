from typing import Literal

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.menus import menu

import aiofiles

from horser.embeds import *

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]

MAX_APP_EMOJIS = 2000

class Horser(commands.Cog):
    """
    A horse-racing simulation game.
    """

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=314665745441095680,
            force_registration=True,
        )

        emojis_config = {
            "emoji_horse_aqua": "NotSet",
            "emoji_horse_ash": "NotSet",
            "emoji_horse_black": "NotSet",
            "emoji_horse_blue": "NotSet",
            "emoji_horse_brown": "NotSet",
            "emoji_horse_chocolate": "NotSet",
            "emoji_horse_cream": "NotSet",
            "emoji_horse_diamond": "NotSet",
            "emoji_horse_green": "NotSet",
            "emoji_horse_grey": "NotSet",
            "emoji_horse_lime": "NotSet",
            "emoji_horse_orange": "NotSet",
            "emoji_horse_pink": "NotSet",
            "emoji_horse_purple": "NotSet",
            "emoji_horse_red": "NotSet",
            "emoji_horse_sky": "NotSet",
            "emoji_horse_soot": "NotSet",
            "emoji_horse_white": "NotSet",
            "emoji_horse_yellow": "NotSet",
            "emoji_horse_zombie": "NotSet",
        }

        self.config.register_global(**emojis_config)

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int) -> None:
        # TODO: Replace this with the proper end user data removal handling.
        super().red_delete_data_for_user(requester=requester, user_id=user_id)

    async def cog_load(self) -> None:
        # This method is called when the cog is loaded.

        # Load custom emojis into config, creating them if necessary
        all_emojis = await self.bot.fetch_application_emojis()
        # Horse emojis
        for emoji_name in ("horse_aqua", "horse_ash", "horse_black", "horse_blue", "horse_brown", "horse_chocolate", "horse_cream",
                           "horse_diamond", "horse_green", "horse_grey", "horse_lime", "horse_orange", "horse_pink", "horse_purple",
                           "horse_red", "horse_sky", "horse_soot", "horse_white", "horse_yellow", "horse_zombie"):
            emoji = next((emoji for emoji in all_emojis if emoji.name == emoji_name), None)
            if not emoji and len(all_emojis) < MAX_APP_EMOJIS:
                async with aiofiles.open(bundled_data_path(self) / f"{emoji_name}.png", "rb") as fp:
                    image = await fp.read()
                emoji = await self.bot.create_application_emoji(name=emoji_name, image=image)
            if emoji:
                await self.config.__getattr__("emoji_" + emoji_name).set(str(emoji))

    class MainMenu(discord.ui.View):
        def __init__(self) -> None:
            super().__init__(timeout=None)

        @discord.ui.button(label="Stable", style=discord.ButtonStyle.secondary)
        async def stable_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=discord.Embed(description="Stable menu is under construction."), view=None)

        @discord.ui.button(label="Store", style=discord.ButtonStyle.secondary)
        async def store_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=discord.Embed(description="Store menu is under construction."), view=None)

        @discord.ui.button(label="Race!", style=discord.ButtonStyle.primary)
        async def race_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=discord.Embed(description="Race menu is under construction."), view=None)


    @commands.command()
    async def horser(self, ctx: commands.Context) -> None:
        """Horser main menu."""

        await ctx.send(embed=await embeds.main_menu(self, ctx), view=self.MainMenu())
