import ccxt
import pandas as pd
from ta.volatility import BollingerBands
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

# ==============================
# CONFIGURATION
# ==============================
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1d'
LIMIT = 300
INITIAL_BALANCE = 10000
TRADE_PERCENTAGE = 1
TAKE_PROFIT_PERCENTAGE = 0.20
STOP_LOSS_PERCENTAGE = 0.05

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
    data['bb_upper'] = bb_indicator.bollinger_hband()
    data['bb_middle'] = bb_indicator.bollinger_mavg()
    data['bb_lower'] = bb_indicator.bollinger_lband()
    return data


def add_target_for_ml(data):
    """
    Ajouter une colonne 'target' qui correspond à la variation future de prix normalisée entre 0 et 1.
    """
    future_periods = 3
    data['future_return'] = data['close'].shift(-future_periods) / data['close'] - 1
    data['target'] = (data['future_return'] + 1) / 2  # Normalisation entre 0 et 1
    return data.dropna()


def train_ml_model(data, features):
    """
    Entraîner un modèle pour prédire un coefficient d'investissement entre 0 et 1.
    """
    X = data[features]
    y = data['target']

    # Diviser en ensemble d'entraînement et de test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entraîner un modèle RandomForestRegressor
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Évaluer le modèle
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Mean Squared Error: {mse:.4f}")

    return model


def backtest_with_ml(data, model, features, initial_balance, trade_percentage, take_profit, stop_loss):
    """
    Backtest basé sur le modèle de machine learning.
    """
    balance = initial_balance
    btc_balance = 0
    trades = []
    balance_over_time = [initial_balance]
    in_position = False
    buy_price = None

    for i in range(len(data)):
        price = data['close'].iloc[i]

        # Prédire le coefficient d'investissement
        if i >= len(data) - 3:  # Éviter les indices hors limites
            continue
        inputs = data[features].iloc[i].values.reshape(1, -1)
        investment_coefficient = model.predict(inputs)[0]

        # Ajuster le pourcentage de capital à utiliser pour ce trade
        dynamic_trade_percentage = trade_percentage * investment_coefficient

        # Quantité de BTC à acheter/vendre
        trade_amount = (dynamic_trade_percentage * balance) / price

        # Si une position est ouverte
        if in_position:
            change = (price - buy_price) / buy_price
            if change >= take_profit or change <= -stop_loss:
                balance += btc_balance * price
                trades.append(('SELL', price, balance, 0))
                btc_balance = 0
                buy_price = None
                in_position = False

        else:
            if dynamic_trade_percentage > 0 and balance >= trade_amount * price:
                btc_balance += trade_amount
                balance -= trade_amount * price
                buy_price = price
                trades.append(('BUY', price, balance, btc_balance))
                in_position = True

        # Calculer le capital total actuel
        current_total_balance = balance + (btc_balance * price)
        balance_over_time.append(current_total_balance)

    final_balance = balance + (btc_balance * data['close'].iloc[-1])
    return final_balance, trades, balance_over_time


def plot_backtest(data, trades, balance_over_time):
    """Tracer les résultats du backtesting."""
    plt.figure(figsize=(14, 7))
    plt.subplot(2, 1, 1)
    plt.plot(data.index, data['close'], label='Prix BTC/USDT', alpha=0.7)
    for trade in trades:
        action, price, _, _ = trade
        color = 'green' if action == 'BUY' else 'red'
        plt.scatter(data.index[data['close'] == price], [price], c=color, label=action, alpha=0.7)

    plt.title("Prix et signaux de trading")
    plt.xlabel("Date")
    plt.ylabel("Prix (USDT)")
    plt.legend()
    plt.grid()

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

# Récupérer les données
data = fetch_historical_data(SYMBOL, TIMEFRAME, LIMIT)

# Appliquer les indicateurs techniques
data = apply_bollinger_bands(data)

# Ajouter la colonne target
data = add_target_for_ml(data)

# Caractéristiques utilisées pour le modèle
features = ['close', 'bb_upper', 'bb_middle', 'bb_lower']

# Entraîner le modèle
model = train_ml_model(data, features)

# Backtest basé sur le modèle ML
final_balance, trades, balance_over_time = backtest_with_ml(
    data,
    model,
    features,
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