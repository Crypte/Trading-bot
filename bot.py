import ccxt
import os
import pandas as pd
from ta.volatility import BollingerBands
import time
import logging

# ==============================
# CONFIGURATION
# ==============================
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1d'
INITIAL_BALANCE = 10000
TRADE_PERCENTAGE = 1
TAKE_PROFIT_PERCENTAGE = 0.20
STOP_LOSS_PERCENTAGE = 0.04

# Récupération des clés API depuis les variables d'environnement
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

if not API_KEY or not API_SECRET:
    raise ValueError(
        "Les clés API Binance doivent être spécifiées via les variables d'environnement BINANCE_API_KEY et BINANCE_API_SECRET.")

# ==============================
# INITIALISATION DE BINANCE
# ==============================
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


# ==============================
# FONCTIONS
# ==============================
def fetch_historical_data(symbol, timeframe, limit):
    """Télécharger les données historiques de marché (OHLCV)."""
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    data.set_index('timestamp', inplace=True)
    return data


def apply_bollinger_bands(data):
    """Ajouter les Bandes de Bollinger (BB) au DataFrame."""
    bb_indicator = BollingerBands(close=data['close'], window=20, window_dev=2)
    data['bb_upper'] = bb_indicator.bollinger_hband()
    data['bb_middle'] = bb_indicator.bollinger_mavg()
    data['bb_lower'] = bb_indicator.bollinger_lband()
    return data


def generate_signal_bb(data):
    """Générer des signaux d'achat basés sur les Bandes de Bollinger."""
    data['signal'] = 'HOLD'
    for i in range(1, len(data)):
        close_price = data['close'].iloc[i]
        bb_lower_5_percent = data['bb_lower'].iloc[i] * 1.05

        # Condition d'achat : prix inférieur ou égal à 95% de la bande inférieure
        if close_price <= bb_lower_5_percent:
            data.loc[data.index[i], 'signal'] = 'BUY'
    return data


def execute_trade(action, amount, symbol):
    """Exécuter un ordre de trading."""
    try:
        if action == 'BUY':
            order = exchange.create_market_buy_order(symbol, amount)
        elif action == 'SELL':
            order = exchange.create_market_sell_order(symbol, amount)
        logger.info(f"Ordre {action} exécuté : {order}")
        return order
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de l'ordre {action} : {str(e)}")


def run_bot():
    """Fonction principale du bot de trading."""
    balance = INITIAL_BALANCE
    btc_balance = 0
    in_position = False
    buy_price = None

    while True:
        try:
            # Récupérer les données historiques
            data = fetch_historical_data(SYMBOL, TIMEFRAME, limit=100)

            # Appliquer les Bandes de Bollinger et générer des signaux
            data = apply_bollinger_bands(data)
            data = generate_signal_bb(data)

            # Obtenir le dernier signal
            last_signal = data['signal'].iloc[-1]
            last_price = data['close'].iloc[-1]

            # Si une position est ouverte
            if in_position:
                change = (last_price - buy_price) / buy_price

                # Condition de prise de profit ou stop-loss
                if change >= TAKE_PROFIT_PERCENTAGE or change <= -STOP_LOSS_PERCENTAGE:
                    logger.info(f"TP/SL atteint. Vente au prix {last_price:.2f}")
                    execute_trade('SELL', btc_balance, SYMBOL)
                    balance += btc_balance * last_price
                    btc_balance = 0
                    in_position = False

            # Si aucune position n'est ouverte
            elif last_signal == 'BUY' and balance > 0:
                trade_amount = (TRADE_PERCENTAGE * balance) / last_price
                logger.info(f"Signal d'achat détecté. Achat au prix {last_price:.2f}")
                execute_trade('BUY', trade_amount, SYMBOL)
                btc_balance += trade_amount
                balance -= trade_amount * last_price
                in_position = True

            # Afficher le statut actuel
            total_balance = balance + (btc_balance * last_price)
            logger.info(f"Balance totale : {total_balance:.2f} USDT")
            logger.info(f"BTC détenu : {btc_balance:.6f}, Solde en USDT : {balance:.2f}")

            # Attendre jusqu'à la prochaine période quotidienne
            for _ in range(24):  # Attendre 24 heures (par incréments d'1 heure pour éviter un crash)
                time.sleep(3600)

        except Exception as e:
            logger.error(f"Erreur dans le bot : {str(e)}")
            time.sleep(60)  # Attendre 1 minute avant de réessayer après une erreur


# ==============================
# LANCEMENT DU BOT
# ==============================
if __name__ == "__main__":
    run_bot()