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
        self.csv_url = csv_url
        self.token = token

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
            df = pd.read_csv(self.csv_url)
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
