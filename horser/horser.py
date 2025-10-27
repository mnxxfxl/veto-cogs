from typing import Literal

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.data_manager import bundled_data_path

import aiofiles

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

    @commands.command()
    async def horser(self, ctx: commands.Context) -> None:
        """Horser main menu."""
        await ctx.send("Welcome to Horser! This is where the horse-racing simulation game will be implemented.")
        horse_aqua_emoji = await self.config.emoji_horse_aqua()
        await ctx.send(f"{horse_aqua_emoji} represents the aqua horse!")
