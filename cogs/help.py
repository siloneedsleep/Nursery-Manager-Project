from typing import TYPE_CHECKING, Optional

import discord
from discord.ext import commands

from core.helpers import err_emb, q_emb

if TYPE_CHECKING:
    from core.bot import NurseryBot


class HelpCog(commands.Cog):
    def __init__(self, bot: "NurseryBot") -> None:
        self.bot = bot

    @commands.hybrid_command(name="help")
    async def help_command(self, ctx: commands.Context, cmd: Optional[str] = None) -> None:
        if not cmd:
            embed = discord.Embed(
                title="🌈 BẢNG CHỈ DẪN NHÀ TRẺ",
                description="Gõ `/help <tên_lệnh>` để xem chi tiết nhé!",
                color=0xFFB6C1,
            )

            if self.bot.user:
                embed.set_thumbnail(url=self.bot.user.display_avatar.url)

            embed.add_field(
                name="🏫 LỚP HỌC",
                value="`class list`, `class info`, `class setup`, `class teacher`, `class add`, `class remove`, `class reward`, `class delete`",
                inline=False,
            )
            embed.add_field(
                name="🍬 KINH TẾ",
                value="`profile`, `work`, `daily`, `fish`, `dep`, `with`, `leaderboard`",
                inline=False,
            )
            embed.add_field(name="🎮 TRÒ CHƠI", value="`race`, `slot`, `coinflip`", inline=False)
            embed.add_field(name="⚙️ QUẢN TRỊ", value="`noti`, `admin`, `removead`, `edit`, `setlog`, `sync`", inline=False)
            embed.set_footer(text="Yêu cầu bởi {0}".format(ctx.author.display_name))
            await ctx.send(embed=embed)
            return

        if cmd.lower() in ["classroom", "class"]:
            await q_emb(
                ctx,
                "🏫 HỆ THỐNG LỚP HỌC",
                "`class list` - Xem toàn bộ lớp đang có.\n"
                "`class info <tên>` - Xem role, giáo viên và sĩ số của lớp.\n"
                "`class setup <tên> <@role>` - Tạo hoặc cập nhật role cho lớp.\n"
                "`class teacher <tên> [@giáo_viên]` - Gán giáo viên, bỏ trống để gỡ phân công.\n"
                "`class add <tên> <@bé>` - Xếp một bé vào lớp, tự gỡ lớp cũ nếu có.\n"
                "`class remove <tên> <@bé>` - Đưa một bé ra khỏi lớp.\n"
                "`class reward <tên> <số_kẹo>` - Phát kẹo cho cả lớp.\n"
                "`class delete <tên>` - Xóa cấu hình lớp khỏi hệ thống.",
                0x3498DB,
            )
            return

        details = {
            "profile": "Xem hồ sơ thông tin của bé (XP, Kẹo, Tâm trạng...).",
            "daily": "Điểm danh mỗi ngày để nhận 300 🍬.",
            "leaderboard": "Xem Top 10 đại gia kẹo trong server.",
            "dep": "Gửi kẹo vào lợn đất (ngân hàng) cho an toàn.",
            "with": "Đập lợn lấy kẹo ra tiêu xài.",
            "slot": "Chơi quay xèng 🎰. Cược kẹo để kiếm lời.",
            "coinflip": "Đoán đồng xu (Sấp/Ngửa) 🪙.",
            "class list": "Xem danh sách toàn bộ lớp đang được cấu hình trong server.",
            "class info": "Xem thông tin số lượng thành viên của một lớp.",
            "class setup": "Admin: Tạo lớp mới hoặc cập nhật role liên kết cho lớp.",
            "class teacher": "Admin: Gán hoặc gỡ giáo viên chủ nhiệm cho lớp.",
            "class add": "Admin: Kéo bé vào một lớp học. Nếu bé đang ở lớp khác, bot sẽ tự chuyển lớp.",
            "class remove": "Admin: Đưa một bé ra khỏi lớp học.",
            "class reward": "Admin: Phát kẹo cho toàn bộ bé đang ở trong lớp.",
            "class delete": "Admin: Xóa cấu hình lớp khỏi hệ thống quản lý.",
        }
        await q_emb(ctx, "📖 CHI TIẾT: {0}".format(cmd.upper()), details.get(cmd.lower(), "Bạn cứ thử dùng lệnh đó đi, dễ lắm!"), 0x3498DB)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            await err_emb(ctx, "Bé đang mệt hoặc làm quá nhanh! Chờ **{0:.0f} giây** nữa nhé.".format(error.retry_after))
        elif isinstance(error, commands.MissingRequiredArgument):
            await err_emb(ctx, "Bé nhập thiếu thông tin gì rồi, gõ `/help` xem lại nhé!")
        elif isinstance(error, commands.CheckFailure):
            await err_emb(ctx, "Bé không có quyền dùng lệnh này đâu nha!")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print("✅ {0} ĐÃ SẴN SÀNG PHỤC VỤ CÁC BÉ!".format(self.bot.user))


async def setup(bot: "NurseryBot") -> None:
    await bot.add_cog(HelpCog(bot))