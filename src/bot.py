import asyncio
import os
from typing import Optional, Callable

import discord
import pandas as pd
from discord.ext import commands
from dotenv import load_dotenv


class DiscordBot:
    TAG = "DiscordBot"

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
                print(f"[${self.TAG}] {df_new}")
                df_local = df_new
                command_description = "help: show description\n".join(
                    (df_new["what"].astype(str) + ": " + df_new["name"]).values,
                )

            except Exception:
                df_local = df
                print(f"[${self.TAG}] failed to new CSV")

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

            try:
                df_target = df_local[df_local["what"].astype(str) == what]

                if len(df_target) > 0:
                    message_content = df_target["message"].values[0]
                    print(f"[${self.TAG}] > {what}\n{message_content}")
                    if isActionCommand(ctx):
                        await ctx.message.delete()
                        await ctx.send(f"> {message_content}")
                    elif isSlashCommand(ctx):
                        await ctx.reply(
                            content=df_target["name"].values[0],
                            ephemeral=True
                        )
                        await ctx.reply(f"> {message_content}")
                else:
                    raise commands.CheckFailure(f"unsupported what: {what}\n{command_description}")

            except Exception as e:
                if isSlashCommand(ctx):
                    await ctx.reply(f"오류가 발생 했습니다: {e}", ephemeral=True)

        @bot.event
        async def on_ready():
            await bot.tree.sync()
            print(f'[{self.TAG}] Logged in as {bot.user}')
            if on_ready_bot:
                on_ready_bot()

    def run_discord_bot(self):
        loop = asyncio.new_event_loop()
        self.loop = loop
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.bot.start(self.token))  # 봇 실행
        except asyncio.CancelledError:
            print("asyncio.CancelledError")
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
