import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
import uuid

class Services(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/services.json'
        self.config_file = 'data/services_config.json'
        self.ensure_data_file()

    def ensure_data_file(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"services": [], "active_services": {}}, f, indent=2)
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f:
                json.dump({
                    "panel_channel_id": None,
                    "panel_message_id": None,
                    "allowed_roles": ["Police", "Commandant", "Chef de Police"]
                }, f, indent=2)

    def load_services(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"services": [], "active_services": {}}

    def save_services(self, data):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "panel_channel_id": None,
                "panel_message_id": None,
                "allowed_roles": ["Police", "Commandant", "Chef de Police"]
            }

    def save_config(self, data):
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def has_police_role(self, member: discord.Member) -> bool:
        config = self.load_config()
        allowed_roles = config.get("allowed_roles", ["Police", "Commandant", "Chef de Police"])
        member_roles = [role.name for role in member.roles]
        for role in allowed_roles:
            if role in member_roles:
                return True
        return False

    def calculate_hours(self, start_time, end_time, pauses):
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        total_seconds = (end - start).total_seconds()
        for pause in pauses:
            pause_start = datetime.fromisoformat(pause["start"])
            pause_end = datetime.fromisoformat(pause["end"])
            pause_duration = (pause_end - pause_start).total_seconds()
            total_seconds -= pause_duration
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"{hours}h{minutes:02d}"

    @app_commands.command(name="setup_services_panel", description="Configurer le salon du panel de services")
    @app_commands.describe(channel="Le salon où envoyer le panel")
    async def setup_services_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="❌ Permission refusée", description="Seul un administrateur peut configurer le panel.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        config = self.load_config()
        config["panel_channel_id"] = channel.id
        self.save_config(config)
        embed = discord.Embed(title="✅ Panel configuré", description=f"Le panel de services sera envoyé dans {channel.mention}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="services_config_roles", description="Configurer les rôles autorisés pour les services")
    @app_commands.describe(roles="Rôles autorisés (séparés par des virgules). Ex: Police,Commandant,Chef")
    async def services_config_roles(self, interaction: discord.Interaction, roles: str):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="❌ Permission refusée", description="Seul un administrateur peut configurer les rôles.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        role_list = [r.strip() for r in roles.split(",")]
        config = self.load_config()
        config["allowed_roles"] = role_list
        self.save_config(config)

        embed = discord.Embed(title="✅ Rôles configurés", description=f"Rôles autorisés:\n" + "\n".join([f"• {r}" for r in role_list]), color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="services_config_view", description="Voir la configuration actuelle des services")
    async def services_config_view(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="❌ Permission refusée", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        config = self.load_config()
        allowed_roles = config.get("allowed_roles", [])
        channel_id = config.get("panel_channel_id")
        channel_text = f"<#{channel_id}>" if channel_id else "Non configuré"
        
        embed = discord.Embed(title="⚙️ Configuration Services", color=discord.Color.blue())
        embed.add_field(name="🎯 Rôles autorisés", value="\n".join([f"• {r}" for r in allowed_roles]) if allowed_roles else "Aucun", inline=False)
        embed.add_field(name="📍 Salon du panel", value=channel_text, inline=False)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="services_panel", description="Envoyer le panel de prise de service")
    async def services_panel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="❌ Permission refusée", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        config = self.load_config()
        channel_id = config.get("panel_channel_id")
        if not channel_id:
            embed = discord.Embed(title="❌ Panel non configuré", description="Utilisez `/setup_services_panel` d'abord", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        channel = self.bot.get_channel(channel_id)
        embed = discord.Embed(title="👮 PANEL DE PRISE DE SERVICE", description="Cliquez sur un bouton pour gérer votre service", color=discord.Color.blue())
        embed.add_field(name="🟢 Prendre Service", value="Commencer votre journée", inline=False)
        embed.add_field(name="⏸️ Pause", value="Mettre en pause", inline=False)
        embed.add_field(name="▶️ Reprendre", value="Reprendre le service", inline=False)
        embed.add_field(name="🔴 Fin de Service", value="Terminer votre journée", inline=False)
        view = ServicesPanelView(self)
        message = await channel.send(embed=embed, view=view)
        config["panel_message_id"] = message.id
        self.save_config(config)
        embed_confirm = discord.Embed(title="✅ Panel envoyé", description=f"Panel envoyé dans {channel.mention}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed_confirm, ephemeral=True)

    @app_commands.command(name="service_list", description="Afficher les officiers en service")
    async def service_list(self, interaction: discord.Interaction):
        data = self.load_services()
        active_services = data.get("active_services", {})
        if not active_services:
            embed = discord.Embed(title="👮 Officiers en Service", description="Aucun officier en service actuellement", color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
            return
        embed = discord.Embed(title="👮 Officiers en Service", description=f"Total: **{len(active_services)}** officier(s)", color=discord.Color.blue())
        for officer_id, service_info in active_services.items():
            status = "🟢 En Service" if service_info.get("status") == "en_service" else "⏸️ En Pause"
            field_value = f"**Matricule:** {service_info.get('matricule', 'N/A')}\n**Grade:** {service_info.get('grade', 'N/A')}\n**Plaque:** {service_info.get('plaque', 'N/A')}\n**Depuis:** {service_info.get('start_time', 'N/A')[11:16]}\n**Statut:** {status}"
            embed.add_field(name=f"👤 {service_info.get('nom_prenom', 'Unknown')}", value=field_value, inline=False)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="service_info", description="Voir les détails du service d'un officier")
    @app_commands.describe(matricule="Le matricule (2 chiffres)")
    async def service_info(self, interaction: discord.Interaction, matricule: str):
        data = self.load_services()
        active_services = data.get("active_services", {})
        service_found = None
        for officer_id, service_info in active_services.items():
            if service_info.get("matricule") == matricule:
                service_found = service_info
                break
        if not service_found:
            embed = discord.Embed(title="❌ Service non trouvé", description=f"Aucun officier trouvé avec le matricule {matricule}", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(title=f"👮 FICHE DE SERVICE - {service_found.get('nom_prenom')}", color=discord.Color.blue())
        embed.add_field(name="🆔 Matricule", value=service_found.get("matricule", "N/A"), inline=True)
        embed.add_field(name="📝 Nom/Prénom", value=service_found.get("nom_prenom", "N/A"), inline=True)
        embed.add_field(name="⭐ Grade", value=service_found.get("grade", "N/A"), inline=True)
        embed.add_field(name="🚗 Plaque", value=service_found.get("plaque", "N/A"), inline=False)
        start_time = service_found.get("start_time", "N/A")
        if start_time != "N/A":
            start_time = start_time[11:16]
        embed.add_field(name="🟢 Prise de service", value=start_time, inline=True)
        pauses = service_found.get("pauses", [])
        if pauses:
            pause_text = ""
            for i, pause in enumerate(pauses, 1):
                pause_start = pause.get("start", "N/A")[11:16]
                pause_end = pause.get("end", "N/A")[11:16] if pause.get("end") else "En cours"
                if pause_end != "En cours":
                    pause_text += f"{i}. {pause_start} → {pause_end}\n"
            if pause_text:
                embed.add_field(name="⏸️ Pauses", value=pause_text, inline=False)
        end_time = service_found.get("end_time")
        if end_time:
            end_time = end_time[11:16]
            embed.add_field(name="🔴 Fin de service", value=end_time, inline=True)
            total_hours = self.calculate_hours(service_found.get("start_time"), service_found.get("end_time"), pauses)
            embed.add_field(name="⏱️ Total", value=total_hours, inline=True)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)

class ServicesPanelView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Prendre Service", style=discord.ButtonStyle.success, emoji="🟢")
    async def take_service(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.cog.has_police_role(interaction.user):
            embed = discord.Embed(title="❌ Permission refusée", description="Seuls les membres autorisés peuvent prendre service.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        data = self.cog.load_services()
        if str(interaction.user.id) in data.get("active_services", {}):
            embed = discord.Embed(title="❌ Déjà en service", description="Vous êtes déjà en service.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        modal = TakeServiceModal(self.cog)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary, emoji="⏸️")
    async def take_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.cog.load_services()
        active_services = data.get("active_services", {})
        if str(interaction.user.id) not in active_services:
            embed = discord.Embed(title="❌ Pas en service", description="Vous devez d'abord prendre service", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        service_info = active_services[str(interaction.user.id)]
        if service_info.get("status") == "pause":
            embed = discord.Embed(title="❌ Déjà en pause", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        service_info["status"] = "pause"
        service_info["pauses"].append({"start": datetime.now().isoformat(), "end": None})
        self.cog.save_services(data)
        embed = discord.Embed(title="⏸️ Pause activée", description=f"Pause depuis {datetime.now().strftime('%H:%M')}", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Reprendre", style=discord.ButtonStyle.primary, emoji="▶️")
    async def resume_service(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.cog.load_services()
        active_services = data.get("active_services", {})
        if str(interaction.user.id) not in active_services:
            embed = discord.Embed(title="❌ Pas en service", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        service_info = active_services[str(interaction.user.id)]
        if service_info.get("status") == "en_service":
            embed = discord.Embed(title="❌ Pas en pause", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        service_info["status"] = "en_service"
        if service_info.get("pauses"):
            service_info["pauses"][-1]["end"] = datetime.now().isoformat()
        self.cog.save_services(data)
        embed = discord.Embed(title="▶️ Service repris", description=f"Reprise depuis {datetime.now().strftime('%H:%M')}", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Fin de Service", style=discord.ButtonStyle.danger, emoji="🔴")
    async def end_service(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.cog.load_services()
        active_services = data.get("active_services", {})
        if str(interaction.user.id) not in active_services:
            embed = discord.Embed(title="❌ Pas en service", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        service_info = active_services[str(interaction.user.id)]
        service_info["end_time"] = datetime.now().isoformat()
        service_info["status"] = "terminated"
        if service_info.get("pauses") and not service_info["pauses"][-1].get("end"):
            service_info["pauses"][-1]["end"] = datetime.now().isoformat()
        data["services"].append(service_info)
        del active_services[str(interaction.user.id)]
        self.cog.save_services(data)
        total_hours = self.cog.calculate_hours(service_info.get("start_time"), service_info.get("end_time"), service_info.get("pauses", []))
        embed = discord.Embed(title=f"👮 FICHE DE SERVICE - {service_info.get('nom_prenom')}", color=discord.Color.gold())
        embed.add_field(name="🆔 Matricule", value=service_info.get("matricule", "N/A"), inline=True)
        embed.add_field(name="📝 Nom/Prénom", value=service_info.get("nom_prenom", "N/A"), inline=True)
        embed.add_field(name="⭐ Grade", value=service_info.get("grade", "N/A"), inline=True)
        embed.add_field(name="🚗 Plaque", value=service_info.get("plaque", "N/A"), inline=False)
        start_time = service_info.get("start_time", "N/A")[11:16]
        embed.add_field(name="🟢 Prise de service", value=start_time, inline=True)
        pauses = service_info.get("pauses", [])
        if pauses:
            pause_text = ""
            for i, pause in enumerate(pauses, 1):
                pause_start = pause.get("start", "N/A")[11:16]
                pause_end = pause.get("end", "N/A")[11:16]
                pause_text += f"{i}. {pause_start} → {pause_end}\n"
            embed.add_field(name="⏸️ Pauses", value=pause_text, inline=False)
        end_time = service_info.get("end_time", "N/A")[11:16]
        embed.add_field(name="🔴 Fin de service", value=end_time, inline=True)
        embed.add_field(name="⏱️ Total", value=total_hours, inline=True)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed)

class TakeServiceModal(discord.ui.Modal, title="Prise de Service"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    matricule = discord.ui.TextInput(label="Matricule (2 chiffres)", placeholder="01", min_length=2, max_length=2)
    nom_prenom = discord.ui.TextInput(label="Nom/Prénom", placeholder="John Doe", min_length=1, max_length=100)
    grade = discord.ui.TextInput(label="Grade", placeholder="Sergent", min_length=1, max_length=50)
    plaque = discord.ui.TextInput(label="Plaque de Service", placeholder="75ABC123", min_length=1, max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        data = self.cog.load_services()
        service_entry = {
            "id": str(uuid.uuid4()),
            "officer_id": str(interaction.user.id),
            "officer_name": interaction.user.name,
            "matricule": self.matricule.value,
            "nom_prenom": self.nom_prenom.value,
            "grade": self.grade.value,
            "plaque": self.plaque.value.upper(),
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "en_service",
            "pauses": []
        }
        data["active_services"][str(interaction.user.id)] = service_entry
        self.cog.save_services(data)
        embed = discord.Embed(title="✅ Service commencé", description=f"{self.nom_prenom.value} a pris service", color=discord.Color.green())
        embed.add_field(name="🆔 Matricule", value=self.matricule.value, inline=True)
        embed.add_field(name="⭐ Grade", value=self.grade.value, inline=True)
        embed.add_field(name="🚗 Plaque", value=self.plaque.value.upper(), inline=True)
        embed.add_field(name="🟢 Heure", value=datetime.now().strftime("%H:%M"), inline=False)
        embed.timestamp = datetime.now()
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Services(bot))
