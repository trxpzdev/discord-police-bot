# 🚔 Discord Police Bot

Un bot Discord pour le roleplay police avec système complet d'arrestations, amendes et dossiers!

## 📋 Fonctionnalités

✅ **Arrestations** - Arrêtez et libérez des joueurs
✅ **Amendes** - Donnez des amendes avec raison et montant
✅ **Avertissements** - Avertissez les joueurs
✅ **Dossiers** - Consultez l'historique complet d'un joueur
✅ **Système de persistance** - Les données sont sauvegardées
✅ **Embeds Discord** - Interface moderne et colorée

## 🚀 Installation

### Prérequis
- Python 3.8+
- Un bot Discord créé sur [Discord Developer Portal](https://discord.com/developers/applications)
- Le token du bot

### Étapes

1. **Clonez le repo**
   ```bash
   git clone https://github.com/trxpzdev/discord-police-bot.git
   cd discord-police-bot
   ```

2. **Installez les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurez le token**
   - Copiez `.env.example` en `.env`
   - Remplacez `votre_token_ici` par votre vrai token bot
   ```bash
   cp .env.example .env
   ```

4. **Lancez le bot**
   ```bash
   python main.py
   ```

## 📝 Commandes

### Police

| Commande | Description | Exemple |
|----------|-------------|----------|
| `/arrest` | Arrêter un joueur | `/arrest player:@User reason:Violation de la loi` |
| `/release` | Libérer un joueur | `/release player:@User` |
| `/fine` | Donner une amende | `/fine player:@User amount:500 reason:Excès de vitesse` |
| `/warn` | Avertir un joueur | `/warn player:@User reason:Avertissement` |
| `/record` | Consulter le dossier | `/record player:@User` |
| `/clear_record` | Effacer un dossier | `/clear_record player:@User` |

## 📂 Structure du projet

```
discord-police-bot/
├── main.py              # Fichier principal
├── cogs/
│   └── police.py        # Commandes police
├── data/
│   └── records.json     # Base de données (généré automatiquement)
├── requirements.txt     # Dépendances
├── .env                 # Configuration (à créer)
├── .env.example         # Exemple de configuration
├── .gitignore          # Fichiers ignorés
└── README.md           # Ce fichier
```

## 🛠️ Personnalisation

### Changer le préfixe des commandes
Dans `main.py`, modifiez :
```python
bot = commands.Bot(command_prefix='!', intents=intents)  # Remplacez '/' par '!'
```

### Ajouter des rôles requis
Dans `cogs/police.py`, ajoutez avant chaque commande :
```python
@app_commands.checks.has_role("Police")
```

### Modifier les couleurs des embeds
Dans `cogs/police.py`, changez les `discord.Color` :
```python
color=discord.Color.red()      # Rouge
color=discord.Color.green()    # Vert
color=discord.Color.blue()     # Bleu
color=discord.Color.gold()     # Or
color=discord.Color.orange()   # Orange
```

## 📊 Exemple de dossier

Quand vous consultez le dossier d'un joueur avec `/record`, vous obtenez :
- **Statut** : Arrêté ou Libre
- **Arrestations** : Nombre et détails
- **Amendes** : Montant total et détails
- **Avertissements** : Nombre et détails

## 🔐 Permissions

Pour limiter l'accès aux commandes police :

1. Créez un rôle "Police" sur votre serveur
2. Modifiez chaque commande en ajoutant :
   ```python
   @app_commands.checks.has_role("Police")
   ```

## 📚 Ressources

- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Guide complet Discord Bot](https://guide.discord.com/)

## 🤝 Support

Si vous avez des questions ou besoin d'aide :
1. Vérifiez que le token est valide
2. Assurez-vous que le bot a les permissions nécessaires
3. Vérifiez les logs d'erreur dans la console

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

---

**Créé par trxpzdev** 🚔
