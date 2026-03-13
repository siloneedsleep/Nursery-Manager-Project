import discord
from discord.ext import commands
import sqlite3
import random
import datetime
import asyncio
import os
from typing import Optional
from dotenv import load_dotenv

# ==========================================

# 1. CẤU HÌNH HỆ THỐNG

# ==========================================

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

OWNER_ID = 914831312295165982

PREFIXES = ['>', '?']

FISH_DATA = {

    "🐟 Cá Rô": {"xp": 20}, "🐠 Cá Hề": {"xp": 40}, "🦑 Mực Ống": {"xp": 80},

    "🦈 Cá Mập": {"xp": 150}, "🐳 Cá Voi Xanh": {"xp": 400}

}

SLOT_EMOJIS = ["🍒", "🍉", "🍇", "🍋", "💎", "🔔"]

# ==========================================

# 2. KHỞI TẠO BOT & DATABASE

# ==========================================

class UltimateNurseryBot(commands.Bot):

    def __init__(self):

        intents = discord.Intents.all()

        super().__init__(command_prefix=commands.when_mentioned_or(*PREFIXES), intents=intents, help_command=None)

        self.conn = sqlite3.connect('nursery_final.db', check_same_thread=False)

        self._setup_db()

    def _setup_db(self):

        c = self.conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0, 

                     lvl INTEGER DEFAULT 1, candies INTEGER DEFAULT 100, bank INTEGER DEFAULT 0, 

                     last_daily TEXT, mood INTEGER DEFAULT 100, title TEXT DEFAULT 'Bé Ngoan')''')

        c.execute('''CREATE TABLE IF NOT EXISTS classrooms (class_name TEXT PRIMARY KEY, role_id INTEGER, teacher_id INTEGER)''')

        c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')

        c.execute('''CREATE TABLE IF NOT EXISTS inventory (user_id INTEGER, item_name TEXT, quantity INTEGER, PRIMARY KEY(user_id, item_name))''')

        c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value INTEGER)''')

        self.conn.commit()

    def get_user(self, uid):

        c = self.conn.cursor()

        c.execute("SELECT xp, lvl, candies, bank, last_daily, mood, title FROM users WHERE user_id = ?", (uid,))

        row = c.fetchone()

        if not row:

            c.execute("INSERT INTO users (user_id) VALUES (?)", (uid,))

            self.conn.commit()

            return (0, 1, 100, 0, None, 100, 'Bé Ngoan')

        return row

    def update_user(self, uid, candy=0, bank=0, xp=0, mood=0):

        xp_old, lvl, can_old, bnk_old, ld, mood_old, title = self.get_user(uid)

        new_xp = xp_old + xp

        new_lvl = lvl

        while new_xp >= (new_lvl * 500):

            new_xp -= (new_lvl * 500)

            new_lvl += 1

        c = self.conn.cursor()

        c.execute("UPDATE users SET xp=?, lvl=?, candies=?, bank=?, mood=? WHERE user_id=?",

                  (new_xp, new_lvl, max(0, can_old + candy), max(0, bnk_old + bank), min(100, max(0, mood_old + mood)), uid))

        self.conn.commit()

        return new_lvl > lvl, new_lvl

bot = UltimateNurseryBot()

# --- FORMATTING HELPERS ---

