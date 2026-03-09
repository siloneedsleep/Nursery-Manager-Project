import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import os
from dotenv import load_dotenv

# ==========================================
# CẤU HÌNH BOT (ĐỌC TỪ .ENV)
# ==========================================
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = 'k!'

class NurseryManager(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        
        # Kết nối Database - check_same_thread=False cực kỳ quan trọng cho Slash Commands
        self.conn = sqlite3.connect('nursery_data.db', check_same_thread=False)
        self.c = self.conn.cursor()
        self._setup_db()

    def _setup_db(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS users 
                         (user_id INTEGER PRIMARY KEY, xp INTEGER, level INTEGER, candies INTEGER, last_daily TEXT)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS inventory 
                         (user_id INTEGER, item_name TEXT, quantity INTEGER)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS marriage 
                         (user_id INTEGER PRIMARY KEY, partner_id INTEGER)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS pets 
                         (user_id INTEGER PRIMARY KEY, pet_name TEXT, pet_type TEXT, pet_level INTEGER)''')
        self.conn.commit()

    async def on_ready(self):
        try:
            synced = await self.tree.sync()
            print(f"✅ Đã đồng bộ {len(synced)} lệnh slash!")
        except Exception as e:
            print(f"❌ Lỗi đồng bộ lệnh: {e}")
        print(f'🚀 {self.user.name} đã sẵn sàng phục vụ tại Kindgarden!')

bot = NurseryManager()

# --- HELPERS ---
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
    next_xp = lvl * 100
    if new_xp >= next_xp:
        lvl += 1
        new_xp = 0
    bot.c.execute("UPDATE users SET xp = ?, level = ?, candies = ? WHERE user_id = ?", (new_xp, lvl, new_candies, user_id))
    bot.conn.commit()
    return lvl

# --- SLASH COMMANDS ---
@bot.tree.command(name="fish", description="Câu cá kiếm vật phẩm")
async def fish(interaction: discord.Interaction):
    fishes = [("🐟 Cá Rô", 70), ("🐠 Cá Hề", 20), ("🦈 Cá Mập", 10)]
    fish_name = random.choices([f[0] for f in fishes], weights=[f[1] for f in fishes])[0]
    bot.c.execute("INSERT INTO inventory (user_id, item_name, quantity) VALUES (?, ?, 1)", (interaction.user.id, fish_name))
    bot.conn.commit()
    update_user(interaction.user.id, xp_add=15)
    await interaction.response.send_message(f"🎣 Bé đã câu được một **{fish_name}**!")

@bot.tree.command(name="profile", description="Xem học bạ")
async def profile(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    xp, lvl, candies = get_user_data(user.id)
    embed = discord.Embed(title=f"🎒 Hồ Sơ: {user.display_name}", color=0xffb6c1)
    embed.add_field(name="🏫 Lớp", value=f"Level {lvl}", inline=True)
    embed.add_field(name="🍬 Kẹo", value=f"{candies}", inline=True)
    embed.set_thumbnail(url=user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="marry", description="Kết nghĩa bạn thân")
async def marry(interaction: discord.Interaction, member: discord.Member):
    if member == interaction.user: return await interaction.response.send_message("Tự kết nghĩa với mình sao?")
    bot.c.execute("INSERT OR REPLACE INTO marriage VALUES (?, ?)", (interaction.user.id, member.id))
    bot.c.execute("INSERT OR REPLACE INTO marriage VALUES (?, ?)", (member.id, interaction.user.id))
    bot.conn.commit()
    await interaction.response.send_message(f"💖 {interaction.user.mention} và {member.mention} đã là bạn thân!")

# --- PREFIX COMMANDS ---
@bot.command()
async def help(ctx):
    await ctx.send("🤖 **Nursery Manager**: Dùng `/` để xem các lệnh Slash như `/fish`, `/profile`, `/marry`!")

if __name__ == "__main__":
    bot.run(TOKEN)
