import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

class Search(commands.Cog):
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
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_records(self, data):
        """Sauvegarde les dossiers dans le fichier JSON"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def calculate_danger_level(self, arrests: int, fines: int, warnings: int) -> tuple:
        """
        Calcule le niveau de dangerosité basé sur l'historique
        Retourne: (niveau, emoji, couleur)
        """
        score = (arrests * 3) + (fines * 1) + (warnings * 0.5)
        
        if score == 0:
            return ("Bas", "🟢", discord.Color.green())
        elif score < 5:
            return ("Faible", "🟡", discord.Color.yellow())
        elif score < 15:
            return ("Moyen", "🟠", discord.Color.orange())
        elif score < 30:
            return ("Élevé", "🔴", discord.Color.red())
        else:
            return ("Très Élevé", "🔴🔴", discord.Color.dark_red())

    @app_commands.command(name="search", description="Rechercher un citoyen dans la base")
    @app_commands.describe(joueur="Le citoyen à rechercher")
    async def search(self, interaction: discord.Interaction, joueur: discord.User):
        """Recherche un citoyen et affiche son dossier complet"""
        records = self.load_records()
        player_id = str(joueur.id)

        # Vérifier si le citoyen existe dans la base
        if player_id not in records:
            embed = discord.Embed(
                title="❌ Aucun dossier trouvé",
                description=f"Le citoyen **{joueur.name}** n'a aucun dossier dans la base de données.",
                color=discord.Color.greyple()
            )
            embed.set_thumbnail(url=joueur.display_avatar.url)
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        record = records[player_id]

        # Compter les infractions
        num_arrests = len(record.get('arrests', []))
        num_fines = len(record.get('fines', []))
        num_warnings = len(record.get('warnings', []))
        total_fines = sum(f.get('amount', 0) for f in record.get('fines', []))

        # Calculer le niveau de dangerosité
        danger_level, danger_emoji, danger_color = self.calculate_danger_level(
            num_arrests, num_fines, num_warnings
        )

        # Créer l'embed principal
        embed = discord.Embed(
            title=f"🔍 DOSSIER CRIMINEL - {joueur.name}",
            description=f"Recherche effectuée par {interaction.user.mention}",
            color=danger_color
        )

        # Avatar
        embed.set_thumbnail(url=joueur.display_avatar.url)

        # Statut
        status = record.get('status', 'libre')
        status_emoji = "🚨" if status == 'arrêté' else "✅"
        embed.add_field(
            name="👤 Statut",
            value=f"{status_emoji} **{status.upper()}**",
            inline=True
        )

        # Niveau de dangerosité
        embed.add_field(
            name="⚠️ Niveau de Dangerosité",
            value=f"{danger_emoji} **{danger_level}**",
            inline=True
        )

        # Discord ID
        embed.add_field(
            name="🆔 Discord ID",
            value=f"`{player_id}`",
            inline=True
        )

        # Nom RP (si disponible)
        rp_name = record.get('rp_name', 'Non renseigné')
        rp_prenom = record.get('rp_prenom', 'Non renseigné')
        embed.add_field(
            name="📝 Nom RP",
            value=f"{rp_prenom} {rp_name}",
            inline=False
        )

        # Section Arrestations
        arrests_text = f"**📊 Total: {num_arrests} arrestations**\n"
        if record.get('arrests'):
            arrests_text += "**3 plus récentes:**\n"
            for i, arrest in enumerate(record['arrests'][-3:], 1):
                date = arrest.get('date', 'N/A')[:10]  # Extraire la date
                arrests_text += f"{i}. {arrest.get('reason', 'N/A')} - {date}\n"
        else:
            arrests_text = "✅ Aucune arrestation"

        embed.add_field(
            name="🚨 Arrestations",
            value=arrests_text,
            inline=False
        )

        # Section Amendes
        fines_text = f"**💰 Total: {total_fines}€ ({num_fines} amende(s))**\n"
        if record.get('fines'):
            fines_text += "**3 plus récentes:**\n"
            for i, fine in enumerate(record['fines'][-3:], 1):
                date = fine.get('date', 'N/A')[:10]
                fines_text += f"{i}. {fine.get('amount', 0)}€ - {fine.get('reason', 'N/A')} - {date}\n"
        else:
            fines_text = "✅ Aucune amende"

        embed.add_field(
            name="💵 Amendes",
            value=fines_text,
            inline=False
        )

        # Section Avertissements
        warnings_text = f"**📋 Total: {num_warnings} avertissement(s)**\n"
        if record.get('warnings'):
            warnings_text += "**3 plus récents:**\n"
            for i, warning in enumerate(record['warnings'][-3:], 1):
                date = warning.get('date', 'N/A')[:10]
                warnings_text += f"{i}. {warning.get('reason', 'N/A')} - {date}\n"
        else:
            warnings_text = "✅ Aucun avertissement"

        embed.add_field(
            name="⚠️ Avertissements",
            value=warnings_text,
            inline=False
        )

        # Véhicules associés
        vehicles = record.get('vehicles', [])
        if vehicles:
            vehicles_text = ", ".join(vehicles)
        else:
            vehicles_text = "❌ Aucun"
        embed.add_field(
            name="🚗 Véhicules Associés",
            value=vehicles_text,
            inline=False
        )

        # Mandats éventuels
        warrants = record.get('warrants', [])
        if warrants:
            warrants_text = f"**{len(warrants)} mandat(s) actif(s)**\n"
            for warrant in warrants[:3]:
                warrants_text += f"• {warrant.get('reason', 'N/A')}\n"
        else:
            warrants_text = "✅ Aucun mandat actif"
        embed.add_field(
            name="⚖️ Mandats",
            value=warrants_text,
            inline=False
        )

        # Affaires associées
        cases = record.get('cases', [])
        if cases:
            cases_text = f"**{len(cases)} affaire(s) associée(s)**"
        else:
            cases_text = "✅ Aucune affaire"
        embed.add_field(
            name="🕵️ Affaires",
            value=cases_text,
            inline=False
        )

        # Footer
        embed.set_footer(text=f"Recherche effectuée le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="set_rp_name", description="Définir le nom RP d'un citoyen")
    @app_commands.describe(
        joueur="Le citoyen",
        prenom="Prénom RP",
        nom="Nom RP"
    )
    async def set_rp_name(self, interaction: discord.Interaction, joueur: discord.User, prenom: str, nom: str):
        """Définit le nom RP d'un citoyen"""
        records = self.load_records()
        player_id = str(joueur.id)

        # Créer le dossier s'il n'existe pas
        if player_id not in records:
            records[player_id] = {
                'name': joueur.name,
                'arrests': [],
                'fines': [],
                'warnings': [],
                'status': 'libre',
                'rp_name': nom,
                'rp_prenom': prenom,
                'vehicles': [],
                'warrants': [],
                'cases': []
            }
        else:
            records[player_id]['rp_name'] = nom
            records[player_id]['rp_prenom'] = prenom

        self.save_records(records)

        embed = discord.Embed(
            title="✅ Nom RP défini",
            description=f"Le nom RP de {joueur.mention} a été enregistré.",
            color=discord.Color.green()
        )
        embed.add_field(name="Nom RP", value=f"{prenom} {nom}", inline=False)
        embed.add_field(name="Discord", value=joueur.name, inline=True)
        embed.add_field(name="Officier", value=interaction.user.mention, inline=True)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Search(bot))
