import asyncio
import random
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from core.constants import SLOT_EMOJIS
from core.helpers import err_emb, q_emb

if TYPE_CHECKING:
    from core.bot import NurseryBot


class GamesCog(commands.Cog):
    def __init__(self, bot: "NurseryBot") -> None:
        self.bot = bot

    @commands.hybrid_command(name="race")
    async def race(self, ctx: commands.Context, bet: int, choice: str) -> None:
        _, _, candies, _, _, _, _ = self.bot.get_user_profile(ctx.author.id)
        animals = ["🐶", "🐱", "🐰", "🦊"]

        if choice not in animals:
            await err_emb(ctx, "Bé chọn sai thú rồi! Chỉ được chọn: 🐶, 🐱, 🐰 hoặc 🦊")
            return

        if bet > candies or bet < 50:
            await err_emb(ctx, "Cược tối thiểu 50 🍬 và không được cược âm hoặc lố số kẹo đang có!")
            return

        track = dict((animal, 0) for animal in animals)
        message = await ctx.send("🏁 **Chuẩn bị xuất phát...**")

        for _ in range(4):
            await asyncio.sleep(1)

            for animal in animals:
                track[animal] += random.randint(1, 4)

            await message.edit(
                content="🏎️ **TRƯỜNG ĐUA THÚ**\n" + "\n".join("{0}{1}".format("➖" * position, animal) for animal, position in track.items())
            )

        winner = max(track, key=track.get)

        if winner == choice:
            self.bot.update_user_profile(ctx.author.id, candy=bet)
            await q_emb(ctx, "🎉 CHIẾN THẮNG", "Tuyệt vời! {0} đã về nhất. Bé trúng thưởng **{1:,} 🍬**".format(winner, bet), 0x2ECC71)
            return

        self.bot.update_user_profile(ctx.author.id, candy=-bet)
        await q_emb(ctx, "😢 THUA RỒI", "Tiếc quá! {0} về nhất cơ. Bé mất **{1:,} 🍬** rồi.".format(winner, bet), 0xFF4757)

    @commands.hybrid_command(name="slot")
    async def slot(self, ctx: commands.Context, bet: int) -> None:
        _, _, candies, _, _, _, _ = self.bot.get_user_profile(ctx.author.id)

        if bet > candies or bet < 50:
            await err_emb(ctx, "Cược tối thiểu 50 🍬 và không vượt quá túi kẹo!")
            return

        slot_1, slot_2, slot_3 = random.choices(SLOT_EMOJIS, k=3)
        embed = discord.Embed(
            title="🎰 MÁY QUAY XÈNG",
            description="**[ {0} | {1} | {2} ]**".format(slot_1, slot_2, slot_3),
            color=0x9B59B6,
        )

        if slot_1 == slot_2 == slot_3:
            win = bet * 5
            self.bot.update_user_profile(ctx.author.id, candy=win)
            embed.add_field(name="Nổ Hũ!", value="Chúc mừng bé! Trúng gấp 5 lần: **{0:,} 🍬**".format(win))
        elif slot_1 == slot_2 or slot_2 == slot_3 or slot_1 == slot_3:
            win = bet * 2
            self.bot.update_user_profile(ctx.author.id, candy=win)
            embed.add_field(name="Thắng nhỏ!", value="Trúng 2 ô! Bé nhận được: **{0:,} 🍬**".format(win))
        else:
            self.bot.update_user_profile(ctx.author.id, candy=-bet)
            embed.add_field(name="Trượt rồi!", value="Máy xèng nuốt mất của bé **{0:,} 🍬**".format(bet))

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="coinflip", aliases=["cf"])
    async def coinflip(self, ctx: commands.Context, bet: int, choice: str) -> None:
        _, _, candies, _, _, _, _ = self.bot.get_user_profile(ctx.author.id)

        if choice.lower() not in ["ngửa", "sấp", "h", "t"]:
            await err_emb(ctx, "Bé hãy chọn `ngửa` (h) hoặc `sấp` (t) nhé!")
            return

        if bet > candies or bet < 10:
            await err_emb(ctx, "Cược tối thiểu 10 🍬 và không vượt quá túi kẹo!")
            return

        user_choice = "ngửa" if choice.lower() in ["ngửa", "h"] else "sấp"
        result = random.choice(["ngửa", "sấp"])

        if user_choice == result:
            self.bot.update_user_profile(ctx.author.id, candy=bet)
            await q_emb(
                ctx,
                "🪙 TUNG ĐỒNG XU",
                "Đồng xu ra **{0}**! Bé đoán đúng và ăn được **{1:,} 🍬**".format(result.upper(), bet),
                0x2ECC71,
            )
            return

        self.bot.update_user_profile(ctx.author.id, candy=-bet)
        await q_emb(
            ctx,
            "🪙 TUNG ĐỒNG XU",
            "Đồng xu ra **{0}**! Bé đoán sai và mất **{1:,} 🍬**".format(result.upper(), bet),
            0xFF4757,
        )


async def setup(bot: "NurseryBot") -> None:
    await bot.add_cog(GamesCog(bot))