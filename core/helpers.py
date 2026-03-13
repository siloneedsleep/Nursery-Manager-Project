from typing import TYPE_CHECKING, List, Optional, Tuple, cast

import discord
from discord.ext import commands

from config.settings import settings

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from core.bot import NurseryBot


ClassroomRecord = Tuple[str, int, Optional[int]]


def _nursery_bot(bot: commands.Bot) -> "NurseryBot":
    return cast("NurseryBot", bot)


async def q_emb(
    ctx: "Context",
    title: str,
    desc: str,
    color: int = 0xFFB6C1,
    thumbnail: Optional[str] = None,
):
    embed = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(
        text="📌 Yêu cầu bởi {0}".format(ctx.author.display_name),
        icon_url=ctx.author.display_avatar.url,
    )

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    return await ctx.send(embed=embed)


async def err_emb(ctx: "Context", desc: str):
    embed = discord.Embed(title="⚠️ Ôi hỏng!", description="**{0}**".format(desc), color=0xFF4757)
    return await ctx.send(embed=embed, delete_after=15)


async def send_log(ctx: "Context", action_title: str, details: str, color: int = 0x34495E) -> None:
    bot = _nursery_bot(ctx.bot)
    cursor = bot.conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = 'log_channel'")
    result = cursor.fetchone()

    if not result:
        return

    log_channel = bot.get_channel(result[0])

    if not log_channel:
        return

    embed = discord.Embed(
        title="📜 LOG: {0}".format(action_title),
        description=details,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await log_channel.send(embed=embed)


def is_admin_or_owner():
    async def predicate(ctx: "Context") -> bool:
        if ctx.author.id == settings.owner_id:
            return True

        bot = _nursery_bot(ctx.bot)
        cursor = bot.conn.cursor()
        cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (ctx.author.id,))
        return cursor.fetchone() is not None

    return commands.check(predicate)


def normalize_class_name(name: str) -> str:
    return name.strip().lower()


def get_classroom_record(bot: "NurseryBot", name: str) -> Optional[ClassroomRecord]:
    cursor = bot.conn.cursor()
    cursor.execute(
        "SELECT class_name, role_id, teacher_id FROM classrooms WHERE class_name = ?",
        (normalize_class_name(name),),
    )
    return cursor.fetchone()


def get_all_classrooms(bot: "NurseryBot") -> List[ClassroomRecord]:
    cursor = bot.conn.cursor()
    cursor.execute("SELECT class_name, role_id, teacher_id FROM classrooms ORDER BY class_name ASC")
    return cursor.fetchall()


def format_teacher(guild: discord.Guild, teacher_id: Optional[int]) -> str:
    if not teacher_id:
        return "Chưa phân công"

    teacher = guild.get_member(teacher_id)

    if teacher:
        return teacher.mention

    return "`ID {0}` (không còn trong server)".format(teacher_id)


async def resolve_classroom(ctx: "Context", name: str):
    if ctx.guild is None:
        await err_emb(ctx, "Lệnh này chỉ dùng trong server nhé!")
        return None

    bot = _nursery_bot(ctx.bot)
    record = get_classroom_record(bot, name)

    if not record:
        await err_emb(ctx, "Lớp này chưa được tạo!")
        return None

    class_name, role_id, teacher_id = record
    role = ctx.guild.get_role(role_id)

    if not role:
        await err_emb(ctx, "Role của lớp này không còn tồn tại. Hãy dùng `class setup` để gắn lại role nhé!")
        return None

    return class_name, role, teacher_id