import ccxt
import pandas as pd
from ta.volatility import BollingerBands
import matplotlib.pyplot as plt

# ==============================
# CONFIGURATION
# ==============================
SYMBOL = 'BTC/USDT'  # Paire de trading
TIMEFRAME = '1d'  # Bougies journalières
LIMIT = 300  # Nombre de bougies récupérées (maximum disponible)
INITIAL_BALANCE = 10000  # Capital initial en USDT
TRADE_PERCENTAGE = 1  # Pourcentage du portefeuille par trade
TAKE_PROFIT_PERCENTAGE = 0.20  # Prise de profit à +20%
STOP_LOSS_PERCENTAGE = 0.05  # Stop-loss à -5%

# ==============================
# INITIALISATION DE BINANCE
# ==============================
exchange = ccxt.binance()

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
    data['bb_upper'] = bb_indicator.bollinger_hband()  # Bande supérieure
    data['bb_middle'] = bb_indicator.bollinger_mavg()  # Moyenne mobile (SMA 20)
    data['bb_lower'] = bb_indicator.bollinger_lband()  # Bande inférieure
    return data


def generate_signal_bb(data):
    """Générer des signaux d'achat/vente basés sur la Bande inférieure et supérieure de Bollinger avec une marge de 5%."""
    data['signal'] = 'HOLD'  # Par défaut, aucun signal
    for i in range(1, len(data)):
        close_price = data['close'].iloc[i]

        # Calcul de la marge de 5% autour des bandes de Bollinger
        bb_lower_5_percent = data['bb_lower'].iloc[i] * 1.05  # 5% en dessous de la bande inférieure
        bb_upper_5_percent = data['bb_upper'].iloc[i] * 0.95 # 5% au-dessus de la bande supérieure

        # Condition d'achat : prix inférieur ou égal à 95% de la bande inférieure
        if close_price <= bb_lower_5_percent:
            data.loc[data.index[i], 'signal'] = 'BUY'

        # Condition de vente : prix supérieur ou égal à 105% de la bande supérieure
        elif close_price >= bb_upper_5_percent:
            data.loc[data.index[i], 'signal'] = 'SELL'

    return data

def backtest_bb_with_tp_sl(data, initial_balance, trade_percentage, take_profit, stop_loss):
    """Backtest avec logique stricte et gestion des Take-Profit et Stop-Loss."""
    balance = initial_balance
    btc_balance = 0
    trades = []
    balance_over_time = [initial_balance]
    in_position = False  # Indicateur pour position ouverte
    buy_price = None  # Suivi du prix d'achat

    for i in range(len(data)):
        signal = data['signal'].iloc[i]
        price = data['close'].iloc[i]

        # Quantité de BTC à acheter/vendre
        trade_amount = (trade_percentage * balance) / price

        # Si une position est ouverte
        if in_position:
            # Vérifier Take-Profit ou Stop-Loss
            change = (price - buy_price) / buy_price  # Calcul de la performance

            # Condition de prise de profit (+20%) ou stop-loss (-5%)
            if change >= take_profit or change <= -stop_loss:
                balance += btc_balance * price  # Vendre tout
                trades.append(('SELL', price, balance, 0))
                btc_balance = 0
                buy_price = None  # Réinitialiser le prix d'achat
                in_position = False  # Position fermée

        else:
            # Si aucune position n'est ouverte
            if signal == 'BUY' and balance >= trade_amount * price:
                btc_balance += trade_amount
                balance -= trade_amount * price
                buy_price = price  # Enregistrer le prix d'achat
                trades.append(('BUY', price, balance, btc_balance))
                in_position = True  # Position ouverte

        # Calcul de la valeur totale actuelle
        current_total_balance = balance + (btc_balance * price)
        balance_over_time.append(current_total_balance)

    # Valeur totale finale
    final_balance = balance + (btc_balance * data['close'].iloc[-1])
    return final_balance, trades, balance_over_time

def plot_backtest(data, trades, balance_over_time):
    """Tracer les résultats du backtesting."""
    # Graphique des prix et signaux
    plt.figure(figsize=(14, 7))
    plt.subplot(2, 1, 1)
    plt.plot(data.index, data['close'], label='Prix BTC/USDT', alpha=0.7)
    plt.plot(data.index, data['bb_upper'], label='Bande Supérieure (BB)', linestyle='--', alpha=0.7)
    plt.plot(data.index, data['bb_middle'], label='Moyenne Mobile (BB)', linestyle='--', alpha=0.7)
    plt.plot(data.index, data['bb_lower'], label='Bande Inférieure (BB)', linestyle='--', alpha=0.7)

    # Ajouter les trades sur le graphique
    for trade in trades:
        action, price, _, _ = trade
        color = 'green' if action == 'BUY' else 'red'
        plt.scatter(data.index[data['close'] == price], [price], c=color, label=action, alpha=0.7)

    plt.title("Prix et signaux de trading (Bandes de Bollinger)")
    plt.xlabel("Date")
    plt.ylabel("Prix (USDT)")
    plt.legend()
    plt.grid()

    # Graphique de l'évolution du capital
    plt.subplot(2, 1, 2)
    plt.plot(balance_over_time, label='Évolution du capital', color='blue')
    plt.title("Évolution du capital au cours du backtesting")
    plt.xlabel("Nombre de trades / Périodes")
    plt.ylabel("Capital (USDT)")
    plt.legend()
    plt.grid()

    plt.tight_layout()
    plt.show()

# ==============================
# SCRIPT PRINCIPAL
# ==============================

# Récupérer les données historiques
data = fetch_historical_data(SYMBOL, TIMEFRAME, LIMIT)

# Appliquer les Bandes de Bollinger
data = apply_bollinger_bands(data)

# Générer les signaux basés sur la BB
data = generate_signal_bb(data)

# Effectuer le backtesting avec TP et SL
final_balance, trades, balance_over_time = backtest_bb_with_tp_sl(
    data,
    INITIAL_BALANCE,
    TRADE_PERCENTAGE,
    TAKE_PROFIT_PERCENTAGE,
    STOP_LOSS_PERCENTAGE
)

# Résultats
print(f"Capital initial : {INITIAL_BALANCE} USDT")
print(f"Capital final : {final_balance:.2f} USDT")
print(f"Nombre de transactions : {len(trades)}")

# Tracer les résultats
plot_backtest(data, trades, balance_over_time)