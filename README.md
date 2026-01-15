# GuidanceBot 🎮

Un bot Discord intelligent conçu pour aider les joueurs bloqués dans leurs quêtes, missions et niveaux de jeux vidéo.

## 📋 Description

GuidanceBot est un assistant Discord alimenté par un LLM qui fournit des conseils et solutions personnalisés aux joueurs en difficulté. Le bot s'appuie sur une base de données de guides de jeux scrapés pour offrir des réponses précises et contextuelles.

## ✨ Fonctionnalités

- 🤖 Assistance en temps réel via Discord
- 📚 Base de connaissances alimentée par des guides de jeux
- 🎯 Réponses contextuelles adaptées aux problèmes spécifiques
- 🔍 Recherche intelligente dans les guides
- 💬 Interface conversationnelle naturelle

## 🏗️ Architecture

Le projet se compose de deux parties principales :

1. **Scraper de guides** : Script de collecte automatique de guides depuis des sites spécialisés
2. **Bot Discord** : Interface Discord connectée à un LLM pour répondre aux questions des joueurs

## 🚀 Installation

### Prérequis

- Python 3.8+
- Un compte Discord et un bot Discord configuré
- Accès à une API LLM (OpenAI, Anthropic, etc.)

### Étapes d'installation

```bash
# Cloner le repository
git clone https://github.com/votre-username/guidancebot.git
cd guidancebot

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API
```

### Configuration

Créez un fichier `.env` à la racine du projet avec les informations suivantes :

```env
DISCORD_TOKEN=votre_token_discord
LLM_API_KEY=votre_clé_api_llm
DATABASE_PATH=./data/guides.db
```

## 📖 Utilisation

### Scraper les guides

```bash
python scraper/main.py --url "https://site-de-guides.com" --output ./data/
```

### Lancer le bot

```bash
python bot/main.py
```

### Commandes Discord

- `!help` - Affiche l'aide et les commandes disponibles
- `!guide <jeu> <question>` - Pose une question sur un jeu spécifique
- `!search <mots-clés>` - Recherche dans la base de guides

## 📁 Structure du projet

```
guidancebot/
├── scraper/
│   ├── main.py           # Script principal de scraping
│   ├── parsers.py        # Parseurs pour différents sites
│   └── utils.py          # Fonctions utilitaires
├── bot/
│   ├── main.py           # Point d'entrée du bot Discord
│   ├── commands.py       # Commandes Discord
│   ├── llm_handler.py    # Gestion des appels au LLM
│   └── database.py       # Gestion de la base de données
├── data/                 # Données scrapées et base de données
├── tests/                # Tests unitaires
├── requirements.txt      # Dépendances Python
├── .env.example          # Exemple de configuration
└── README.md            # Ce fichier
```

## 🛠️ Technologies utilisées

- **Discord.py** - Bibliothèque pour interagir avec l'API Discord
- **BeautifulSoup4** - Parsing HTML pour le scraping
- **Requests** - Requêtes HTTP
- **LangChain** - Framework pour les applications LLM
- **ChromaDB** / **FAISS** - Base de données vectorielle pour la recherche sémantique

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Roadmap

- [ ] Support multi-langues
- [ ] Interface web pour visualiser les guides
- [ ] Intégration de captures d'écran et vidéos
- [ ] Système de notation des réponses
- [ ] Cache intelligent pour optimiser les performances

## ⚖️ Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📧 Contact

Votre Nom - [@votre_twitter](https://twitter.com/votre_twitter)

Lien du projet : [https://github.com/votre-username/guidancebot](https://github.com/votre-username/guidancebot)

## 🙏 Remerciements

- Merci aux sites de guides qui fournissent un contenu de qualité
- Communauté Discord.py pour leur excellente documentation
- Tous les contributeurs qui aident à améliorer ce projet