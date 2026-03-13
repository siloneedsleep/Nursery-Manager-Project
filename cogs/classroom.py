from typing import TYPE_CHECKING, Optional

import discord
from discord.ext import commands

from core.helpers import (
    err_emb,
    format_teacher,
    get_all_classrooms,
    get_classroom_record,
    is_admin_or_owner,
    normalize_class_name,
    q_emb,
    resolve_classroom,
    send_log,
)

if TYPE_CHECKING:
    from core.bot import NurseryBot


class ClassroomCog(commands.Cog):
    def __init__(self, bot: "NurseryBot") -> None:
        self.bot = bot

    async def _ensure_guild(self, ctx: commands.Context) -> bool:
        if ctx.guild is not None:
            return True

        await err_emb(ctx, "Lệnh này chỉ dùng trong server nhé!")
        return False

    @commands.group(name="classroom", aliases=["class"], invoke_without_command=True)
    async def classroom(self, ctx: commands.Context) -> None:
        help_command = self.bot.get_command("help")

        if help_command is None:
            await err_emb(ctx, "Không tìm thấy lệnh help để hướng dẫn nhé!")
            return

        await ctx.invoke(help_command, cmd="classroom")

    @classroom.command(name="setup")
    @is_admin_or_owner()
    async def class_setup(self, ctx: commands.Context, name: str, role: discord.Role) -> None:
        if not await self._ensure_guild(ctx):
            return

        class_name = normalize_class_name(name)

        if not class_name:
            await err_emb(ctx, "Tên lớp không được để trống!")
            return

        cursor = self.bot.conn.cursor()
        existing = get_classroom_record(self.bot, class_name)

        if existing:
            cursor.execute("UPDATE classrooms SET role_id = ? WHERE class_name = ?", (role.id, class_name))
            message = "Đã cập nhật lớp **{0}** sang Role {1}!".format(class_name.upper(), role.mention)
        else:
            cursor.execute(
                "INSERT INTO classrooms (class_name, role_id, teacher_id) VALUES (?, ?, ?)",
                (class_name, role.id, None),
            )
            message = "Lớp **{0}** đã được gắn với Role {1}!".format(class_name.upper(), role.mention)

        self.bot.conn.commit()

        await q_emb(ctx, "✅ CẤU HÌNH LỚP THÀNH CÔNG", message, 0x2ECC71)
        await send_log(
            ctx,
            "CẬP NHẬT LỚP HỌC",
            "**Lớp:** {0}\n**Role:** {1}".format(class_name.upper(), role.mention),
            0x2ECC71,
        )

    @classroom.command(name="list", aliases=["all", "ls"])
    async def class_list(self, ctx: commands.Context) -> None:
        if not await self._ensure_guild(ctx):
            return

        classrooms = get_all_classrooms(self.bot)

        if not classrooms:
            await err_emb(ctx, "Hiện chưa có lớp học nào được tạo!")
            return

        lines = []

        for class_name, role_id, teacher_id in classrooms:
            role = ctx.guild.get_role(role_id)
            role_text = role.mention if role else "Role đã bị xóa"
            class_size = len(role.members) if role else 0
            teacher_text = format_teacher(ctx.guild, teacher_id)
            lines.append(
                "**{0}** | {1} | GV: {2} | Sĩ số: **{3}** bé".format(
                    class_name.upper(),
                    role_text,
                    teacher_text,
                    class_size,
                )
            )

        await q_emb(ctx, "📚 DANH SÁCH LỚP HỌC", "\n".join(lines), 0x3498DB)

    @classroom.command(name="info")
    async def class_info(self, ctx: commands.Context, name: str) -> None:
        resolved = await resolve_classroom(ctx, name)

        if not resolved:
            return

        class_name, role, teacher_id = resolved
        members_preview = ", ".join(member.mention for member in role.members[:10]) or "Chưa có bé nào trong lớp."

        if len(role.members) > 10:
            members_preview += "\n... và thêm **{0}** bé nữa.".format(len(role.members) - 10)

        embed = discord.Embed(title="🏫 THÔNG TIN LỚP: {0}".format(class_name.upper()), color=0x3498DB)
        embed.add_field(name="🏷️ Role Lớp", value=role.mention, inline=True)
        embed.add_field(name="👩‍🏫 Giáo viên", value=format_teacher(ctx.guild, teacher_id), inline=True)
        embed.add_field(name="👥 Sĩ số", value="**{0}** bé".format(len(role.members)), inline=True)
        embed.add_field(name="🧸 Danh sách nhanh", value=members_preview, inline=False)

        if ctx.guild and ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        await ctx.send(embed=embed)

    @classroom.command(name="teacher")
    @is_admin_or_owner()
    async def class_teacher(
        self,
        ctx: commands.Context,
        name: str,
        member: Optional[discord.Member] = None,
    ) -> None:
        record = get_classroom_record(self.bot, name)

        if not record:
            await err_emb(ctx, "Lớp này chưa được tạo!")
            return

        class_name, _, _ = record

        if member and member.bot:
            await err_emb(ctx, "Không thể phân công bot làm giáo viên lớp nhé!")
            return

        cursor = self.bot.conn.cursor()

        if member is None:
            cursor.execute("UPDATE classrooms SET teacher_id = NULL WHERE class_name = ?", (class_name,))
            self.bot.conn.commit()

            await q_emb(
                ctx,
                "🧹 GỠ GIÁO VIÊN CHỦ NHIỆM",
                "Đã gỡ phân công giáo viên khỏi lớp **{0}**.".format(class_name.upper()),
                0xE67E22,
            )
            await send_log(ctx, "GỠ GIÁO VIÊN CHỦ NHIỆM", "**Lớp:** {0}".format(class_name.upper()), 0xE67E22)
            return

        cursor.execute("UPDATE classrooms SET teacher_id = ? WHERE class_name = ?", (member.id, class_name))
        self.bot.conn.commit()

        await q_emb(
            ctx,
            "👩‍🏫 PHÂN CÔNG GIÁO VIÊN",
            "Đã phân công {0} phụ trách lớp **{1}**.".format(member.mention, class_name.upper()),
            0x1ABC9C,
        )
        await send_log(
            ctx,
            "PHÂN CÔNG GIÁO VIÊN",
            "**Lớp:** {0}\n**Giáo viên:** {1}".format(class_name.upper(), member.mention),
            0x1ABC9C,
        )

    @classroom.command(name="add")
    @is_admin_or_owner()
    async def class_add(self, ctx: commands.Context, name: str, member: discord.Member) -> None:
        resolved = await resolve_classroom(ctx, name)

        if not resolved:
            return

        class_name, role, _ = resolved
        other_class_roles = []

        for other_name, role_id, _ in get_all_classrooms(self.bot):
            if other_name == class_name:
                continue

            other_role = ctx.guild.get_role(role_id)

            if other_role and other_role in member.roles:
                other_class_roles.append(other_role)

        if role in member.roles and not other_class_roles:
            await err_emb(ctx, "{0} đã ở sẵn lớp **{1}** rồi!".format(member.mention, class_name.upper()))
            return

        try:
            if other_class_roles:
                await member.remove_roles(*other_class_roles, reason="Chuyển lớp sang {0}".format(class_name.upper()))

            if role not in member.roles:
                await member.add_roles(role, reason="Xếp vào lớp {0}".format(class_name.upper()))

            moved_from = ""

            if other_class_roles:
                moved_from = "\nĐã chuyển bé khỏi: {0}".format(", ".join(role_item.mention for role_item in other_class_roles))

            await q_emb(
                ctx,
                "🎒 NHẬP HỌC",
                "Đã bế bé {0} vào lớp **{1}** ({2})!{3}".format(
                    member.mention,
                    class_name.upper(),
                    role.mention,
                    moved_from,
                ),
                0x9B59B6,
            )
            await send_log(
                ctx,
                "XẾP LỚP HỌC SINH",
                "**Lớp mới:** {0}\n**Học sinh:** {1}".format(class_name.upper(), member.mention),
                0x9B59B6,
            )
        except discord.Forbidden:
            await err_emb(ctx, "Bot không có quyền chỉnh Role này! Hãy kéo Role của bot lên cao hơn Role lớp nhé.")

    @classroom.command(name="remove", aliases=["kick"])
    @is_admin_or_owner()
    async def class_remove(self, ctx: commands.Context, name: str, member: discord.Member) -> None:
        resolved = await resolve_classroom(ctx, name)

        if not resolved:
            return

        class_name, role, _ = resolved

        if role not in member.roles:
            await err_emb(ctx, "{0} hiện không ở lớp **{1}**.".format(member.mention, class_name.upper()))
            return

        try:
            await member.remove_roles(role, reason="Rời lớp {0}".format(class_name.upper()))

            await q_emb(
                ctx,
                "🧸 RỜI LỚP",
                "Đã đưa bé {0} ra khỏi lớp **{1}**.".format(member.mention, class_name.upper()),
                0xE67E22,
            )
            await send_log(
                ctx,
                "XÓA HỌC SINH KHỎI LỚP",
                "**Lớp:** {0}\n**Học sinh:** {1}".format(class_name.upper(), member.mention),
                0xE67E22,
            )
        except discord.Forbidden:
            await err_emb(ctx, "Bot không có quyền gỡ Role này! Hãy kiểm tra thứ tự Role của bot nhé.")

    @classroom.command(name="reward")
    @is_admin_or_owner()
    async def class_reward(self, ctx: commands.Context, name: str, amount: int) -> None:
        if amount <= 0:
            await err_emb(ctx, "Số kẹo thưởng phải lớn hơn 0 nhé!")
            return

        resolved = await resolve_classroom(ctx, name)

        if not resolved:
            return

        class_name, role, _ = resolved

        if not role.members:
            await err_emb(ctx, "Lớp này chưa có bé nào để phát thưởng!")
            return

        cursor = self.bot.conn.cursor()

        for member in role.members:
            self.bot.get_user_profile(member.id)
            cursor.execute("UPDATE users SET candies = candies + ? WHERE user_id = ?", (amount, member.id))

        self.bot.conn.commit()
        total_amount = amount * len(role.members)

        await q_emb(
            ctx,
            "🎁 THƯỞNG LỚP",
            "Bảo mẫu đã phát **{0} 🍬** cho mỗi bé ở lớp {1}!\nTổng phát: **{2:,} 🍬**".format(
                amount,
                role.mention,
                total_amount,
            ),
            0xF1C40F,
        )
        await send_log(
            ctx,
            "THƯỞNG THEO LỚP",
            "**Lớp:** {0}\n**Số bé:** {1}\n**Thưởng mỗi bé:** {2:,} 🍬".format(
                class_name.upper(),
                len(role.members),
                amount,
            ),
            0xF1C40F,
        )

    @classroom.command(name="delete", aliases=["del", "removeclass"])
    @is_admin_or_owner()
    async def class_delete(self, ctx: commands.Context, name: str) -> None:
        record = get_classroom_record(self.bot, name)

        if not record:
            await err_emb(ctx, "Lớp này chưa được tạo!")
            return

        class_name, role_id, _ = record
        role = ctx.guild.get_role(role_id) if ctx.guild else None
        cursor = self.bot.conn.cursor()
        cursor.execute("DELETE FROM classrooms WHERE class_name = ?", (class_name,))
        self.bot.conn.commit()

        role_text = role.mention if role else "`ID {0}`".format(role_id)

        await q_emb(
            ctx,
            "🗑️ XÓA CẤU HÌNH LỚP",
            "Đã xóa lớp **{0}** khỏi hệ thống quản lý.\nRole liên kết trước đó: {1}\n*Lưu ý: Bot không xóa Discord role đang có.*".format(
                class_name.upper(),
                role_text,
            ),
            0xFF4757,
        )
        await send_log(
            ctx,
            "XÓA CẤU HÌNH LỚP",
            "**Lớp:** {0}\n**Role cũ:** {1}".format(class_name.upper(), role_text),
            0xFF4757,
        )


async def setup(bot: "NurseryBot") -> None:
    await bot.add_cog(ClassroomCog(bot))