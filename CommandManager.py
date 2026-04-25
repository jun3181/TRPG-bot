from discord.ext import commands

from PlayerDesign import player_design_manager


def register_commands(bot: commands.Bot) -> None:
    @bot.command(name="아이디")
    async def set_id_command(ctx: commands.Context, login_id: str):
        ok, message = player_design_manager.set_login_id(ctx.author.id, login_id)
        await ctx.send(("✅ " if ok else "❌ ") + message)

    @bot.command(name="비번")
    async def set_password_command(ctx: commands.Context, password: str):
        ok, message = player_design_manager.set_password(ctx.author.id, password)
        await ctx.send(("✅ " if ok else "❌ ") + message)

    @bot.command(name="로그인")
    async def login_command(ctx: commands.Context, login_id: str, password: str):
        ok, message = player_design_manager.login(ctx.author.id, login_id, password)
        await ctx.send(("✅ " if ok else "❌ ") + message)

    @bot.command(name="닉네임")
    async def nickname_command(ctx: commands.Context, nickname: str):
        ok, message = player_design_manager.set_nickname(ctx.author.id, nickname)
        await ctx.send(("✅ " if ok else "❌ ") + message)

    @bot.command(name="직업설정")
    async def job_command(ctx: commands.Context, job: str):
        ok, message = player_design_manager.set_job(ctx.author.id, job)
        await ctx.send(("✅ " if ok else "❌ ") + message)

    @bot.command(name="주사위")
    async def dice_command(ctx: commands.Context, action: str):
        if action != "던지기":
            await ctx.send("❌ 사용법: `!주사위 던지기`")
            return

        ok, message, base_stats = player_design_manager.roll_dice(ctx.author.id)
        if not ok:
            await ctx.send(f"❌ {message}")
            return

        await ctx.send(
            "\n".join(
                [
                    f"✅ {message}",
                    f"결과 - 스피드 {base_stats['speed']} / 공격력 {base_stats['attack']} / 방어력 {base_stats['defense']}",
                ]
            )
        )

    @bot.command(name="캐릭터생성")
    async def create_character_command(ctx: commands.Context):
        ok, message, payload = player_design_manager.finalize_character(ctx.author.id)
        if not ok:
            await ctx.send(f"❌ {message}")
            return

        base_stats = payload["stats"]["base"]
        bonus_stats = payload["stats"]["bonus"]
        final_stats = payload["stats"]["final"]

        await ctx.send(
            "\n".join(
                [
                    f"✅ {message}",
                    f"닉네임: {payload['nickname']}",
                    f"직업: {payload['job']}",
                    f"기본 스탯 - 스피드 {base_stats['speed']} / 공격력 {base_stats['attack']} / 방어력 {base_stats['defense']}",
                    f"직업 보정 - 스피드 +{bonus_stats['speed']} / 공격력 +{bonus_stats['attack']} / 방어력 +{bonus_stats['defense']}",
                    f"최종 스탯 - 스피드 {final_stats['speed']} / 공격력 {final_stats['attack']} / 방어력 {final_stats['defense']}",
                ]
            )
        )

    # 사용자가 요청한 형태(`!캐릭터 생성`)도 동작하도록 그룹 명령어를 함께 지원
    @bot.group(name="캐릭터", invoke_without_command=True)
    async def character_group(ctx: commands.Context):
        await ctx.send("사용법: `!캐릭터 생성`, `!캐릭터 조회`")

    @character_group.command(name="생성")
    async def character_create_subcommand(ctx: commands.Context):
        await create_character_command(ctx)

    @character_group.command(name="조회")
    async def character_view_subcommand(ctx: commands.Context):
        ok, message, payload = player_design_manager.get_character(ctx.author.id)
        if not ok:
            await ctx.send(f"❌ {message}")
            return

        final_stats = payload["stats"]["final"]
        await ctx.send(
            "\n".join(
                [
                    f"✅ {message}",
                    f"닉네임: {payload['nickname']}",
                    f"직업: {payload['job']}",
                    f"최종 스탯 - 스피드 {final_stats['speed']} / 공격력 {final_stats['attack']} / 방어력 {final_stats['defense']}",
                ]
            )
        )