async def q_emb(ctx, title, desc, color=0xffb6c1, thumbnail=None):

    embed = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.datetime.now())

    embed.set_footer(text=f"📌 Yêu cầu bởi {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

    if thumbnail:

        embed.set_thumbnail(url=thumbnail)

    return await ctx.send(embed=embed)

async def err_emb(ctx, desc):

    embed = discord.Embed(title="⚠️ Ôi hỏng!", description=f"**{desc}**", color=0xff4757)

    return await ctx.send(embed=embed, delete_after=15)

async def send_log(ctx, action_title, details, color=0x34495e):

    c = bot.conn.cursor()

    c.execute("SELECT value FROM config WHERE key = 'log_channel'")

    res = c.fetchone()

    if res:

        log_channel = bot.get_channel(res[0])

        if log_channel:

            embed = discord.Embed(title=f"📜 LOG: {action_title}", description=details, color=color, timestamp=datetime.datetime.now())

            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

            await log_channel.send(embed=embed)

def is_admin_or_owner():

    async def predicate(ctx):

        if ctx.author.id == OWNER_ID:

            return True

        c = bot.conn.cursor()

        c.execute("SELECT 1 FROM admins WHERE user_id = ?", (ctx.author.id,))

        return c.fetchone() is not None

    return commands.check(predicate)

def normalize_class_name(name: str) -> str:

    return name.strip().lower()

def get_classroom_record(name: str):

    c = bot.conn.cursor()

    c.execute("SELECT class_name, role_id, teacher_id FROM classrooms WHERE class_name = ?", (normalize_class_name(name),))

    return c.fetchone()

def get_all_classrooms():

    c = bot.conn.cursor()

    c.execute("SELECT class_name, role_id, teacher_id FROM classrooms ORDER BY class_name ASC")

    return c.fetchall()

def format_teacher(guild: discord.Guild, teacher_id: Optional[int]) -> str:

    if not teacher_id:

        return "Chưa phân công"

    teacher = guild.get_member(teacher_id)

    if teacher:

        return teacher.mention

    return f"`ID {teacher_id}` (không còn trong server)"

async def resolve_classroom(ctx, name: str):

    record = get_classroom_record(name)

    if not record:

        await err_emb(ctx, "Lớp này chưa được tạo!")

        return None

    class_name, role_id, teacher_id = record

    role = ctx.guild.get_role(role_id)

    if not role:

        await err_emb(ctx, "Role của lớp này không còn tồn tại. Hãy dùng `class setup` để gắn lại role nhé!")

        return None

    return class_name, role, teacher_id

# ==========================================

# 3. NHÓM LỆNH OWNER (CHỦ TRƯỞNG)

# ==========================================


@bot.command()

@commands.is_owner()

async def admin(ctx, member: discord.Member):

    bot.conn.cursor().execute("INSERT OR IGNORE INTO admins VALUES (?)", (member.id,))

    bot.conn.commit()

    await q_emb(ctx, "👮 CẤP QUYỀN", f"Đã thêm {member.mention} vào danh sách **Bảo Mẫu**!", 0x2ecc71)

@bot.command()

@commands.is_owner()

async def removead(ctx, member: discord.Member):

    bot.conn.cursor().execute("DELETE FROM admins WHERE user_id = ?", (member.id,))

    bot.conn.commit()

    await q_emb(ctx, "💢 TƯỚC QUYỀN", f"Đã xóa {member.mention} khỏi danh sách Admin!", 0xff4757)

@bot.command()

@commands.is_owner()

async def setlog(ctx, channel: discord.TextChannel):

    bot.conn.cursor().execute("INSERT OR REPLACE INTO config VALUES ('log_channel', ?)", (channel.id,))

    bot.conn.commit()

    await q_emb(ctx, "⚙️ CẤU HÌNH", f"Đã thiết lập kênh {channel.mention} làm nơi lưu nhật ký!", 0x2ecc71)

@bot.command()

@commands.is_owner()

async def edit(ctx, member: discord.Member, amount: int):

    bot.update_user(member.id, candy=amount)

    action = "TẶNG" if amount >= 0 else "THU HỒI"

    await q_emb(ctx, "💎 ĐIỀU CHỈNH KẸO", f"Đã {action.lower()} **{abs(amount)} 🍬** cho {member.mention}.", 0xf1c40f)

    await send_log(ctx, "BIẾN ĐỘNG KHO KẸO", f"**Hành động:** {action} {abs(amount)} 🍬\n**Đối tượng:** {member.mention}", 0xe67e22)

# ==========================================

# 4. NHÓM LỆNH ADMIN (BẢO MẪU) - LỚP HỌC

# ==========================================

@bot.command()

@is_admin_or_owner()

async def noti(ctx, channel: discord.TextChannel, role: discord.Role, *, content: str):

    await ctx.message.delete()

    emb = discord.Embed(title="📢 THÔNG BÁO TỪ BẢO MẪU", description=f"\n{content}", color=0xf1c40f)

    emb.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)

    await channel.send(content=role.mention, embed=emb)

@bot.group(name="classroom", aliases=["class"], invoke_without_command=True)

async def classroom(ctx):

    await ctx.invoke(bot.get_command('help'), cmd="classroom")

@classroom.command(name="setup")

@is_admin_or_owner()

