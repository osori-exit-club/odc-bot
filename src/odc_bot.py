import os

import discord
import pandas as pd
from discord.ext import commands
from dotenv import load_dotenv


def main():
    load_dotenv()

    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix='!', intents=intents)

    df = pd.read_csv(os.getenv("CSV_URL"))
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
            print(df_new)
            df_local = df_new
            command_description = "help: show description\n".join(
                (df_new["what"].astype(str) + ": " + df_new["name"]).values,
            )

        except Exception:
            df_local = df
            print("failed to new CSV")

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
                print(f"> {what}\n{message_content}")
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
        print(f'Logged in as {bot.user}')

    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
