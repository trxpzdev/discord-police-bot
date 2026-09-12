import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# Charger les variables d'environnement
load_dotenv()

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot connecté en tant que {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'🔄 {len(synced)} commande(s) synchronisée(s)')
    except Exception as e:
        print(f'❌ Erreur lors de la synchronisation: {e}')
        import traceback
        traceback.print_exc()

# Charger les cogs (modules)
async def load_cogs():
    cogs_dir = './cogs'
    if not os.path.exists(cogs_dir):
        print(f'❌ Le dossier {cogs_dir} n\'existe pas!')
        return
    
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'📦 Cog chargé: {filename}')
            except Exception as e:
                print(f'❌ Erreur lors du chargement de {filename}: {e}')
                import traceback
                traceback.print_exc()

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    asyncio.run(main())