async def class_setup(ctx, name: str, role: discord.Role):

    class_name = normalize_class_name(name)

    if not class_name:

        return await err_emb(ctx, "Tên lớp không được để trống!")

    c = bot.conn.cursor()

    existing = get_classroom_record(class_name)

    if existing:

        c.execute("UPDATE classrooms SET role_id = ? WHERE class_name = ?", (role.id, class_name))

        message = f"Đã cập nhật lớp **{class_name.upper()}** sang Role {role.mention}!"

    else:

        c.execute("INSERT INTO classrooms (class_name, role_id, teacher_id) VALUES (?, ?, ?)", (class_name, role.id, None))

        message = f"Lớp **{class_name.upper()}** đã được gắn với Role {role.mention}!"

    bot.conn.commit()

    await q_emb(ctx, "✅ CẤU HÌNH LỚP THÀNH CÔNG", message, 0x2ecc71)

    await send_log(ctx, "CẬP NHẬT LỚP HỌC", f"**Lớp:** {class_name.upper()}\n**Role:** {role.mention}", 0x2ecc71)

@classroom.command(name="list", aliases=["all", "ls"])

async def class_list(ctx):

    classrooms = get_all_classrooms()

    if not classrooms:

        return await err_emb(ctx, "Hiện chưa có lớp học nào được tạo!")

    lines = []

    for class_name, role_id, teacher_id in classrooms:

        role = ctx.guild.get_role(role_id)

        role_text = role.mention if role else "Role đã bị xóa"

        class_size = len(role.members) if role else 0

        teacher_text = format_teacher(ctx.guild, teacher_id)

        lines.append(f"**{class_name.upper()}** | {role_text} | GV: {teacher_text} | Sĩ số: **{class_size}** bé")

    await q_emb(ctx, "📚 DANH SÁCH LỚP HỌC", "\n".join(lines), 0x3498db)

@classroom.command(name="info")

async def class_info(ctx, name: str):

    resolved = await resolve_classroom(ctx, name)

    if not resolved:

        return

    class_name, role, teacher_id = resolved

    members_preview = ", ".join(member.mention for member in role.members[:10]) or "Chưa có bé nào trong lớp."

    if len(role.members) > 10:

        members_preview += f"\n... và thêm **{len(role.members) - 10}** bé nữa."

    embed = discord.Embed(title=f"🏫 THÔNG TIN LỚP: {class_name.upper()}", color=0x3498db)

    embed.add_field(name="🏷️ Role Lớp", value=role.mention, inline=True)

    embed.add_field(name="👩‍🏫 Giáo viên", value=format_teacher(ctx.guild, teacher_id), inline=True)

    embed.add_field(name="👥 Sĩ số", value=f"**{len(role.members)}** bé", inline=True)

    embed.add_field(name="🧸 Danh sách nhanh", value=members_preview, inline=False)

    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)

    await ctx.send(embed=embed)

@classroom.command(name="teacher")

@is_admin_or_owner()

async def class_teacher(ctx, name: str, member: Optional[discord.Member] = None):

    record = get_classroom_record(name)

    if not record:

        return await err_emb(ctx, "Lớp này chưa được tạo!")

    class_name, _, _ = record

    if member and member.bot:

        return await err_emb(ctx, "Không thể phân công bot làm giáo viên lớp nhé!")

    c = bot.conn.cursor()

    if member is None:

        c.execute("UPDATE classrooms SET teacher_id = NULL WHERE class_name = ?", (class_name,))

        bot.conn.commit()

        await q_emb(ctx, "🧹 GỠ GIÁO VIÊN CHỦ NHIỆM", f"Đã gỡ phân công giáo viên khỏi lớp **{class_name.upper()}**.", 0xe67e22)

        await send_log(ctx, "GỠ GIÁO VIÊN CHỦ NHIỆM", f"**Lớp:** {class_name.upper()}", 0xe67e22)

        return

    c.execute("UPDATE classrooms SET teacher_id = ? WHERE class_name = ?", (member.id, class_name))

    bot.conn.commit()

    await q_emb(ctx, "👩‍🏫 PHÂN CÔNG GIÁO VIÊN", f"Đã phân công {member.mention} phụ trách lớp **{class_name.upper()}**.", 0x1abc9c)

    await send_log(ctx, "PHÂN CÔNG GIÁO VIÊN", f"**Lớp:** {class_name.upper()}\n**Giáo viên:** {member.mention}", 0x1abc9c)

@classroom.command(name="add")

@is_admin_or_owner()

