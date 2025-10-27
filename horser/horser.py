from typing import Literal

import discord
from discord.ext import tasks

from redbot.core import bank, commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.data_manager import bundled_data_path, cog_data_path
from redbot.core.utils.menus import menu
from redbot.core.utils.chat_formatting import humanize_number

import aiofiles
import apsw

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]

MAX_APP_EMOJIS = 2000

# Energy regen constants
TICK_SECONDS = 300  # 5 minutes
REGEN_PER_TICK = 1  # 1 energy per tick

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

        # SQLite DB setup
        self._connection = apsw.Connection(str(cog_data_path(self) / "horser.db"))
        self.cursor = self._connection.cursor()
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS horses ('
            'guild_id INTEGER,'
            'user_id INTEGER,'
            'horse_id INTEGER PRIMARY KEY AUTOINCREMENT,'

            'horse_name TEXT,'
            'horse_color TEXT NOT NULL,'

            'speed INTEGER NOT NULL DEFAULT 1,'
            'power INTEGER NOT NULL DEFAULT 1,'
            'stamina INTEGER NOT NULL DEFAULT 1,'
            'guts INTEGER NOT NULL DEFAULT 1,'
            'wit INTEGER NOT NULL DEFAULT 1,'

            'energy INTEGER NOT NULL DEFAULT 10,'
            'max_energy INTEGER NOT NULL DEFAULT 10,'
            "last_energy_regen_ts INTEGER NOT NULL DEFAULT (strftime('%s','now')),"

            'races_run INTEGER NOT NULL DEFAULT 0,'
            'races_won INTEGER NOT NULL DEFAULT 0'
            ');'
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

    class MainMenu(discord.ui.View):
        def __init__(self, horser, ctx: commands.Context) -> None:
            super().__init__(timeout=None)
            self.horser = horser
            self.ctx = ctx
           

        @discord.ui.button(label="Stable", style=discord.ButtonStyle.secondary)
        async def stable_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=await self.horser.get_embed(self.ctx, "stable_menu"), view=self.horser.StableMenu(self.horser, self.ctx))

        @discord.ui.button(label="Store", style=discord.ButtonStyle.secondary)
        async def store_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=await self.horser.get_embed(self.ctx, "store_menu"), view=self.horser.StoreMenu(self.horser, self.ctx))

        @discord.ui.button(label="Race!", style=discord.ButtonStyle.primary)
        async def race_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=await self.horser.get_embed(self.ctx, "race_menu"), view=self.horser.RaceMenu(self.horser, self.ctx))

    class StableMenu(discord.ui.View):
        def __init__(self, horser, ctx: commands.Context) -> None:
            super().__init__(timeout=None)
            self.horser = horser
            self.ctx = ctx

        @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
        async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=await self.horser.get_embed(self.ctx, "main_menu"), view=self.horser.MainMenu(self.horser, self.ctx))

    class StoreMenu(discord.ui.View):
        def __init__(self, horser, ctx: commands.Context) -> None:
            super().__init__(timeout=None)
            self.horser = horser
            self.ctx = ctx

        @discord.ui.button(label="Buy Horse", style=discord.ButtonStyle.primary)
        async def buy_horse_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=await self.horser.get_embed(self.ctx, "store_menu_buy_horse"), view=self.horser.StoreMenuBuyHorse(self.horser, self.ctx))

        @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
        async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=await self.horser.get_embed(self.ctx, "main_menu"), view=self.horser.MainMenu(self.horser, self.ctx))

    class StoreMenuBuyHorse(discord.ui.View):
        def __init__(self, horser, ctx: commands.Context) -> None:
            super().__init__(timeout=None)
            self.horser = horser
            self.ctx = ctx

        @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
        async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=await self.horser.get_embed(self.ctx, "store"), view=self.horser.StoreMenu(self.horser, self.ctx))

    class RaceMenu(discord.ui.View):
        def __init__(self, horser, ctx: commands.Context) -> None:
            super().__init__(timeout=None)
            self.horser = horser
            self.ctx = ctx

        @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
        async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            await interaction.response.edit_message(embed=await self.horser.get_embed(self.ctx, "main_menu"), view=self.horser.MainMenu(self.horser, self.ctx))

    @commands.command()
    async def horser(self, ctx: commands.Context, cmd: str | None = None, *args) -> None:
        """Horser main menu."""

        if not cmd:
            await ctx.send(embed=await self.get_embed(ctx, "main_menu"), view=self.MainMenu(self, ctx))
        elif cmd.lower() == "buyhorse":
            # Buy horse command
            if len(args) < 2:
                await ctx.send("Usage: !horser buy_horse [color] [name]")
                return

            color = args[0].lower()
            name = " ".join(arg.capitalize() for arg in args[1:])

            # Check if color is valid
            valid_colors = [
                "aqua", "ash", "black", "blue", "brown", "chocolate", "cream",
                "diamond", "green", "grey", "lime", "orange", "pink", "purple",
                "red", "sky", "soot", "white", "yellow", "zombie"
            ]
            if color not in valid_colors:
                await ctx.send(f"Invalid color. Valid colors are: {', '.join(valid_colors)}")
                return

            # Check if user has enough balance
            currency_name = await bank.get_currency_name(ctx.guild)
            horse_cost = 25000
            user_balance = await bank.get_balance(ctx.author)
            if user_balance < horse_cost:
                await ctx.send(f"You do not have enough {currency_name} to buy a horse. You need {humanize_number(horse_cost)} {currency_name}.")
                return

            # Deduct cost and add horse to database
            await bank.withdraw_credits(ctx.author, horse_cost)
            self.cursor.execute(
                "INSERT INTO horses (guild_id, user_id, horse_name, horse_color) VALUES (?, ?, ?, ?);",
                (ctx.guild.id, ctx.author.id, name, color)
            )
            await ctx.send(f"You have successfully bought a {color} horse named '{name}' for {humanize_number(horse_cost)} {currency_name}!")

    async def get_embed(self, ctx: commands.Context, code: str) -> discord.Embed:
        currency_name = await bank.get_currency_name(ctx.guild)

        embed = discord.Embed()

        if code == "main_menu":
            embed.color = discord.Color.dark_magenta()
            embed.title = "Horser"

            horse_count = list(self.cursor.execute(
                "SELECT COUNT(*) FROM horses WHERE guild_id = ? AND user_id = ?;",
                (ctx.guild.id, ctx.author.id),
            ))[0][0]

            embed.add_field(name="", value=
f"""Welcome to Horser! The horse racing simulation game.

{ctx.author.mention}, you have {horse_count} horses in your stable.""")

        elif code == "stable_menu":
            embed.color = discord.Color.dark_gold()
            embed.title = "Stable"

            horse_count = list(self.cursor.execute(
                "SELECT COUNT(*) FROM horses WHERE guild_id = ? AND user_id = ?;",
                (ctx.guild.id, ctx.author.id),
            ))[0][0]

            embed.add_field(name="", value=
            f"You currently have {horse_count} horses in your stable."
            "*To manage your horse, type !horser manage [horse name] or use the select menu below.*"
            )
            
            horse_idx = 1
            for horse in self.cursor.execute(
                "SELECT horse_name, horse_color, energy, max_energy FROM horses WHERE guild_id = ? AND user_id = ?;",
                (ctx.guild.id, ctx.author.id),
            ):
                # add embed which shows the horse emoji with the corresponding color
                emoji = await self.config.__getattr__(f'emoji_horse_{horse[1]}')()
                embed.add_field(name=f"{horse_idx}. {horse[0]}", value=emoji, inline=False)
                embed.add_field(name="", value=f"Energy: {horse[2]}/{horse[3]}", inline=False)
                horse_idx += 1

        elif code == "store_menu":
            embed.color = discord.Color.dark_green()
            embed.title = "Store"

            embed.add_field(name="", value= 
f""" Here you can buy horses and training equipment.

Your current balance is {humanize_number(await bank.get_balance(ctx.author))} {currency_name}.

Store currently under construction.""")
            
        elif code == "store_menu_buy_horse":
            embed.color = discord.Color.dark_green()
            embed.title = "Buy Horse"

            embed.add_field(name="", value= 
f""" Your current balance is {humanize_number(await bank.get_balance(ctx.author))} {currency_name}.

To buy a horse, type !horser buyHorse [color] [name]. A horse costs {25000} {currency_name}.

There are currently 20 colors available. Hover over each horse emoji below to see its color name.

{await self.config.emoji_horse_aqua()} {await self.config.emoji_horse_ash()} {await self.config.emoji_horse_black()} {await self.config.emoji_horse_blue()}
{await self.config.emoji_horse_brown()} {await self.config.emoji_horse_chocolate()} {await self.config.emoji_horse_cream()} {await self.config.emoji_horse_diamond()} 
{await self.config.emoji_horse_green()} {await self.config.emoji_horse_grey()} {await self.config.emoji_horse_lime()} {await self.config.emoji_horse_orange()} 
{await self.config.emoji_horse_pink()} {await self.config.emoji_horse_purple()} {await self.config.emoji_horse_red()} {await self.config.emoji_horse_sky()}
{await self.config.emoji_horse_soot()} {await self.config.emoji_horse_white()} {await self.config.emoji_horse_yellow()} {await self.config.emoji_horse_zombie()}""")

        elif code == "race_menu":
            embed.color = discord.Color.green()
            embed.title = "Race!"

            embed.add_field(name="", value=
f""" Race your horses for cash!

Race currently under construction.""")

        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        return embed
    
    ### Energy regeneration logic ###
    def update_energy(self) -> None:
        self.cursor.execute(
            """
            UPDATE horses
            SET
                energy = MIN(
                max_energy,
                energy + CAST((strftime('%s','now') - last_regen_ts) / ? AS INTEGER) * ?
                ),
                last_regen_ts = last_regen_ts + (
                CAST((strftime('%s','now') - last_regen_ts) / ? AS INTEGER) * ?
                )
            WHERE energy < max_energy;
            """,
            (TICK_SECONDS, REGEN_PER_TICK, TICK_SECONDS, TICK_SECONDS),
        )

    @tasks.loop(seconds=60)
    async def energy_catchup(self):
        # Downtime-proof: does nothing unless a full 5-min tick elapsed
        try:
            self.bring_energy_current(None)
        except Exception as e:
            print(f"[energy_catchup] DB error: {e}")

    @energy_catchup.before_loop
    async def _before_loop(self):
        await self.bot.wait_until_ready()
    ### End energy regeneration logic ###