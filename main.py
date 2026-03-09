import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import asyncio
from datetime import datetime
import os

# ==========================================
# CẤU HÌNH BOT
# ==========================================
TOKEN = 'YOUR_BOT_TOKEN_HERE'
PREFIX = 'k!'

class NurseryManager(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        
        # Kết nối Database và tạo các bảng cần thiết
        self.conn = sqlite3.connect('nursery_data.db')
        self.c = self.conn.cursor()
        self._setup_db()

    def _setup_db(self):
        # Bảng người dùng (Kinh tế & Level)
        self.c.execute('''CREATE TABLE IF NOT EXISTS users 
                         (user_id INTEGER PRIMARY KEY, xp INTEGER, level INTEGER, candies INTEGER, last_daily TEXT)''')
        # Bảng túi đồ
        self.c.execute('''CREATE TABLE IF NOT EXISTS inventory 
                         (user_id INTEGER, item_name TEXT, quantity INTEGER)''')
        # Bảng kết nghĩa (Marry)
        self.c.execute('''CREATE TABLE IF NOT EXISTS marriage 
                         (user_id INTEGER PRIMARY KEY, partner_id INTEGER)''')
        # Bảng thú cưng
        self.c.execute('''CREATE TABLE IF NOT EXISTS pets 
                         (user_id INTEGER PRIMARY KEY, pet_name TEXT, pet_type TEXT, pet_level INTEGER)''')
        self.conn.commit()

    async def on_ready(self):
        await self.tree.sync()
        print(f'🚀 {self.user.name} đã sẵn sàng phục vụ tại Kindgarden!')

bot = NurseryManager()

# ==========================================
# HÀM BỔ TRỢ (DATABASE HELPERS)
# ==========================================
def get_user_data(user_id):
    bot.c.execute("SELECT xp, level, candies FROM users WHERE user_id = ?", (user_id,))
    row = bot.c.fetchone()
    if row is None:
        bot.c.execute("INSERT INTO users (user_id, xp, level, candies) VALUES (?, 0, 1, 100)", (user_id,))
        bot.conn.commit()
        return 0, 1, 100
    return row

def update_user(user_id, xp_add=0, candy_add=0):
    xp, lvl, candies = get_user_data(user_id)
    new_xp = xp + xp_add
    new_candies = candies + candy_add
    
    leveled_up = False
    next_xp = lvl * 100
    if new_xp >= next_xp:
        lvl += 1
        new_xp = 0
        leveled_up = True
    
    bot.c.execute("UPDATE users SET xp = ?, level = ?, candies = ? WHERE user_id = ?", 
                  (new_xp, lvl, new_candies, user_id))
    bot.conn.commit()
    return lvl, leveled_up

# ==========================================
# HỆ THỐNG MENU HELP
# ==========================================
class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Giải trí', description='Câu cá, Đào mỏ, Làm việc', emoji='🎮'),
            discord.SelectOption(label='Kinh tế & Xã hội', description='Profile, Marry, Pay, Top', emoji='💖'),
            discord.SelectOption(label='Thú cưng & Kho', description='Pet, Inventory, Sell', emoji='🐾'),
            discord.SelectOption(label='Quản trị', description='Announce, Setup Welcome', emoji='🛡️'),
        ]
        super().__init__(placeholder='Chọn danh mục bạn muốn xem...', options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        embed = discord.Embed(title=f"📖 Hướng dẫn: {cat}", color=0xffb6c1)
        
        if cat == 'Giải trí':
            embed.description = "`/fish`: Câu cá\n`/mine`: Đào mỏ\n`/work`: Làm việc tốt\n`/daily`: Nhận kẹo mỗi ngày"
        elif cat == 'Kinh tế & Xã hội':
            embed.description = "`/profile`: Xem hồ sơ\n`/top`: Bảng vàng\n`/pay`: Tặng kẹo\n`/marry`: Kết nghĩa bạn thân"
        elif cat == 'Thú cưng & Kho':
            embed.description = "`/pet_adopt`: Nuôi pet\n`/pet_info`: Xem pet\n`/inventory`: Xem túi đồ\n`/sell`: Bán vật phẩm lấy kẹo"
        else:
            embed.description = "`k!announce`: Gửi thông báo (Admin)\n`k!setup_welcome`: Cài đặt chào mừng\n`k!setlevel`: Chỉnh cấp độ"
            
        await interaction.response.edit_message(embed=embed)

# ==========================================
# LỆNH SLASH: MINIGAMES & KINH TẾ
# ==========================================
@bot.tree.command(name="fish", description="Câu cá kiếm vật phẩm")
async def fish(interaction: discord.Interaction):
    fishes = [("🐟 Cá Rô", 70), ("🐠 Cá Hề", 20), ("🦈 Cá Mập", 10)]
    fish_name = random.choices([f[0] for f in fishes], weights=[f[1] for f in fishes])[0]
    
    # Lưu vào kho
    bot.c.execute("INSERT INTO inventory (user_id, item_name, quantity) VALUES (?, ?, 1)", (interaction.user.id, fish_name))
    bot.conn.commit()
    update_user(interaction.user.id, xp_add=15)
    
    await interaction.response.send_message(f"🎣 Bé đã câu được một **{fish_name}**! Đã cất vào túi đồ.")

@bot.tree.command(name="sell", description="Bán toàn bộ cá trong túi lấy kẹo")
async def sell(interaction: discord.Interaction):
    bot.c.execute("SELECT item_name, SUM(quantity) FROM inventory WHERE user_id = ? GROUP BY item_name", (interaction.user.id,))
    items = bot.c.fetchall()
    
    if not items:
        return await interaction.response.send_message("🎒 Bé không có gì trong túi để bán cả!")

    total_gain = 0
    prices = {"🐟 Cá Rô": 50, "🐠 Cá Hề": 150, "🦈 Cá Mập": 500}
    
    for name, qty in items:
        price = prices.get(name, 10)
        total_gain += price * qty
        
    bot.c.execute("DELETE FROM inventory WHERE user_id = ?", (interaction.user.id,))
    update_user(interaction.user.id, candy_add=total_gain)
    await interaction.response.send_message(f"💰 Bé đã bán hết cá và thu về **{total_gain} 🍬 Kẹo**!")

@bot.tree.command(name="profile", description="Xem học bạ Kindgarden")
async def profile(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    xp, lvl, candies = get_user_data(user.id)
    
    # Lấy thông tin Pet và Marry
    bot.c.execute("SELECT partner_id FROM marriage WHERE user_id = ?", (user.id,))
    partner_row = bot.c.fetchone()
    partner_str = f"<@{partner_row[0]}>" if partner_row else "Chưa có"

    embed = discord.Embed(title=f"🎒 Hồ Sơ: {user.display_name}", color=0xffb6c1)
    embed.add_field(name="🏫 Lớp", value=f"Level {lvl}", inline=True)
    embed.add_field(name="🍬 Kẹo", value=f"{candies}", inline=True)
    embed.add_field(name="🤝 Bạn thân", value=partner_str, inline=True)
    embed.set_thumbnail(url=user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# ==========================================
# LỆNH SLASH: KẾT NGHĨA (MARRY)
# ==========================================
class MarriageView(discord.ui.View):
    def __init__(self, author, target):
        super().__init__(timeout=60)
        self.author = author
        self.target = target

    @discord.ui.button(label="Đồng ý 🤝", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            return await interaction.response.send_message("Không phải lượt của bạn!", ephemeral=True)
        
        bot.c.execute("INSERT OR REPLACE INTO marriage VALUES (?, ?)", (self.author.id, self.target.id))
        bot.c.execute("INSERT OR REPLACE INTO marriage VALUES (?, ?)", (self.target.id, self.author.id))
        bot.conn.commit()
        await interaction.response.edit_message(content=f"💖 **{self.author.display_name}** và **{self.target.display_name}** đã trở thành bạn thân nhất!", view=None)

@bot.tree.command(name="marry", description="Kết nghĩa bạn thân")
async def marry(interaction: discord.Interaction, member: discord.Member):
    if member == interaction.user: return await interaction.response.send_message("Tự kết nghĩa với mình sao bé?")
    view = MarriageView(interaction.user, member)
    await interaction.response.send_message(f"{member.mention}, bé {interaction.user.mention} muốn kết nghĩa bạn thân với bé đó!", view=view)

# ==========================================
# LỆNH PREFIX: QUẢN TRỊ (ADMIN)
# ==========================================
@bot.command()
@commands.has_permissions(administrator=True)
async def announce(ctx, channel: discord.TextChannel, *, content):
    embed = discord.Embed(title="📢 Thông báo từ Nhà Trường", description=content, color=0x3498db)
    embed.set_footer(text=f"Người gửi: {ctx.author.name}")
    await channel.send(embed=embed)

@bot.command()
async def help(ctx):
    view = discord.ui.View()
    view.add_item(HelpDropdown())
    await ctx.send("🤖 **Nursery Manager**\nChào bé! Bé muốn khám phá chức năng nào?", view=view)

@bot.command()
@commands.has_permissions(administrator=True)
async def setlevel(ctx, member: discord.Member, lvl: int):
    bot.c.execute("UPDATE users SET level = ?, xp = 0 WHERE user_id = ?", (lvl, member.id))
    bot.conn.commit()
    await ctx.send(f"✅ Đã đặt cấp độ của {member.mention} thành **Lớp {lvl}**.")

# ==========================================
# KHỞI CHẠY BOT
# ==========================================
if __name__ == "__main__":
    bot.run(TOKEN)
    if __name__ == "__main__":
    # Bot sẽ tìm biến có tên là 'DISCORD_TOKEN' trong phần Settings/Variables của Host
    TOKEN = os.getenv('DISCORD_TOKEN') 
    bot.run(TOKEN)