async def class_add(ctx, name: str, member: discord.Member):

    resolved = await resolve_classroom(ctx, name)

    if not resolved:

        return

    class_name, role, _ = resolved

    other_class_roles = []

    for other_name, role_id, _ in get_all_classrooms():

        if other_name == class_name:

            continue

        other_role = ctx.guild.get_role(role_id)

        if other_role and other_role in member.roles:

            other_class_roles.append(other_role)

    if role in member.roles and not other_class_roles:

        return await err_emb(ctx, f"{member.mention} đã ở sẵn lớp **{class_name.upper()}** rồi!")

    try:

        if other_class_roles:

            await member.remove_roles(*other_class_roles, reason=f"Chuyển lớp sang {class_name.upper()}")

        if role not in member.roles:

            await member.add_roles(role, reason=f"Xếp vào lớp {class_name.upper()}")

        moved_from = ""

        if other_class_roles:

            moved_from = f"\nĐã chuyển bé khỏi: {', '.join(role_item.mention for role_item in other_class_roles)}"

        await q_emb(ctx, "🎒 NHẬP HỌC", f"Đã bế bé {member.mention} vào lớp **{class_name.upper()}** ({role.mention})!{moved_from}", 0x9b59b6)

        await send_log(ctx, "XẾP LỚP HỌC SINH", f"**Lớp mới:** {class_name.upper()}\n**Học sinh:** {member.mention}", 0x9b59b6)

    except discord.Forbidden:

        await err_emb(ctx, "Bot không có quyền chỉnh Role này! Hãy kéo Role của bot lên cao hơn Role lớp nhé.")

@classroom.command(name="remove", aliases=["kick"])

@is_admin_or_owner()

async def class_remove(ctx, name: str, member: discord.Member):

    resolved = await resolve_classroom(ctx, name)

    if not resolved:

        return

    class_name, role, _ = resolved

    if role not in member.roles:

        return await err_emb(ctx, f"{member.mention} hiện không ở lớp **{class_name.upper()}**.")

    try:

        await member.remove_roles(role, reason=f"Rời lớp {class_name.upper()}")

        await q_emb(ctx, "🧸 RỜI LỚP", f"Đã đưa bé {member.mention} ra khỏi lớp **{class_name.upper()}**.", 0xe67e22)

        await send_log(ctx, "XÓA HỌC SINH KHỎI LỚP", f"**Lớp:** {class_name.upper()}\n**Học sinh:** {member.mention}", 0xe67e22)

    except discord.Forbidden:

        await err_emb(ctx, "Bot không có quyền gỡ Role này! Hãy kiểm tra thứ tự Role của bot nhé.")

@classroom.command(name="reward")

@is_admin_or_owner()

async def class_reward(ctx, name: str, amount: int):

    if amount <= 0:

        return await err_emb(ctx, "Số kẹo thưởng phải lớn hơn 0 nhé!")

    resolved = await resolve_classroom(ctx, name)

    if not resolved:

        return

    class_name, role, _ = resolved

    if not role.members:

        return await err_emb(ctx, "Lớp này chưa có bé nào để phát thưởng!")

    c = bot.conn.cursor()

    for member in role.members:

        bot.get_user(member.id)

        c.execute("UPDATE users SET candies = candies + ? WHERE user_id = ?", (amount, member.id))

    bot.conn.commit()

    total_amount = amount * len(role.members)

    await q_emb(ctx, "🎁 THƯỞNG LỚP", f"Bảo mẫu đã phát **{amount} 🍬** cho mỗi bé ở lớp {role.mention}!\nTổng phát: **{total_amount:,} 🍬**", 0xf1c40f)

    await send_log(ctx, "THƯỞNG THEO LỚP", f"**Lớp:** {class_name.upper()}\n**Số bé:** {len(role.members)}\n**Thưởng mỗi bé:** {amount:,} 🍬", 0xf1c40f)

@classroom.command(name="delete", aliases=["del", "removeclass"])

@is_admin_or_owner()

