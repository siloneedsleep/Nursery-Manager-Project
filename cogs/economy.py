import datetime
import random
from typing import TYPE_CHECKING, Optional

import discord
from discord.ext import commands

from core.constants import FISH_DATA
from core.helpers import err_emb, q_emb

if TYPE_CHECKING:
    from core.bot import NurseryBot


class EconomyCog(commands.Cog):
    def __init__(self, bot: "NurseryBot") -> None:
        self.bot = bot

    @commands.hybrid_command(name="profile", aliases=["pf"])
    async def profile(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        member = member or ctx.author
        xp, level, candies, bank, _, mood, title = self.bot.get_user_profile(member.id)

        needed_xp = level * 500
        progress = int((xp / needed_xp) * 10)
        bar = "▰" * progress + "▱" * (10 - progress)

        embed = discord.Embed(
            title="📛 HỒ SƠ: {0}".format(member.display_name),
            description="✨ **Danh hiệu:** `{0}`".format(title),
            color=0xFFB6C1,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="📊 Cấp độ", value="**Cấp {0}**\n{1} ({2}/{3} XP)".format(level, bar, xp, needed_xp), inline=False)
        embed.add_field(name="🍬 Túi Kẹo", value="**{0:,}** 🍬".format(candies), inline=True)
        embed.add_field(name="🏦 Ngân Hàng", value="**{0:,}** 🍬".format(bank), inline=True)
        embed.add_field(name="🎭 Tâm Trạng", value="**{0}/100** 💖".format(mood), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="daily")
    async def daily(self, ctx: commands.Context) -> None:
        user_id = ctx.author.id
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        cursor = self.bot.conn.cursor()
        cursor.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()

        if result and result[0] == today:
            await err_emb(ctx, "Hôm nay bé đã nhận kẹo rồi, mai quay lại nhé!")
            return

        self.bot.get_user_profile(user_id)
        cursor.execute("UPDATE users SET last_daily = ?, candies = candies + 300 WHERE user_id = ?", (today, user_id))
        self.bot.conn.commit()
        await q_emb(ctx, "📅 ĐIỂM DANH HÀNG NGÀY", "Bé ngoan lắm! Thưởng cho bé **300 🍬** nhé!", 0x2ECC71)

    @commands.hybrid_command(name="dep")
    async def dep(self, ctx: commands.Context, amount: int) -> None:
        _, _, candies, _, _, _, _ = self.bot.get_user_profile(ctx.author.id)

        if amount > candies or amount <= 0:
            await err_emb(ctx, "Số kẹo gửi không hợp lệ hoặc bé không có đủ kẹo!")
            return

        self.bot.update_user_profile(ctx.author.id, candy=-amount, bank=amount)
        await q_emb(ctx, "🏦 GỬI NGÂN HÀNG", "Bé đã cất an toàn **{0:,} 🍬** vào lợn đất!".format(amount), 0x3498DB)

    @commands.hybrid_command(name="with")
    async def withdraw(self, ctx: commands.Context, amount: int) -> None:
        _, _, _, bank, _, _, _ = self.bot.get_user_profile(ctx.author.id)

        if amount > bank or amount <= 0:
            await err_emb(ctx, "Số kẹo rút không hợp lệ hoặc lợn đất không đủ kẹo!")
            return

        self.bot.update_user_profile(ctx.author.id, candy=amount, bank=-amount)
        await q_emb(ctx, "🏦 RÚT NGÂN HÀNG", "Bé đã đập lợn lấy ra **{0:,} 🍬** để xài!".format(amount), 0xE67E22)

    @commands.hybrid_command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx: commands.Context) -> None:
        cursor = self.bot.conn.cursor()
        cursor.execute("SELECT user_id, (candies + bank) AS total FROM users ORDER BY total DESC LIMIT 10")
        top_users = cursor.fetchall()

        description = ""

        for index, (user_id, total) in enumerate(top_users):
            user = ctx.guild.get_member(user_id) if ctx.guild else None

            if user is None:
                user = self.bot.get_user(user_id)

            name = user.display_name if user else "Người dùng vô danh ({0})".format(user_id)
            medal = ["🏆", "🥈", "🥉"][index] if index < 3 else "**#{0}**".format(index + 1)
            description += "{0} | **{1}**: {2:,} 🍬\n\n".format(medal, name, total)

        embed = discord.Embed(
            title="🏆 BẢNG VÀNG ĐẠI GIA KẸO",
            description=description or "Chưa có ai chơi cả!",
            color=0xF1C40F,
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3176/3176298.png")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="work")
    @commands.cooldown(1, 45, commands.BucketType.user)
    async def work(self, ctx: commands.Context) -> None:
        _, _, _, _, _, mood, _ = self.bot.get_user_profile(ctx.author.id)

        if mood < 10:
            await err_emb(ctx, "Bé mệt rã rời rồi! Hãy đi câu cá `/fish` để thư giãn hồi Mood nhé!")
            return

        gain = random.randint(60, 150)
        self.bot.update_user_profile(ctx.author.id, candy=gain, xp=30, mood=-5)
        await q_emb(
            ctx,
            "🧹 LÀM VIỆC NHÀ",
            "Bé phụ quét nhà rất giỏi, được thưởng **{0} 🍬**!\n*(Mất 5% Tâm trạng)*".format(gain),
            0x1ABC9C,
        )

    @commands.hybrid_command(name="fish")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def fish(self, ctx: commands.Context) -> None:
        fish_name = random.choice(list(FISH_DATA.keys()))
        self.bot.update_user_profile(ctx.author.id, xp=FISH_DATA[fish_name]["xp"], mood=10)
        await q_emb(
            ctx,
            "🎣 CÂU CÁ THƯ GIÃN",
            "Wow! Bé câu được **{0}**!\n*(Hồi 10% Tâm trạng, +{1} XP)*".format(
                fish_name,
                FISH_DATA[fish_name]["xp"],
            ),
            0x3498DB,
        )


async def setup(bot: "NurseryBot") -> None:
    await bot.add_cog(EconomyCog(bot))