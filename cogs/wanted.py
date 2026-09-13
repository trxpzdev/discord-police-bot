import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

class Wanted(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/wanted.json'
        self.config_file = 'data/config.json'
        self.ensure_data_file()

    def ensure_data_file(self):
        """Crée les fichiers de données s'ils n'existent pas"""
        if not os.path.exists('data'):
            os.makedirs('data')
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({}, f)
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f:
                json.dump({"wanted_channel_id": None}, f)

    def load_wanted(self):
        """Charge la liste des personnes recherchées"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_wanted(self, data):
        """Sauvegarde la liste des personnes recherchées"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load_config(self):
        """Charge la configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return {"wanted_channel_id": None}

    def save_config(self, data):
        """Sauvegarde la configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def has_required_role(self, member: discord.Member) -> bool:
        """
        Vérifie si le membre a l'un des rôles requis
        À modifier avec vos vrais rôles (voir les noms des rôles Discord)
        Rôles actuels: "Commandant", "Chef de Police"
        """
        required_roles = ["Commandant", "Chef de Police"]
        member_roles = [role.name for role in member.roles]
        
        for role in required_roles:
            if role in member_roles:
                return True
        return False

    @app_commands.command(name="config_wanted_channel", description="Configurer le salon #wanted")
    @app_commands.describe(channel="Le salon où envoyer les avis de recherche")
    async def config_wanted_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Configure le salon où seront envoyés les avis de recherche"""
        # Vérifier les permissions (admin ou rôle élevé)
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission refusée",
                description="Seul un administrateur peut configurer le salon.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        config = self.load_config()
        config["wanted_channel_id"] = channel.id
        self.save_config(config)

        embed = discord.Embed(
            title="✅ Salon configuré",
            description=f"Les avis de recherche seront envoyés dans {channel.mention}",
            color=discord.Color.green()
        )
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="add_wanted", description="Ajouter une personne à la liste des recherchés")
    @app_commands.describe(
        joueur="La personne recherchée",
        motif="Motif de la recherche",
        danger_level="Niveau de danger (Faible/Moyen/Élevé/Très Élevé)",
        plaques="Les plaques de ses véhicules (séparées par des virgules)"
    )
    async def add_wanted(self, interaction: discord.Interaction, joueur: discord.User, motif: str, danger_level: str, plaques: str):
        """Ajouter une personne à la liste des recherchés avec photo"""
        
        # Vérifier le rôle de l'officier
        if not self.has_required_role(interaction.user):
            embed = discord.Embed(
                title="❌ Permission refusée",
                description="Seuls les hauts grades (Commandant, Chef de Police) peuvent ajouter des recherchés.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Demander la photo
        embed = discord.Embed(
            title="📸 Photo requise",
            description=f"Veuillez envoyer une photo du visage de {joueur.mention} dans le prochain message.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Suspect", value=f"{joueur.mention}", inline=False)
        embed.add_field(name="Motif", value=motif, inline=False)
        embed.add_field(name="Niveau de danger", value=danger_level, inline=True)
        embed.add_field(name="Plaques", value=plaques if plaques else "Non renseignées", inline=True)

        view = PhotoWantedView(
            joueur=joueur,
            motif=motif,
            danger_level=danger_level,
            plaques=plaques,
            officer=interaction.user,
            bot=interaction.client
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="wanted", description="Afficher la liste des personnes recherchées")
    async def wanted(self, interaction: discord.Interaction):
        """Affiche la liste des personnes recherchées"""
        wanted_list = self.load_wanted()

        if not wanted_list:
            embed = discord.Embed(
                title="🚨 Liste des recherchés",
                description="Aucune personne actuellement recherchée.",
                color=discord.Color.green()
            )
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        embed = discord.Embed(
            title="🚨 PERSONNES RECHERCHÉES",
            description=f"Total: {len(wanted_list)} personne(s)",
            color=discord.Color.red()
        )

        for user_id, info in wanted_list.items():
            field_value = f"""
**Discord**: {info.get('name', 'N/A')}
**RP**: {info.get('rp_name', 'Non renseigné')}
**Motif**: {info.get('reason', 'N/A')}
**Danger**: {info.get('danger_level', 'Non défini')}
**Plaques**: {info.get('plaques', 'Non renseignées')}
**Officier**: {info.get('officer', 'N/A')}
**Date**: {info.get('date', 'N/A')[:10]}
            """
            embed.add_field(
                name=f"📌 {info.get('rp_name', info.get('name', 'Inconnu'))}",
                value=field_value,
                inline=False
            )

        embed.set_footer(text=f"Consulté par {interaction.user.name} - {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="remove_wanted", description="Retirer une personne de la liste des recherchés")
    @app_commands.describe(joueur="La personne à retirer")
    async def remove_wanted(self, interaction: discord.Interaction, joueur: discord.User):
        """Retirer une personne de la liste des recherchés"""
        
        # Vérifier le rôle de l'officier
        if not self.has_required_role(interaction.user):
            embed = discord.Embed(
                title="❌ Permission refusée",
                description="Seuls les hauts grades peuvent retirer des recherchés.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        wanted_list = self.load_wanted()
        player_id = str(joueur.id)

        if player_id not in wanted_list:
            embed = discord.Embed(
                title="❌ Non trouvé",
                description=f"{joueur.mention} ne figure pas sur la liste des recherchés.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Créer une confirmation
        view = ConfirmRemoveView(joueur, player_id, self)
        embed = discord.Embed(
            title="⚠️ Confirmation",
            description=f"Êtes-vous sûr de vouloir retirer {joueur.mention} de la liste des recherchés ?",
            color=discord.Color.orange()
        )
        embed.add_field(name="Suspect", value=wanted_list[player_id].get('rp_name', joueur.name), inline=False)
        embed.add_field(name="Motif", value=wanted_list[player_id].get('reason', 'N/A'), inline=False)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class PhotoWantedView(discord.ui.View):
    def __init__(self, joueur: discord.User, motif: str, danger_level: str, plaques: str, officer: discord.User, bot):
        super().__init__(timeout=600)  # 10 minutes
        self.joueur = joueur
        self.motif = motif
        self.danger_level = danger_level
        self.plaques = plaques
        self.officer = officer
        self.bot = bot
        self.photo_url = None

    @discord.ui.button(label="Photo uploadée", style=discord.ButtonStyle.green, emoji="✅")
    async def photo_uploaded(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirme que la photo a été uploadée"""
        channel = interaction.channel

        # Chercher la photo dans les messages récents
        async for message in channel.history(limit=10):
            if message.author == self.officer and message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image'):
                        self.photo_url = attachment.url
                        await self.save_wanted(interaction)
                        return

        # Pas de photo trouvée
        await interaction.response.send_message(
            "❌ Aucune photo trouvée. Veuillez envoyer une photo d'abord!",
            ephemeral=True
        )

    async def save_wanted(self, interaction: discord.Interaction):
        """Sauvegarde la personne recherchée et envoie le message dans #wanted"""
        wanted_cog = interaction.client.get_cog("Wanted")
        wanted_list = wanted_cog.load_wanted()
        config = wanted_cog.load_config()

        player_id = str(self.joueur.id)

        # Récupérer le nom RP depuis records.json
        try:
            with open('data/records.json', 'r') as f:
                records = json.load(f)
                rp_name = records.get(player_id, {}).get('rp_name', 'Non renseigné')
                rp_prenom = records.get(player_id, {}).get('rp_prenom', 'Non renseigné')
                rp_full = f"{rp_prenom} {rp_name}"
        except:
            rp_full = "Non renseigné"

        # Ajouter à la liste
        wanted_list[player_id] = {
            'name': self.joueur.name,
            'rp_name': rp_full,
            'reason': self.motif,
            'danger_level': self.danger_level,
            'plaques': self.plaques if self.plaques else "Non renseignées",
            'officer': self.officer.name,
            'date': datetime.now().isoformat(),
            'photo_url': self.photo_url
        }

        wanted_cog.save_wanted(wanted_list)

        # Envoyer le message dans le salon #wanted
        wanted_channel_id = config.get('wanted_channel_id')
        if wanted_channel_id:
            try:
                wanted_channel = interaction.client.get_channel(wanted_channel_id)
                if wanted_channel:
                    embed = discord.Embed(
                        title="🚨 AVIS DE RECHERCHE 🚨",
                        description=f"Une nouvelle personne a été ajoutée à la liste des recherchés.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="👤 Discord", value=self.joueur.mention, inline=False)
                    embed.add_field(name="📝 Nom RP", value=rp_full, inline=False)
                    embed.add_field(name="⚠️ Motif", value=self.motif, inline=False)
                    embed.add_field(name="🔴 Niveau de danger", value=self.danger_level, inline=True)
                    embed.add_field(name="🚗 Véhicules", value=self.plaques if self.plaques else "Non renseignés", inline=True)
                    embed.add_field(name="👮 Officier", value=self.officer.mention, inline=False)
                    embed.set_image(url=self.photo_url)
                    embed.timestamp = datetime.now()
                    embed.set_footer(text=f"ID: {player_id}")

                    await wanted_channel.send(embed=embed)
            except Exception as e:
                print(f"Erreur lors de l'envoi du message dans #wanted: {e}")

        # Confirmation
        embed = discord.Embed(
            title="✅ Avis de recherche créé",
            description=f"{self.joueur.mention} a été ajouté à la liste des recherchés.",
            color=discord.Color.green()
        )
        embed.add_field(name="Suspect", value=rp_full, inline=False)
        embed.add_field(name="Motif", value=self.motif, inline=False)
        embed.add_field(name="Niveau de danger", value=self.danger_level, inline=True)
        embed.add_field(name="Plaques", value=self.plaques if self.plaques else "Non renseignées", inline=True)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed, ephemeral=True)

class ConfirmRemoveView(discord.ui.View):
    def __init__(self, joueur: discord.User, player_id: str, wanted_cog):
        super().__init__(timeout=60)
        self.joueur = joueur
        self.player_id = player_id
        self.wanted_cog = wanted_cog

    @discord.ui.button(label="Confirmer", style=discord.ButtonStyle.red, emoji="🔴")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirme la suppression"""
        wanted_list = self.wanted_cog.load_wanted()

        if self.player_id in wanted_list:
            del wanted_list[self.player_id]
            self.wanted_cog.save_wanted(wanted_list)

            embed = discord.Embed(
                title="✅ Supprimé",
                description=f"{self.joueur.mention} a été retiré de la liste des recherchés.",
                color=discord.Color.green()
            )
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="⚪")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Annule la suppression"""
        embed = discord.Embed(
            title="❌ Annulé",
            description="La suppression a été annulée.",
            color=discord.Color.greyple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Wanted(bot))
