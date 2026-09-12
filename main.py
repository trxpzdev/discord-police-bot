import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot connecté en tant que {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'🔄 {len(synced)} commande(s) synchronisée(s)')
    except Exception as e:
        print(f'❌ Erreur lors de la synchronisation: {e}')

# Charger les cogs (modules)
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'📦 Cog chargé: {filename}')

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
