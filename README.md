# Trading Bot avec Bandes de Bollinger

Ce projet implémente un **bot de trading automatique** basé sur l'analyse technique des **Bandes de Bollinger**. Il utilise l'API de **Binance** pour exécuter des ordres d'achat et de vente sur la paire de trading **BTC/USDT**. Le bot gère également des stratégies de **Take-Profit** et **Stop-Loss** pour protéger le capital.

Le bot fonctionne sur **Python** et utilise des bibliothèques comme **ccxt** (pour interagir avec Binance) et **ta** (pour les indicateurs techniques). Le bot peut être exécuté dans un conteneur Docker pour une utilisation sur des serveurs distants.

La présence de backtests sur 300 jours sont aussi présent afin d'avoir une idée rapide de la performance du bot. 

## Prérequis

Avant d'exécuter ce bot, vous devez disposer des éléments suivants :

- **Python 3.9** ou version supérieure
- **Docker** pour exécuter le bot dans un conteneur
- Une **clé API Binance** et un **secret API**. Ces clés sont nécessaires pour interagir avec l'API de Binance et exécuter des ordres.

## Installation local afin de faire les backtests

### 1. Cloner le dépôt

Clonez ce projet sur votre machine locale :

```bash
git clone https://github.com/Crypte/Trading-bot.git
cd Trading-bot
```

### 2. Créer un environnement virtuel (optionnel mais recommandé)
Si vous souhaitez exécuter le bot localement sans Docker, créez un environnement virtuel Python pour gérer les dépendances.

```bash
python3 -m venv venv
source venv/bin/activate 
```

### 3. Installer les dépendances
Installez les bibliothèques nécessaires via pip :

```bash
pip install -r requirements.txt
```

### 4. API Binance
Pour les backtest, les clés API ne sont pas nécessaire

### 5. Exécuter votre backtests localement :

Placez-vous dans le dossier des backtests
```bash
cd Backtests
```

Exécutez le fichier

```bash
python BacktestFinal.py
```

## Containisation du Bot avec Docker

Afin d'éxecuter le bot dans un conteneur Docker, suivez ces étapes :

### 1. Construire l’image Docker
Dans le répertoire du projet (contenant Dockerfile, bot.py et requirements.txt), exécutez la commande suivante pour construire l’image Docker :

```bash
docker build -t Trading-bot .
```

### 2. Exécuter le conteneur Docker avec en paramètre votre clé API
Une fois l’image construite, exécutez le bot dans un conteneur Docker en passant vos clés API Binance comme variables d’environnement :

```bash
docker run -d \
    -e API_KEY="votre_api_key_binance" \
    -e API_SECRET="votre_api_secret_binance" \
    trading-bot
```
Assurez-vous de remplacer "votre_api_key" et "votre_api_secret" par vos vraies clés API.

### 3. Vérifier les logs du conteneur
Pour vérifier les logs du conteneur en temps réel, vous pouvez exécuter la commande suivante :

```bash
docker logs -f <container_id>
```

### 4. Arrêter le conteneur

Pour arrêter le conteneur, utilisez la commande :

```bash
docker stop <container_id>
```


## Structure du projet

- **bot.py** : Le script principal qui contient la logique du bot.
- **Dockerfile** : Fichier Docker pour construire l’image et exécuter le bot dans un conteneur.
- **requirements.txt** : Liste des dépendances Python nécessaires.
- **README.md** : Ce fichier.
- **/Backtests** : Dossiers des Backtests

## Personnalisation

Vous pouvez personnaliser plusieurs paramètres dans les backtests en modifiant les variables suivantes dans chaque fichier :

- **SYMBOL** : La paire de trading (par défaut `BTC/USDT`).
- **TIMEFRAME** : La période des bougies (par défaut `1d` pour une bougie journalière).
- **LIMIT** : Le nombre de bougies récupérées pour l’analyse (par défaut 300 et également le maximum).
- **INITIAL_BALANCE** : Le capital initial en USDT (par défaut 10000).
- **TRADE_PERCENTAGE** : Le pourcentage du portefeuille utilisé par trade (par défaut 1%).
- **TAKE_PROFIT_PERCENTAGE** : Le pourcentage de prise de profit (+20% par défaut).
- **STOP_LOSS_PERCENTAGE** : Le pourcentage de stop-loss (-5% par défaut).

## Notes

- **Sécurité** : Assurez-vous de ne jamais partager vos clés API en public. Utilisez des variables d’environnement ou des services sécurisés pour les stocker si nécessaire.
- **Backtest** : Le bot utilise un modèle de backtest pour simuler les résultats avant d’exécuter les transactions réelles.
- **API Rate Limits** : L’API de Binance a des limites de requêtes par minute. Le bot est configuré pour respecter ces limites.
- **Prise de profit et Stop-loss** : Le bot gère automatiquement les positions ouvertes avec des stratégies de prise de profit et de stop-loss.
