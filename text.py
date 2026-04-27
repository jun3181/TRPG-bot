import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from CommandManager import register_commands

# Keep existing environment variables, and also load values from .env if present.
load_dotenv(override=False)


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    register_commands(bot)

    @bot.event
    async def on_ready():
        print(f"{bot.user} 로그인 완료! 모든 명령어는 !로 시작합니다.")

    return bot


def _resolve_token() -> str | None:
    """Resolve Discord bot token from common environment variable names."""
    for key in ("TOKEN", "DISCORD_TOKEN", "BOT_TOKEN"):
        value = os.getenv(key)
        if value:
            # Handle accidental quotes / whitespace in .env values.
            return value.strip().strip('"').strip("'")
    return None


def run_bot() -> None:
    token = _resolve_token()
    if not token:
        raise RuntimeError(
            "봇 토큰을 찾지 못했습니다. 환경변수 TOKEN / DISCORD_TOKEN / BOT_TOKEN 중 하나를 설정하세요. "
            "(PowerShell 예시: $env:TOKEN='...')"
        )

    bot = create_bot()
    bot.run(token)


if __name__ == "__main__":
    run_bot()