async def class_delete(ctx, name: str):

    record = get_classroom_record(name)

    if not record:

        return await err_emb(ctx, "Lớp này chưa được tạo!")

    class_name, role_id, _ = record

    role = ctx.guild.get_role(role_id)

    bot.conn.cursor().execute("DELETE FROM classrooms WHERE class_name = ?", (class_name,))

    bot.conn.commit()

    role_text = role.mention if role else f"`ID {role_id}`"

    await q_emb(ctx, "🗑️ XÓA CẤU HÌNH LỚP", f"Đã xóa lớp **{class_name.upper()}** khỏi hệ thống quản lý.\nRole liên kết trước đó: {role_text}\n*Lưu ý: Bot không xóa Discord role đang có.*", 0xff4757)

    await send_log(ctx, "XÓA CẤU HÌNH LỚP", f"**Lớp:** {class_name.upper()}\n**Role cũ:** {role_text}", 0xff4757)

# ==========================================

# 5. KINH TẾ & HỒ SƠ

# ==========================================

@bot.hybrid_command(name="profile", aliases=["pf"])

async def profile(ctx, member: Optional[discord.Member] = None):

    member = member or ctx.author

    xp, lvl, can, bnk, ld, mood, title = bot.get_user(member.id)

    

    needed_xp = lvl * 500

    progress = int((xp / needed_xp) * 10)

    bar = "▰" * progress + "▱" * (10 - progress)

    

    embed = discord.Embed(title=f"📛 HỒ SƠ: {member.display_name}", description=f"✨ **Danh hiệu:** `{title}`", color=0xffb6c1)

    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="📊 Cấp độ", value=f"**Cấp {lvl}**\n{bar} ({xp}/{needed_xp} XP)", inline=False)

    embed.add_field(name="🍬 Túi Kẹo", value=f"**{can:,}** 🍬", inline=True)

    embed.add_field(name="🏦 Ngân Hàng", value=f"**{bnk:,}** 🍬", inline=True)

    embed.add_field(name="🎭 Tâm Trạng", value=f"**{mood}/100** 💖", inline=True)

    await ctx.send(embed=embed)

@bot.hybrid_command(name="daily")

async def daily(ctx):

    uid = ctx.author.id

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    c = bot.conn.cursor()

    c.execute("SELECT last_daily FROM users WHERE user_id = ?", (uid,))

    res = c.fetchone()

    

    if res and res[0] == today:

        return await err_emb(ctx, "Hôm nay bé đã nhận kẹo rồi, mai quay lại nhé!")

        

    bot.get_user(uid) # Đảm bảo user tồn tại

    c.execute("UPDATE users SET last_daily = ?, candies = candies + 300 WHERE user_id = ?", (today, uid))

    bot.conn.commit()

    await q_emb(ctx, "📅 ĐIỂM DANH HÀNG NGÀY", "Bé ngoan lắm! Thưởng cho bé **300 🍬** nhé!", 0x2ecc71)

@bot.hybrid_command(name="dep")

async def dep(ctx, amount: int):

    xp, lvl, can, bnk, ld, mood, title = bot.get_user(ctx.author.id)

    if amount > can or amount <= 0:

        return await err_emb(ctx, "Số kẹo gửi không hợp lệ hoặc bé không có đủ kẹo!")

    

    bot.update_user(ctx.author.id, candy=-amount, bank=amount)

    await q_emb(ctx, "🏦 GỬI NGÂN HÀNG", f"Bé đã cất an toàn **{amount:,} 🍬** vào lợn đất!", 0x3498db)

@bot.hybrid_command(name="with")

async def withdraw(ctx, amount: int):

    xp, lvl, can, bnk, ld, mood, title = bot.get_user(ctx.author.id)

    if amount > bnk or amount <= 0:

        return await err_emb(ctx, "Số kẹo rút không hợp lệ hoặc lợn đất không đủ kẹo!")

    

    bot.update_user(ctx.author.id, candy=amount, bank=-amount)

    await q_emb(ctx, "🏦 RÚT NGÂN HÀNG", f"Bé đã đập lợn lấy ra **{amount:,} 🍬** để xài!", 0xe67e22)

@bot.hybrid_command(name="leaderboard", aliases=["lb", "top"])

async def leaderboard(ctx):

    c = bot.conn.cursor()

    c.execute("SELECT user_id, (candies + bank) as total FROM users ORDER BY total DESC LIMIT 10")

    top_users = c.fetchall()

    

    desc = ""

    for i, (uid, total) in enumerate(top_users):

        user = ctx.guild.get_member(uid) or bot.get_user(uid)

        name = user.display_name if user else f"Người dùng vô danh ({uid})"

        medal = ["🏆", "🥈", "🥉"][i] if i < 3 else f"**#{i+1}**"

        desc += f"{medal} | **{name}**: {total:,} 🍬\n\n"

        

    embed = discord.Embed(title="🏆 BẢNG VÀNG ĐẠI GIA KẸO", description=desc or "Chưa có ai chơi cả!", color=0xf1c40f)

    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3176/3176298.png") # Icon kẹo

    await ctx.send(embed=embed)

