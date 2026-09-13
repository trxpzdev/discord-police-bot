import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
import uuid

class Warrants(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/warrants.json'
        self.ensure_data_file()

    def ensure_data_file(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"warrants_list": []}, f, indent=2)

    def load_warrants(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"warrants_list": []}

    def save_warrants(self, data):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def has_required_role(self, member: discord.Member) -> bool:
        required_roles = ["Commandant", "Chef de Police", "Juge"]
        member_roles = [role.name for role in member.roles]
        for role in required_roles:
            if role in member_roles:
                return True
        return False

    def has_cancel_permission(self, member: discord.Member) -> bool:
        required_roles = ["Juge", "Commandant"]
        member_roles = [role.name for role in member.roles]
        for role in required_roles:
            if role in member_roles:
                return True
        return member.guild_permissions.administrator

    @app_commands.command(name="warrant_create", description="Créer un mandat d'arrêt")
    @app_commands.describe(
        joueur="La personne visée par le mandat",
        raison="Raison du mandat",
        type_mandat="Type: Arrestation, Perquisition, Saisie"
    )
    async def warrant_create(self, interaction: discord.Interaction, joueur: discord.User, raison: str, type_mandat: str):
        if not self.has_required_role(interaction.user):
            embed = discord.Embed(
                title="❌ Permission refusée",
                description="Seuls les hauts grades (Commandant, Chef de Police, Juge) peuvent créer des mandats.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        valid_types = ["Arrestation", "Perquisition", "Saisie"]
        if type_mandat not in valid_types:
            embed = discord.Embed(
                title="❌ Type invalide",
                description=f"Types valides: {', '.join(valid_types)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        data = self.load_warrants()
        
        for warrant in data["warrants_list"]:
            if warrant.get("player_id") == str(joueur.id) and warrant.get("status") == "Actif":
                embed = discord.Embed(
                    title="❌ Mandat existant",
                    description=f"Un mandat actif existe déjà pour {joueur.mention}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        warrant_entry = {
            "id": str(uuid.uuid4()),
            "player_id": str(joueur.id),
            "player_name": joueur.name,
            "type": type_mandat,
            "reason": raison,
            "officer": interaction.user.name,
            "officer_id": str(interaction.user.id),
            "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "status": "Actif",
            "executed": False,
            "executed_at": None,
            "executed_by": None
        }

        data["warrants_list"].append(warrant_entry)
        self.save_warrants(data)

        embed = discord.Embed(
            title="📜 Mandat créé",
            description=f"Mandat d'arrêt créé pour **{joueur.name}**",
            color=discord.Color.gold()
        )
        embed.add_field(name="Type", value=type_mandat, inline=True)
        embed.add_field(name="Raison", value=raison, inline=False)
        embed.add_field(name="Autorité", value=interaction.user.mention, inline=False)
        embed.add_field(name="ID Mandat", value=warrant_entry["id"], inline=False)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warrant_list", description="Afficher la liste des mandats actifs")
    async def warrant_list(self, interaction: discord.Interaction):
        data = self.load_warrants()
        active_warrants = [w for w in data["warrants_list"] if w.get("status") == "Actif"]

        if not active_warrants:
            embed = discord.Embed(
                title="📜 Mandats",
                description="Aucun mandat actif",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title="📜 Mandats actifs",
            description=f"Total: **{len(active_warrants)}** mandat(s)",
            color=discord.Color.gold()
        )

        for warrant in active_warrants:
            status_icon = "🔴" if not warrant.get("executed") else "✅"
            field_value = f"**Type:** {warrant.get('type', 'N/A')}\n"
            field_value += f"**Raison:** {warrant.get('reason', 'N/A')}\n"
            field_value += f"**Créé par:** {warrant.get('officer', 'N/A')}\n"
            field_value += f"**Date:** {warrant.get('created_at', 'N/A')}"
            
            embed.add_field(
                name=f"{status_icon} {warrant.get('player_name', 'Unknown')}",
                value=field_value,
                inline=False
            )

        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warrant_view", description="Afficher les détails d'un mandat")
    @app_commands.describe(joueur="La personne concernée")
    async def warrant_view(self, interaction: discord.Interaction, joueur: discord.User):
        data = self.load_warrants()
        
        warrant = None
        for w in data["warrants_list"]:
            if w.get("player_id") == str(joueur.id) and w.get("status") == "Actif":
                warrant = w
                break

        if not warrant:
            embed = discord.Embed(
                title="❌ Mandat non trouvé",
                description=f"Aucun mandat actif pour {joueur.mention}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📜 Mandat - {warrant.get('player_name')}",
            color=discord.Color.gold()
        )
        embed.add_field(name="🆔 ID", value=warrant.get("id", "N/A"), inline=False)
        embed.add_field(name="📋 Type", value=warrant.get("type", "N/A"), inline=True)
        embed.add_field(name="⚠️ Raison", value=warrant.get("reason", "N/A"), inline=False)
        embed.add_field(name="👮 Créé par", value=warrant.get("officer", "N/A"), inline=True)
        embed.add_field(name="📅 Date", value=warrant.get("created_at", "N/A"), inline=True)
        embed.add_field(name="📊 Statut", value=warrant.get("status", "N/A"), inline=True)
        
        if warrant.get("executed"):
            embed.add_field(name="✅ Exécuté le", value=warrant.get("executed_at", "N/A"), inline=True)
            embed.add_field(name="✅ Exécuté par", value=warrant.get("executed_by", "N/A"), inline=True)

        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warrant_cancel", description="Annuler un mandat")
    @app_commands.describe(joueur="La personne visée")
    async def warrant_cancel(self, interaction: discord.Interaction, joueur: discord.User):
        if not self.has_cancel_permission(interaction.user):
            embed = discord.Embed(
                title="❌ Permission refusée",
                description="Seul un Juge ou Admin peut annuler des mandats.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        data = self.load_warrants()
        
        for warrant in data["warrants_list"]:
            if warrant.get("player_id") == str(joueur.id) and warrant.get("status") == "Actif":
                warrant["status"] = "Annulé"
                warrant["canceled_at"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                warrant["canceled_by"] = interaction.user.name
                
                self.save_warrants(data)

                embed = discord.Embed(
                    title="✅ Mandat annulé",
                    description=f"Mandat annulé pour **{joueur.name}**",
                    color=discord.Color.green()
                )
                embed.add_field(name="Annulé par", value=interaction.user.mention, inline=False)
                embed.timestamp = datetime.now()

                await interaction.response.send_message(embed=embed)
                return

        embed = discord.Embed(
            title="❌ Non trouvé",
            description=f"Aucun mandat actif pour {joueur.mention}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Warrants(bot))
