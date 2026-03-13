from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from core.helpers import is_admin_or_owner, q_emb, send_log

if TYPE_CHECKING:
    from core.bot import NurseryBot


class AdminCog(commands.Cog):
    def __init__(self, bot: "NurseryBot") -> None:
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def admin(self, ctx: commands.Context, member: discord.Member) -> None:
        cursor = self.bot.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO admins VALUES (?)", (member.id,))
        self.bot.conn.commit()
        await q_emb(ctx, "👮 CẤP QUYỀN", "Đã thêm {0} vào danh sách **Bảo Mẫu**!".format(member.mention), 0x2ECC71)

    @commands.command()
    @commands.is_owner()
    async def removead(self, ctx: commands.Context, member: discord.Member) -> None:
        cursor = self.bot.conn.cursor()
        cursor.execute("DELETE FROM admins WHERE user_id = ?", (member.id,))
        self.bot.conn.commit()
        await q_emb(ctx, "💢 TƯỚC QUYỀN", "Đã xóa {0} khỏi danh sách Admin!".format(member.mention), 0xFF4757)

    @commands.command()
    @commands.is_owner()
    async def setlog(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        cursor = self.bot.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO config VALUES ('log_channel', ?)", (channel.id,))
        self.bot.conn.commit()
        await q_emb(ctx, "⚙️ CẤU HÌNH", "Đã thiết lập kênh {0} làm nơi lưu nhật ký!".format(channel.mention), 0x2ECC71)

    @commands.command()
    @commands.is_owner()
    async def edit(self, ctx: commands.Context, member: discord.Member, amount: int) -> None:
        self.bot.update_user_profile(member.id, candy=amount)
        action = "TẶNG" if amount >= 0 else "THU HỒI"

        await q_emb(
            ctx,
            "💎 ĐIỀU CHỈNH KẸO",
            "Đã {0} **{1} 🍬** cho {2}.".format(action.lower(), abs(amount), member.mention),
            0xF1C40F,
        )
        await send_log(
            ctx,
            "BIẾN ĐỘNG KHO KẸO",
            "**Hành động:** {0} {1} 🍬\n**Đối tượng:** {2}".format(action, abs(amount), member.mention),
            0xE67E22,
        )

    @commands.command()
    @is_admin_or_owner()
    async def noti(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        role: discord.Role,
        *,
        content: str
    ) -> None:
        await ctx.message.delete()

        embed = discord.Embed(
            title="📢 THÔNG BÁO TỪ BẢO MẪU",
            description="\n{0}".format(content),
            color=0xF1C40F,
        )

        if ctx.guild and ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        await channel.send(content=role.mention, embed=embed)

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context) -> None:
        await self.bot.tree.sync()
        await ctx.send("✅ Đã đồng bộ toàn bộ lệnh Slash!")


async def setup(bot: "NurseryBot") -> None:
    await bot.add_cog(AdminCog(bot))