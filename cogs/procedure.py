import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

class Procedure(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/procedures.json'
        self.ensure_data_file()

    def ensure_data_file(self):
        """Crée le fichier de données s'il n'existe pas"""
        if not os.path.exists('data'):
            os.makedirs('data')
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({}, f)

    def load_procedures(self):
        """Charge les procédures depuis le fichier JSON"""
        with open(self.data_file, 'r') as f:
            return json.load(f)

    def save_procedures(self, data):
        """Sauvegarde les procédures dans le fichier JSON"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    @app_commands.command(name="setup_procedure", description="Configurer le salon de procédure")
    async def setup_procedure(self, interaction: discord.Interaction):
        """Configure le salon de procédure avec un bouton"""
        # Créer l'embed avec le bouton
        embed = discord.Embed(
            title="🚔 Système de Procédure d'Arrestation",
            description="Cliquez sur le bouton ci-dessous pour commencer une nouvelle procédure d'arrestation.",
            color=discord.Color.blue()
        )
        embed.add_field(name="📋 Processus", value="""
1️⃣ Cliquez sur le bouton
2️⃣ Remplissez le formulaire
3️⃣ Uploadez une photo du criminel
4️⃣ Procédure enregistrée ✅
        """, inline=False)
        embed.set_footer(text="Système de Procédure Police")
        embed.timestamp = datetime.now()

        # Envoyer l'embed avec le bouton
        view = ProcedureView()
        await interaction.response.send_message(embed=embed, view=view)
        await interaction.followup.send("✅ Salon de procédure configuré!", ephemeral=True)

class ProcedureView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Commencer la procédure", style=discord.ButtonStyle.green, emoji="🚔")
    async def start_procedure(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ouvre un modal pour commencer la procédure"""
        await interaction.response.send_modal(ProcedureModal())

class ProcedureModal(discord.ui.Modal, title="Procédure d'Arrestation"):
    # Champs du formulaire
    nom = discord.ui.TextInput(
        label="Nom du criminel",
        placeholder="Entrez le nom...",
        required=True,
        max_length=100
    )
    
    prenom = discord.ui.TextInput(
        label="Prénom du criminel",
        placeholder="Entrez le prénom...",
        required=True,
        max_length=100
    )
    
    plaque = discord.ui.TextInput(
        label="Plaque du véhicule",
        placeholder="Ex: ABC-123-XYZ",
        required=True,
        max_length=50
    )
    
    motif = discord.ui.TextInput(
        label="Motif de l'arrestation",
        placeholder="Décrivez le motif...",
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Traite la soumission du formulaire"""
        # Envoyer un message pour demander la photo
        embed = discord.Embed(
            title="📸 Uploadez une photo",
            description="Veuillez envoyer une photo du criminel dans le prochain message.",
            color=discord.Color.orange()
        )
        
        view = PhotoWaitView(
            nom=self.nom.value,
            prenom=self.prenom.value,
            plaque=self.plaque.value,
            motif=self.motif.value,
            user=interaction.user,
            bot=interaction.client
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class PhotoWaitView(discord.ui.View):
    def __init__(self, nom: str, prenom: str, plaque: str, motif: str, user: discord.User, bot):
        super().__init__(timeout=600)  # 10 minutes timeout
        self.nom = nom
        self.prenom = prenom
        self.plaque = plaque
        self.motif = motif
        self.user = user
        self.bot = bot
        self.photo_url = None
        self.waiting_for_photo = True

    @discord.ui.button(label="Photo uploadée", style=discord.ButtonStyle.green, emoji="✅")
    async def photo_uploaded(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirme que la photo a été uploadée"""
        # Chercher la photo dans les messages récents
        channel = interaction.channel
        
        # Récupérer les messages récents
        async for message in channel.history(limit=5):
            if message.author == self.user and message.attachments:
                # Trouver une image
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image'):
                        self.photo_url = attachment.url
                        await self.save_procedure(interaction)
                        return
        
        # Pas de photo trouvée
        await interaction.response.send_message(
            "❌ Aucune photo trouvée. Veuillez envoyer une photo d'abord!",
            ephemeral=True
        )

    async def save_procedure(self, interaction: discord.Interaction):
        """Sauvegarde la procédure et affiche un résumé"""
        
        # Créer l'ID unique pour la procédure
        procedure_id = f"{self.user.id}_{datetime.now().timestamp()}"
        
        # Récupérer le cog Procedure
        proc_cog = interaction.client.get_cog("Procedure")
        
        procedures = proc_cog.load_procedures()
        procedures[procedure_id] = {
            'id': procedure_id,
            'officier': self.user.name,
            'officier_id': self.user.id,
            'nom': self.nom,
            'prenom': self.prenom,
            'plaque': self.plaque,
            'motif': self.motif,
            'photo_url': self.photo_url,
            'date': datetime.now().isoformat(),
            'status': 'en_cours'
        }
        proc_cog.save_procedures(procedures)
        
        # Créer l'embed de confirmation
        embed = discord.Embed(
            title="✅ Procédure enregistrée",
            description="La procédure d'arrestation a été créée avec succès!",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 Criminel", value=f"{self.prenom} {self.nom}", inline=False)
        embed.add_field(name="🚗 Plaque du véhicule", value=self.plaque, inline=True)
        embed.add_field(name="📋 Motif", value=self.motif, inline=False)
        embed.add_field(name="👮 Officier", value=interaction.user.mention, inline=True)
        embed.add_field(name="🆔 ID Procédure", value=f"`{procedure_id}`", inline=False)
        
        if self.photo_url:
            embed.add_field(name="📸 Photo", value="✅ Uploadée avec succès", inline=False)
            embed.set_image(url=self.photo_url)
        
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Procedure(bot))