@bot.hybrid_command(name="work")

@commands.cooldown(1, 45, commands.BucketType.user)

async def work(ctx):

    xp, lvl, can, bnk, ld, mood, title = bot.get_user(ctx.author.id)

    if mood < 10: return await err_emb(ctx, "Bé mệt rã rời rồi! Hãy đi câu cá `/fish` để thư giãn hồi Mood nhé!")

    gain = random.randint(60, 150)

    bot.update_user(ctx.author.id, candy=gain, xp=30, mood=-5)

    await q_emb(ctx, "🧹 LÀM VIỆC NHÀ", f"Bé phụ quét nhà rất giỏi, được thưởng **{gain} 🍬**!\n*(Mất 5% Tâm trạng)*", 0x1abc9c)

@bot.hybrid_command(name="fish")

@commands.cooldown(1, 15, commands.BucketType.user)

async def fish(ctx):

    f = random.choice(list(FISH_DATA.keys()))

    bot.update_user(ctx.author.id, xp=FISH_DATA[f]["xp"], mood=10)

    await q_emb(ctx, "🎣 CÂU CÁ THƯ GIÃN", f"Wow! Bé câu được **{f}**!\n*(Hồi 10% Tâm trạng, +{FISH_DATA[f]['xp']} XP)*", 0x3498db)

# ==========================================

# 6. MINI-GAMES TRÒ CHƠI

# ==========================================

@bot.hybrid_command(name="race")

async def race(ctx, bet: int, choice: str):

    _, _, can, _, _, _, _ = bot.get_user(ctx.author.id)

    animals = ["🐶", "🐱", "🐰", "🦊"]

    

    if choice not in animals:

        return await err_emb(ctx, "Bé chọn sai thú rồi! Chỉ được chọn: 🐶, 🐱, 🐰 hoặc 🦊")

    if bet > can or bet < 50: 

        return await err_emb(ctx, "Cược tối thiểu 50 🍬 và không được cược âm hoặc lố số kẹo đang có!")

    

    track = {a: 0 for a in animals}

    msg = await ctx.send("🏁 **Chuẩn bị xuất phát...**")

    

    for _ in range(4):

        await asyncio.sleep(1)

        for a in animals: track[a] += random.randint(1, 4)

        await msg.edit(content="🏎️ **TRƯỜNG ĐUA THÚ**\n" + "\n".join([f"{'➖' * pos}{a}" for a, pos in track.items()]))

        

    winner = max(track, key=track.get)

    

    if winner == choice: 

        bot.update_user(ctx.author.id, candy=bet) 

        await q_emb(ctx, "🎉 CHIẾN THẮNG", f"Tuyệt vời! {winner} đã về nhất. Bé trúng thưởng **{bet:,} 🍬**", 0x2ecc71)

    else:

        bot.update_user(ctx.author.id, candy=-bet) 

        await q_emb(ctx, "😢 THUA RỒI", f"Tiếc quá! {winner} về nhất cơ. Bé mất **{bet:,} 🍬** rồi.", 0xff4757)

@bot.hybrid_command(name="slot")

async def slot(ctx, bet: int):

    _, _, can, _, _, _, _ = bot.get_user(ctx.author.id)

    if bet > can or bet < 50: return await err_emb(ctx, "Cược tối thiểu 50 🍬 và không vượt quá túi kẹo!")

    

    s1, s2, s3 = random.choices(SLOT_EMOJIS, k=3)

    embed = discord.Embed(title="🎰 MÁY QUAY XÈNG", description=f"**[ {s1} | {s2} | {s3} ]**", color=0x9b59b6)

    

    if s1 == s2 == s3:

        win = bet * 5

        bot.update_user(ctx.author.id, candy=win)

        embed.add_field(name="Nổ Hũ!", value=f"Chúc mừng bé! Trúng gấp 5 lần: **{win:,} 🍬**")

    elif s1 == s2 or s2 == s3 or s1 == s3:

        win = bet * 2

        bot.update_user(ctx.author.id, candy=win)

        embed.add_field(name="Thắng nhỏ!", value=f"Trúng 2 ô! Bé nhận được: **{win:,} 🍬**")

    else:

        bot.update_user(ctx.author.id, candy=-bet)

        embed.add_field(name="Trượt rồi!", value=f"Máy xèng nuốt mất của bé **{bet:,} 🍬**")

    

    await ctx.send(embed=embed)

