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
        self.csv_url = csv_url
        self.token = token
        self.command_dict = self.get_command_dict()

        @bot.event
        async def on_ready():
            await sync_dynamic_commands()

            print(f'[{self.TAG}] Logged in as {bot.user}')

            if on_ready_bot:
                on_ready_bot()

        async def sync_dynamic_commands():
            for name, (message, description) in self.command_dict.items():
                if name.isdigit():
                    continue
                update_dynamic_slash_command(name, description, message)

            print(f'[{self.TAG}] tree.sync start')
            try:
                synced = await self.bot.tree.sync()
                print(f"[{self.TAG}] Synced {len(synced)} commands. | ${synced}")
            except Exception as e:
                print(f"[{self.TAG}] Error syncing commands: {e}")

        def update_dynamic_slash_command(name, description, message):
            bot.tree.remove_command(name)

            @bot.tree.command(name=name, description=description, )
            async def hybrid_command(interaction: discord.Interaction):
                command_dict = self.get_command_dict()
                (message_dict, _) = command_dict.get(name)
                message_content = message_dict if message_dict is not None else message

                if message_content is not None:
                    print(f'[{self.TAG}] {name} executed {message_content}')
                    try:
                        await interaction.channel.send(f"> {message_content}")
                        await interaction.response.send_message(
                            "메세지 전송 성공",
                            ephemeral=True
                        )

                    except Exception as e:
                        print(e)
                        await interaction.response.send_message(
                            "메세지 전송 실패",
                            ephemeral=True
                        )
                else:
                    await interaction.response.send_message(
                        f"> failed to fine {name} from csv file",
                        ephemeral=True
                    )

        @bot.tree.command(
            name="멘토링-타이머",
            description="멘토링을 시작하고, 종료 10분 전·종료 알림(기본 60분)"
        )
        async def mentoring_start(
                interaction: discord.Interaction,
                duration: Optional[int] = 60  # 디폴트 60분
        ):
            # 시간·분 단위 계산
            hours, mins = divmod(duration, 60)
            if hours > 0 and mins > 0:
                duration_str = f"{hours}시간 {mins}분"
            elif hours > 0 and mins == 0:
                duration_str = f"{hours}시간"
            else:
                duration_str = f"{mins}분"

            # 1️⃣ 즉시 시작 메시지
            await interaction.response.send_message(
                f"멘토링 시작! 총 **{duration_str}** 동안 진행됩니다."
            )
            # 이 호출 이후에 원본 메시지를 가져올 수 있습니다
            start_msg = await interaction.original_response()

            async def schedule_reminders(channel: discord.TextChannel, total_min: int, ref_msg: discord.Message):
                if duration > 10:
                    # (총 시간 – 10분) 후 10분 전 알림
                    await asyncio.sleep((total_min - 10) * 60)
                    await channel.send(
                        "⏰ 종료 10분 전입니다.",
                        reference=ref_msg,
                        allowed_mentions=discord.AllowedMentions(replied_user=False)
                    )
                    # 추가로 10분(=600초) 대기 후 종료 알림
                    await asyncio.sleep(10 * 60)
                    await channel.send(
                        "🏁 멘토링이 종료되었습니다.",
                        reference=ref_msg,
                        allowed_mentions=discord.AllowedMentions(replied_user=False)
                    )
                else:
                    half_time = int(total_min / 2)
                    # 총 시간 10분 이하일 경우는 절반 시간 사용
                    await asyncio.sleep(half_time * 60)
                    await channel.send(
                        "⏰ 종료 {}분 전입니다.".format(half_time),
                        reference=ref_msg,
                        allowed_mentions=discord.AllowedMentions(replied_user=False)
                    )
                    # 추가로 남은 대기 후 종료 알림
                    await asyncio.sleep((total_min - half_time) * 60)
                    await channel.send(
                        "🏁 멘토링이 종료되었습니다.",
                        reference=ref_msg,
                        allowed_mentions=discord.AllowedMentions(replied_user=False)
                    )


            # 백그라운드에서 스케줄링
            bot.loop.create_task(schedule_reminders(interaction.channel, duration, start_msg))

    def get_command_dict(self) -> dict[str, (str, str)]:
        try:
            print(f"[{self.TAG}] read_csv")
            df = pd.read_csv(self.csv_url)
        except Exception:
            print(f"[{self.TAG}] failed to new CSV")
            return dict()

        res = dict()
        for index, row in df.iterrows():
            description = row['description']
            message_content = row['message']
            res[row["name"].replace(" ", "-")] = (message_content, description)
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
