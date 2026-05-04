import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI

from CommandManager import register_commands

# Keep existing environment variables, and also load values from .env if present.
load_dotenv(override=False)


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    bot.trpg_llm_client, bot.trpg_llm_model = _create_llm_client()
    bot.trpg_prompt_template = _load_prompt_template()
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


def _create_llm_client() -> tuple[OpenAI, str]:
    provider = (os.getenv("TRPG_API_PROVIDER", "groq") or "groq").strip().lower()
    if provider == "groq":
        api_key = (os.getenv("GROQ_API_KEY") or "").strip().strip('"').strip("'")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY가 비어 있습니다. .env를 확인하세요.")
        model = (os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile") or "llama-3.3-70b-versatile").strip()
        return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1"), model

    api_key = (os.getenv("OPENAI_API_KEY") or "").strip().strip('"').strip("'")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 비어 있습니다. .env를 확인하세요.")
    model = (os.getenv("OPENAI_MODEL", "gpt-4.1-mini") or "gpt-4.1-mini").strip()
    return OpenAI(api_key=api_key), model


def _load_prompt_template() -> str:
    prompt_file = Path(__file__).resolve().parent / "templates" / "trpg-prompt.template.md"
    return prompt_file.read_text(encoding="utf-8")


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
