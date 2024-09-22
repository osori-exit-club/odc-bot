import asyncio
import os
import sys
import threading

from PyQt5.QtWidgets import QApplication
from dotenv import load_dotenv
from qasync import QEventLoop

from src.ControlPanel import ControlPanel
from src.bot import DiscordBot


class BotClientApp:
    TAG = "BotClientApp"

    def __init__(self, csv_url, token):
        self.bot_thread = None
        self.csv_url = csv_url
        self.bot = None
        self.token = token

        self.panel = ControlPanel(lifecycle=ControlPanel.LifecycleListener(
            on_pause=self.stop_bot,
            on_start=self.run_bot,
            on_end=None,
        ))

    def run_bot(self, done):
        print(f"[{self.TAG}] run_bot")
        if self.bot:
            self.bot.close()
        self.bot = DiscordBot(
            csv_url=self.csv_url,
            on_ready_bot=done,
            token=self.token
        )
        self.bot_thread = threading.Thread(target=self.bot.run_discord_bot)
        self.bot_thread.start()

    def stop_bot(self, done):
        print(f"[{self.TAG}] stop_bot")
        if self.bot:
            self.bot.stop_discord_bot()
            done()
            self.bot = None


async def async_main():
    load_dotenv()

    csv_url = os.getenv("CSV_URL")
    token = os.getenv("DISCORD_TOKEN")

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    client = BotClientApp(csv_url=csv_url, token=token)
    client.panel.show()

    sys.exit(app.exec_())


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
