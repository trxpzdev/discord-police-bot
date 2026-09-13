import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
import uuid

class Vehicles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/vehicles.json'
        self.ensure_data_file()

    def ensure_data_file(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"vehicles_list": []}, f, indent=2)

    def load_vehicles(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"vehicles_list": []}

    def save_vehicles(self, data):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def has_police_role(self, member: discord.Member) -> bool:
        required_roles = ["Police", "Commandant", "Chef de Police"]
        member_roles = [role.name for role in member.roles]
        for role in required_roles:
            if role in member_roles:
                return True
        return False

    @app_commands.command(name="vehicle_register", description="Enregistrer un véhicule")
    @app_commands.describe(plaque="La plaque du véhicule", marque="Marque", modele="Modèle", proprietaire="Propriétaire")
    async def vehicle_register(self, interaction: discord.Interaction, plaque: str, marque: str, modele: str, proprietaire: str):
        if not self.has_police_role(interaction.user):
            embed = discord.Embed(title="❌ Permission refusée", description="Seuls les membres de la Police peuvent enregistrer des véhicules.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        data = self.load_vehicles()
        
        for vehicle in data["vehicles_list"]:
            if vehicle.get("plaque").upper() == plaque.upper():
                embed = discord.Embed(title="❌ Véhicule existant", description=f"La plaque **{plaque}** est déjà enregistrée!", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        vehicle_entry = {
            "id": str(uuid.uuid4()),
            "plaque": plaque.upper(),
            "marque": marque,
            "modele": modele,
            "proprietaire": proprietaire,
            "officer": interaction.user.name,
            "officer_id": str(interaction.user.id),
            "registered_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "status": "Enregistré"
        }

        data["vehicles_list"].append(vehicle_entry)
        self.save_vehicles(data)

        embed = discord.Embed(title="✅ Véhicule enregistré", description=f"Plaque: **{plaque.upper()}**", color=discord.Color.green())
        embed.add_field(name="🏎️ Marque", value=marque, inline=True)
        embed.add_field(name="🏎️ Modèle", value=modele, inline=True)
        embed.add_field(name="👤 Propriétaire", value=proprietaire, inline=False)
        embed.add_field(name="👮 Enregistré par", value=interaction.user.mention, inline=False)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="vehicle_list", description="Afficher la liste des véhicules enregistrés")
    async def vehicle_list(self, interaction: discord.Interaction):
        data = self.load_vehicles()
        vehicles = data.get("vehicles_list", [])

        if not vehicles:
            embed = discord.Embed(title="🏎️ Véhicules", description="Aucun véhicule enregistré", color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(title="🏎️ Véhicules enregistrés", description=f"Total: **{len(vehicles)}** véhicule(s)", color=discord.Color.blue())

        for vehicle in vehicles:
            field_value = f"**Marque:** {vehicle.get('marque', 'N/A')}\n"
            field_value += f"**Modèle:** {vehicle.get('modele', 'N/A')}\n"
            field_value += f"**Propriétaire:** {vehicle.get('proprietaire', 'N/A')}\n"
            field_value += f"**Date:** {vehicle.get('registered_at', 'N/A')}"
            
            embed.add_field(name=f"🔖 {vehicle.get('plaque', 'Unknown')}", value=field_value, inline=False)

        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="vehicle_info", description="Voir les infos d'un véhicule")
    @app_commands.describe(plaque="La plaque du véhicule")
    async def vehicle_info(self, interaction: discord.Interaction, plaque: str):
        data = self.load_vehicles()
        
        vehicle = None
        for v in data["vehicles_list"]:
            if v.get("plaque").upper() == plaque.upper():
                vehicle = v
                break

        if not vehicle:
            embed = discord.Embed(title="❌ Véhicule non trouvé", description=f"Aucun véhicule trouvé avec la plaque **{plaque}**", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(title=f"🏎️ Infos Véhicule - {vehicle.get('plaque')}", color=discord.Color.blue())
        embed.add_field(name="🏎️ Marque", value=vehicle.get("marque", "N/A"), inline=True)
        embed.add_field(name="🏎️ Modèle", value=vehicle.get("modele", "N/A"), inline=True)
        embed.add_field(name="👤 Propriétaire", value=vehicle.get("proprietaire", "N/A"), inline=False)
        embed.add_field(name="📅 Enregistré le", value=vehicle.get("registered_at", "N/A"), inline=True)
        embed.add_field(name="👮 Enregistré par", value=vehicle.get("officer", "N/A"), inline=True)
        embed.timestamp = datetime.now()

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Vehicles(bot))
