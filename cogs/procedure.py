import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from typing import Optional

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
        embed.add_field(name="📋 Informations à fournir", value="""
• 📸 Image de l'arrestation
• 👤 Nom et prénom du suspect
• 🚗 Plaque du véhicule
• 📝 Motif de l'arrestation
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
        label="Nom du suspect",
        placeholder="Entrez le nom...",
        required=True,
        max_length=100
    )
    
    prenom = discord.ui.TextInput(
        label="Prénom du suspect",
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
        # Créer une vue pour demander l'image
        view = ImageUploadView(
            nom=self.nom.value,
            prenom=self.prenom.value,
            plaque=self.plaque.value,
            motif=self.motif.value,
            user=interaction.user,
            bot=interaction.client
        )
        
        embed = discord.Embed(
            title="📸 Téléchargez l'image",
            description="Veuillez télécharger l'image de l'arrestation en réponse à ce message.",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ImageUploadView(discord.ui.View):
    def __init__(self, nom: str, prenom: str, plaque: str, motif: str, user: discord.User, bot):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.nom = nom
        self.prenom = prenom
        self.plaque = plaque
        self.motif = motif
        self.user = user
        self.bot = bot
        self.image_url = None

    @discord.ui.button(label="Continuer sans image", style=discord.ButtonStyle.secondary, emoji="⏭️")
    async def skip_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Passe sans image"""
        self.image_url = None
        await self.save_procedure(interaction)

    @discord.ui.button(label="Coller l'URL de l'image", style=discord.ButtonStyle.primary, emoji="📸")
    async def upload_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ouvre un dialogue pour télécharger l'image"""
        await interaction.response.send_modal(ImageModal(self))

class ImageModal(discord.ui.Modal, title="Télécharger l'image"):
    image_url = discord.ui.TextInput(
        label="URL de l'image",
        placeholder="Collez l'URL de l'image...",
        required=True,
        max_length=500
    )

    def __init__(self, parent_view: ImageUploadView):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        """Traite l'URL de l'image"""
        self.parent_view.image_url = self.image_url.value
        await self.parent_view.save_procedure(interaction)

async def save_procedure(self, interaction: discord.Interaction):
    """Sauvegarde la procédure et affiche un résumé"""
    
    # Créer l'ID unique pour la procédure
    procedure_id = f"{interaction.user.id}_{datetime.now().timestamp()}"
    
    # Récupérer le cog Procedure
    proc_cog = interaction.client.get_cog("Procedure")
    
    procedures = proc_cog.load_procedures()
    procedures[procedure_id] = {
        'id': procedure_id,
        'officier': interaction.user.name,
        'officier_id': interaction.user.id,
        'nom': self.nom,
        'prenom': self.prenom,
        'plaque': self.plaque,
        'motif': self.motif,
        'image_url': self.image_url,
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
    embed.add_field(name="👤 Suspect", value=f"{self.prenom} {self.nom}", inline=False)
    embed.add_field(name="🚗 Plaque", value=self.plaque, inline=True)
    embed.add_field(name="📋 Motif", value=self.motif, inline=False)
    embed.add_field(name="👮 Officier", value=interaction.user.mention, inline=True)
    embed.add_field(name="🆔 ID Procédure", value=f"`{procedure_id}`", inline=False)
    
    if self.image_url:
        embed.add_field(name="📸 Image", value="✅ Téléchargée", inline=True)
        try:
            embed.set_image(url=self.image_url)
        except:
            embed.add_field(name="⚠️ Erreur", value="Impossible de charger l'image", inline=False)
    else:
        embed.add_field(name="📸 Image", value="❌ Non fournie", inline=True)
    
    embed.timestamp = datetime.now()
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Ajouter la méthode au ImageUploadView
ImageUploadView.save_procedure = save_procedure

async def setup(bot):
    await bot.add_cog(Procedure(bot))
