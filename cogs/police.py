import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

class Police(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/records.json'
        self.ensure_data_file()

    def ensure_data_file(self):
        """Crée le fichier de données s'il n'existe pas"""
        if not os.path.exists('data'):
            os.makedirs('data')
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({}, f)

    def load_records(self):
        """Charge les dossiers depuis le fichier JSON"""
        with open(self.data_file, 'r') as f:
            return json.load(f)

    def save_records(self, data):
        """Sauvegarde les dossiers dans le fichier JSON"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    @app_commands.command(name="arrest", description="Arrêter un joueur")
    @app_commands.describe(
        player="Le joueur à arrêter",
        reason="Raison de l'arrestation"
    )
    async def arrest(self, interaction: discord.Interaction, player: discord.User, reason: str):
        """Arrête un joueur et enregistre l'arrestation"""
        records = self.load_records()
        player_id = str(player.id)

        if player_id not in records:
            records[player_id] = {
                'name': player.name,
                'arrests': [],
                'fines': [],
                'warnings': [],
                'status': 'libre'
            }

        # Ajouter l'arrestation
        arrest_record = {
            'date': datetime.now().isoformat(),
            'reason': reason,
            'officer': interaction.user.name
        }
        records[player_id]['arrests'].append(arrest_record)
        records[player_id]['status'] = 'arrêté'

        self.save_records(records)

        embed = discord.Embed(
            title="🚨 Arrestation",
            description=f"{player.mention} a été arrêté(e)!",
            color=discord.Color.red()
        )
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.add_field(name="Officier", value=interaction.user.mention, inline=False)
        embed.add_field(name="Total arrestations", value=len(records[player_id]['arrests']), inline=True)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="release", description="Libérer un joueur")
    @app_commands.describe(player="Le joueur à libérer")
    async def release(self, interaction: discord.Interaction, player: discord.User):
        """Libère un joueur arrêté"""
        records = self.load_records()
        player_id = str(player.id)

        if player_id not in records:
            await interaction.response.send_message(
                f"❌ Aucun dossier trouvé pour {player.mention}",
                ephemeral=True
            )
            return

        records[player_id]['status'] = 'libre'
        self.save_records(records)

        embed = discord.Embed(
            title="✅ Libération",
            description=f"{player.mention} a été libéré(e)!",
            color=discord.Color.green()
        )
        embed.add_field(name="Officier", value=interaction.user.mention, inline=False)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fine", description="Donner une amende")
    @app_commands.describe(
        player="Le joueur à verbaliser",
        amount="Montant de l'amende",
        reason="Raison de l'amende"
    )
    async def fine(self, interaction: discord.Interaction, player: discord.User, amount: int, reason: str):
        """Donne une amende à un joueur"""
        records = self.load_records()
        player_id = str(player.id)

        if player_id not in records:
            records[player_id] = {
                'name': player.name,
                'arrests': [],
                'fines': [],
                'warnings': [],
                'status': 'libre'
            }

        fine_record = {
            'date': datetime.now().isoformat(),
            'amount': amount,
            'reason': reason,
            'officer': interaction.user.name
        }
        records[player_id]['fines'].append(fine_record)
        total_fines = sum(f['amount'] for f in records[player_id]['fines'])

        self.save_records(records)

        embed = discord.Embed(
            title="💰 Amende",
            description=f"{player.mention} a reçu une amende!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Montant", value=f"{amount}€", inline=True)
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.add_field(name="Officier", value=interaction.user.mention, inline=False)
        embed.add_field(name="Total amendes", value=f"{total_fines}€", inline=True)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warn", description="Avertir un joueur")
    @app_commands.describe(
        player="Le joueur à avertir",
        reason="Raison de l'avertissement"
    )
    async def warn(self, interaction: discord.Interaction, player: discord.User, reason: str):
        """Donne un avertissement à un joueur"""
        records = self.load_records()
        player_id = str(player.id)

        if player_id not in records:
            records[player_id] = {
                'name': player.name,
                'arrests': [],
                'fines': [],
                'warnings': [],
                'status': 'libre'
            }

        warning_record = {
            'date': datetime.now().isoformat(),
            'reason': reason,
            'officer': interaction.user.name
        }
        records[player_id]['warnings'].append(warning_record)

        self.save_records(records)

        embed = discord.Embed(
            title="⚠️ Avertissement",
            description=f"{player.mention} a reçu un avertissement!",
            color=discord.Color.orange()
        )
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.add_field(name="Officier", value=interaction.user.mention, inline=False)
        embed.add_field(name="Total avertissements", value=len(records[player_id]['warnings']), inline=True)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="record", description="Consulter le dossier d'un joueur")
    @app_commands.describe(player="Le joueur dont consulter le dossier")
    async def record(self, interaction: discord.Interaction, player: discord.User):
        """Affiche le dossier complet d'un joueur"""
        records = self.load_records()
        player_id = str(player.id)

        if player_id not in records:
            await interaction.response.send_message(
                f"📋 Aucun dossier trouvé pour {player.mention}. Casier vierge!",
                ephemeral=False
            )
            return

        record = records[player_id]

        embed = discord.Embed(
            title=f"📋 Dossier de {player.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=player.display_avatar.url)

        # Statut
        status_emoji = "🚨" if record['status'] == 'arrêté' else "✅"
        embed.add_field(name="Statut", value=f"{status_emoji} {record['status'].capitalize()}", inline=False)

        # Arrestations
        arrests_text = f"**Total: {len(record['arrests'])}**\n"
        if record['arrests']:
            for i, arrest in enumerate(record['arrests'][-3:], 1):
                arrests_text += f"\n{i}. {arrest['reason']} (par {arrest['officer']})"
        else:
            arrests_text = "Aucune arrestation"
        embed.add_field(name="🚨 Arrestations", value=arrests_text, inline=False)

        # Amendes
        total_fines = sum(f['amount'] for f in record['fines'])
        fines_text = f"**Total: {total_fines}€ ({len(record['fines'])} amende(s))**\n"
        if record['fines']:
            for i, fine in enumerate(record['fines'][-3:], 1):
                fines_text += f"\n{i}. {fine['amount']}€ - {fine['reason']}"
        else:
            fines_text = "Aucune amende"
        embed.add_field(name="💰 Amendes", value=fines_text, inline=False)

        # Avertissements
        warnings_text = f"**Total: {len(record['warnings'])}**\n"
        if record['warnings']:
            for i, warning in enumerate(record['warnings'][-3:], 1):
                warnings_text += f"\n{i}. {warning['reason']}"
        else:
            warnings_text = "Aucun avertissement"
        embed.add_field(name="⚠️ Avertissements", value=warnings_text, inline=False)

        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear_record", description="Effacer le dossier d'un joueur")
    @app_commands.describe(player="Le joueur dont effacer le dossier")
    async def clear_record(self, interaction: discord.Interaction, player: discord.User):
        """Efface complètement le dossier d'un joueur (Admin only)"""
        # Vérification des permissions (à adapter selon vos rôles)
        records = self.load_records()
        player_id = str(player.id)

        if player_id not in records:
            await interaction.response.send_message(
                f"❌ Aucun dossier trouvé pour {player.mention}",
                ephemeral=True
            )
            return

        del records[player_id]
        self.save_records(records)

        embed = discord.Embed(
            title="🗑️ Dossier supprimé",
            description=f"Le dossier de {player.mention} a été complètement effacé!",
            color=discord.Color.red()
        )
        embed.add_field(name="Effectué par", value=interaction.user.mention, inline=False)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Police(bot))
