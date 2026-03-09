import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')

class NurseryBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='k!', intents=intents, help_command=None)

    async def setup_hook(self):
        # Nạp các file trong thư mục cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        await self.tree.sync()

    async def on_ready(self):
        print(f'✅ {self.user.name} đã sẵn sàng bảo quản Kindgarden!')

bot = NurseryBot()
bot.run(TOKEN)
