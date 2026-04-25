import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from CommandManager import register_commands

load_dotenv()


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    register_commands(bot)

    @bot.event
    async def on_ready():
        print(f"{bot.user} 로그인 완료! 모든 명령어는 !로 시작합니다.")

    return bot


def run_bot() -> None:
    token = os.getenv("TOKEN")
    if not token:
        raise RuntimeError("환경변수 TOKEN 이 설정되지 않았습니다.")

    bot = create_bot()
    bot.run(token)


if __name__ == "__main__":
    run_bot()
