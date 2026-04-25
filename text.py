import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from CommandManager import register_commands

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
register_commands(bot)


@bot.event
async def on_ready():
    print(f"{bot.user} 로그인 완료! 모든 명령어는 !로 시작합니다.")


bot.run(TOKEN)