@bot.hybrid_command(name="coinflip", aliases=["cf"])

async def coinflip(ctx, bet: int, choice: str):

    _, _, can, _, _, _, _ = bot.get_user(ctx.author.id)

    if choice.lower() not in ["ngửa", "sấp", "h", "t"]:

        return await err_emb(ctx, "Bé hãy chọn `ngửa` (h) hoặc `sấp` (t) nhé!")

    if bet > can or bet < 10: 

        return await err_emb(ctx, "Cược tối thiểu 10 🍬 và không vượt quá túi kẹo!")

    user_choice = "ngửa" if choice.lower() in ["ngửa", "h"] else "sấp"

    result = random.choice(["ngửa", "sấp"])

    

    if user_choice == result:

        bot.update_user(ctx.author.id, candy=bet)

        await q_emb(ctx, "🪙 TUNG ĐỒNG XU", f"Đồng xu ra **{result.upper()}**! Bé đoán đúng và ăn được **{bet:,} 🍬**", 0x2ecc71)

    else:

        bot.update_user(ctx.author.id, candy=-bet)

        await q_emb(ctx, "🪙 TUNG ĐỒNG XU", f"Đồng xu ra **{result.upper()}**! Bé đoán sai và mất **{bet:,} 🍬**", 0xff4757)

# ==========================================

# 7. HỆ THỐNG HELP & SYNC & ERROR

# ==========================================

@bot.hybrid_command(name="help")

async def help_command(ctx, cmd: Optional[str] = None):

    if not cmd:

        emb = discord.Embed(title="🌈 BẢNG CHỈ DẪN NHÀ TRẺ", description="Gõ `/help <tên_lệnh>` để xem chi tiết nhé!", color=0xffb6c1)

        emb.set_thumbnail(url=bot.user.display_avatar.url)

        emb.add_field(name="🏫 LỚP HỌC", value="`class list`, `class info`, `class setup`, `class teacher`, `class add`, `class remove`, `class reward`, `class delete`", inline=False)

        emb.add_field(name="🍬 KINH TẾ", value="`profile`, `work`, `daily`, `fish`, `dep`, `with`, `leaderboard`", inline=False)

        emb.add_field(name="🎮 TRÒ CHƠI", value="`race`, `slot`, `coinflip`", inline=False)

        emb.add_field(name="⚙️ QUẢN TRỊ", value="`noti`, `admin`, `removead`, `edit`, `setlog`", inline=False)

        emb.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}")

        return await ctx.send(embed=emb)

    if cmd.lower() in ["classroom", "class"]:

        return await q_emb(

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

            0x3498db

        )

    

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

        "class delete": "Admin: Xóa cấu hình lớp khỏi hệ thống quản lý."

    }

    await q_emb(ctx, f"📖 CHI TIẾT: {cmd.upper()}", details.get(cmd.lower(), "Bạn cứ thử dùng lệnh đó đi, dễ lắm!"), 0x3498db)

@bot.command()

@commands.is_owner()

async def sync(ctx):

    await bot.tree.sync()

    await ctx.send("✅ Đã đồng bộ toàn bộ lệnh Slash!")

@bot.event

async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandOnCooldown):

        await err_emb(ctx, f"Bé đang mệt hoặc làm quá nhanh! Chờ **{error.retry_after:.0f} giây** nữa nhé.")

    elif isinstance(error, commands.MissingRequiredArgument):

        await err_emb(ctx, "Bé nhập thiếu thông tin gì rồi, gõ `/help` xem lại nhé!")

    elif isinstance(error, commands.CheckFailure):

        await err_emb(ctx, "Bé không có quyền dùng lệnh này đâu nha!")

@bot.event

async def on_ready():

    print(f"✅ {bot.user} ĐÃ SẴN SÀNG PHỤC VỤ CÁC BÉ!")

if TOKEN:

    bot.run(TOKEN)

else:

    print("❌ Lỗi: Không tìm thấy DISCORD_TOKEN trong file .env")

