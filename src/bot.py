import asyncio
import os
from typing import Optional, Callable

import discord
import pandas as pd
from discord.ext import commands
from dotenv import load_dotenv


class DiscordBot:
    TAG = "DiscordBot"
    command_dict = None

    def __init__(self, csv_url, token, on_ready_bot: Optional[Callable] = None):
        self.loop = None
        intents = discord.Intents.default()
        intents.message_content = True

        bot = commands.Bot(command_prefix='!', intents=intents)
        self.bot = bot
        self.token = token

        df = pd.read_csv(csv_url)
        message_description = "help: show description\n".join(
            map(
                lambda x: x if len(x) < 10 else f"{x[:10]}...",
                (df["what"].astype(str) + ": " + df["message"]).values,
            )
        )

        def isSlashCommand(ctx: commands.Context) -> bool:
            return ctx.interaction is not None

        def isActionCommand(ctx: commands.Context) -> bool:
            return ctx.interaction is None

        @bot.hybrid_command(name="odc_message", description=f"예약된 메세지를 전송 합니다. {message_description}")
        async def odc_message(ctx: commands.Context, what: str):
            command_description = message_description

            try:
                df_new = pd.read_csv(os.getenv("CSV_URL"))
                print(f"[{self.TAG}] df_new = {hash(df_new)}")
                command_description = "help: show description\n".join(
                    (df_new["what"].astype(str) + ": " + df_new["name"]).values,
                )

            except Exception:
                print(f"[{self.TAG}] failed to new CSV")

            if what == 'help':
                if isActionCommand(ctx):
                    await ctx.message.delete()
                    await ctx.send(
                        f"{command_description}",
                        delete_after=30,
                    )
                elif isSlashCommand(ctx):
                    await ctx.reply(
                        f"{command_description}",
                        ephemeral=True
                    )
                return

            command_dict = await self.get_command_dict()

            try:
                message_content = command_dict.get(what)

                if message_content is not None:
                    if isActionCommand(ctx):
                        await ctx.message.delete()
                        await ctx.send(f"> {message_content}")
                    elif isSlashCommand(ctx):
                        await ctx.reply(f"> {message_content}")
                else:
                    raise commands.CheckFailure(f"unsupported what: {what}\n{command_description}")

            except Exception as e:
                print(e)
                if isSlashCommand(ctx):
                    await ctx.reply(f"오류가 발생 했습니다: {e}", ephemeral=True)

            print(f'[{self.TAG}] command updated {hash(self.command_dict)} != {hash(command_dict)}')
            if hash(self.command_dict) != hash(command_dict):
                self.command_dict = command_dict
                await sync_dynamic_commands(command_dict)

        @bot.event
        async def on_ready():
            self.command_dict = await self.get_command_dict()
            await sync_dynamic_commands(self.command_dict)

            print(f'[{self.TAG}] Logged in as {bot.user}')

            if on_ready_bot:
                on_ready_bot()

        async def sync_dynamic_commands(command_dict: dict):
            print(f'[{self.TAG}] sync_dynamic_commands {command_dict}')
            for name, message in command_dict.items():
                if name.isdigit():
                    continue
                await add_dynamic_slash_command(name, name, message)

            print(f'[{self.TAG}] tree.sync start')
            try:
                synced = await self.bot.tree.sync()
                print(synced)
                print(f"[{self.TAG}] Synced {len(synced)} commands.")
            except Exception as e:
                print(f"[{self.TAG}] Error syncing commands: {e}")

        async def add_dynamic_slash_command(name, description, message):
            print(f'[{self.TAG}] add_dynamic_slash_command {name} {description}')

            @bot.tree.command(name=name, description=description)
            async def hybrid_command(interaction: discord.Interaction):
                print(f'[{self.TAG}] {name} executed {message}')
                await interaction.response.send_message(f"> {message}")

    async def get_command_dict(self) -> dict[str, str]:
        try:
            print(f"[{self.TAG}] read_csv")
            df = pd.read_csv(os.getenv("CSV_URL"))
        except Exception:
            print(f"[{self.TAG}] failed to new CSV")
            return dict()

        res = dict()
        for index, row in df.iterrows():
            message_content = row['message']
            res[str(row["what"])] = message_content
            res[row["name"].replace(" ", "-")] = message_content
        return res

    def run_discord_bot(self):
        loop = asyncio.new_event_loop()
        self.loop = loop
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.bot.start(self.token))  # 봇 실행
        except asyncio.CancelledError as e:
            print("asyncio.CancelledError")
            print(e)
            pass
        finally:
            loop.run_until_complete(self.bot.close())  # 봇 종료
            loop.close()

    def stop_discord_bot(self):
        self.loop.call_soon_threadsafe(asyncio.create_task, self.bot.close())


def main():
    load_dotenv()
    csv_url = os.getenv("CSV_URL")
    token = os.getenv("DISCORD_TOKEN")

    bot = DiscordBot(csv_url=csv_url, token=token)
    bot.run_discord_bot()


if __name__ == "__main__":
    main()
