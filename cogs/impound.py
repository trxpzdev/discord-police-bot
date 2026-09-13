import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
import uuid

class Impound(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/impounds.json'
        self.ensure_data_file()

    def ensure_data_file(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"impounded_list": []}, f, indent=2)

    def load_impounded(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"impounded_list": []}

    def save_impounded(self, data):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def has_police_role(self, member: discord.Member) -> bool:
        required_roles = ["Police", "Commandant", "Chef de Police"]
        member_roles = [role.name for role in member.roles]
        for role in required_roles:
            if role in member_roles:
                return True
        return False

    @app_commands.command(name="impound", description="Mettre un véhicule en fourrière")
    @app_commands.describe(plaque="La plaque du véhicule", raison="Raison de la mise en fourrière")
    async def impound(self, interaction: discord.Interaction, plaque: str, raison: str):
        if not self.has_police_role(interaction.user):
            embed = discord.Embed(title="❌ Permission refusée", description="Seuls les membres de la Police peuvent utiliser la fourrière.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        data = self.load_impounded()
        
        for impound in data["impounded_list"]:
            if impound.get("plaque").upper() == plaque.upper() and impound.get("status") == "Actif":
                embed = discord.Embed(title="❌ Déjà en fourrière", description=f"La plaque **{plaque}** est déjà en fourrière!", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        impound_entry = {
            "id": str(uuid.uuid4()),
            "plaque": plaque.upper(),
            "raison": raison,
            "officer": interaction.user.name,
            "officer_id": str(interaction.user.id),
            "impound_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "status": "Actif",
            "released": False,
            "released_at": None,
            "released_by": None
        }

        data["impounded_list"].append(impound_entry)
        self.save_impounded(data)

        embed = discord.Embed(title="🚛 Véhicule en fourrière", description=f"Plaque: **{plaque.upper()}**", color=discord.Color.red())
        embed.add_field(name="⚠️ Raison", value=raison, inline=False)
        embed.add_field(name="👮 Officier", value=interaction.user.mention, inline=False)
        embed.add_field(name="🆔 ID Impound", value=impound_entry["id"], inline=False)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="impound_list", description="Afficher la liste des véhicules en fourrière")
    async def impound_list(self, interaction: discord.Interaction):
        data = self.load_impounded()
        active_impounds = [i for i in data["impounded_list"] if i.get("status") == "Actif"]

        if not active_impounds:
            embed = discord.Embed(title="🚛 Fourrière", description="Aucun véhicule en fourrière", color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(title="🚛 Véhicules en fourrière", description=f"Total: **{len(active_impounds)}** véhicule(s)", color=discord.Color.red())

        for impound in active_impounds:
            field_value = f"**Raison:** {impound.get('raison', 'N/A')}\n"
            field_value += f"**Officier:** {impound.get('officer', 'N/A')}\n"
            field_value += f"**Date:** {impound.get('impound_at', 'N/A')}"
            
            embed.add_field(name=f"🔖 {impound.get('plaque', 'Unknown')}", value=field_value, inline=False)

        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="impound_release", description="Libérer un véhicule de la fourrière")
    @app_commands.describe(plaque="La plaque du véhicule")
    async def impound_release(self, interaction: discord.Interaction, plaque: str):
        if not self.has_police_role(interaction.user):
            embed = discord.Embed(title="❌ Permission refusée", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        data = self.load_impounded()
        
        for impound in data["impounded_list"]:
            if impound.get("plaque").upper() == plaque.upper() and impound.get("status") == "Actif":
                impound["status"] = "Libéré"
                impound["released"] = True
                impound["released_at"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                impound["released_by"] = interaction.user.name
                
                self.save_impounded(data)

                embed = discord.Embed(title="✅ Véhicule libéré", description=f"Plaque: **{plaque.upper()}**", color=discord.Color.green())
                embed.add_field(name="Libéré par", value=interaction.user.mention, inline=False)
                embed.timestamp = datetime.now()

                await interaction.response.send_message(embed=embed)
                return

        embed = discord.Embed(title="❌ Véhicule non trouvé", description=f"Aucun véhicule en fourrière trouvé avec la plaque **{plaque}**", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Impound(bot))
