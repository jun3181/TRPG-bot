import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} 로그인 완료!")


@bot.event
async def setup_hook():
    guild = discord.Object(id=GUILD_ID)

    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)

    print(f"{len(synced)}개 슬래시 명령어 동기화 완료!")


@bot.tree.command(name="테스트", description="hello world를 출력합니다.")
async def test_command(interaction: discord.Interaction):
    await interaction.response.send_message("hello world")


bot.run(TOKEN)