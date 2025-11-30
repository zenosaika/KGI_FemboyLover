"""
Normal Day Strategy Analysis & Backtesting
FemboyLover Team - KGI Algo Trading Competition 2025

Deep analysis of strategies that could outperform VWAP mean reversion on normal days.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, time, timedelta
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Directories
BASE_DIR = Path(__file__).parent.parent
TICKS_DIR = BASE_DIR / "marketInfo" / "ticks"
FIGURES_DIR = Path(__file__).parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Constants
COMMISSION_RATE = 0.00157 * 1.07  # 0.168%
INITIAL_CAPITAL = 10_000_000

# Define normal vs anomaly days
ANOMALY_DAYS = ['2025-10-28', '2025-11-11']
NORMAL_TEST_DAYS = ['2025-11-12', '2025-11-13', '2025-11-14', '2025-11-17', '2025-11-18',
                    '2025-11-19', '2025-11-20', '2025-11-21', '2025-09-17', '2025-09-18']

def get_tick_size(price):
    """Get tick size based on SET price tiers"""
    if price < 2: return 0.01
    elif price < 5: return 0.02
    elif price < 10: return 0.05
    elif price < 25: return 0.10
    elif price < 50: return 0.25
    elif price < 100: return 0.50
    elif price < 200: return 1.00
    elif price < 400: return 2.00
    else: return 4.00

def load_tick_data(date_str):
    """Load tick data for a specific date"""
    file_path = TICKS_DIR / f"{date_str}.csv"
    if file_path.exists():
        df = pd.read_csv(file_path)
        # Rename columns to standard names
        df = df.rename(columns={
            'ShareCode': 'symbol',
            'TradeDateTime': 'timestamp',
            'LastPrice': 'price',
            'Volume': 'volume',
            'Flag': 'flag'
        })
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Filter out OPEN flags
        df = df[~df['flag'].str.contains('OPEN', na=False)]
        return df
    return None

def analyze_normal_day_patterns(date_str):
    """Deep analysis of market patterns on a normal day"""
    df = load_tick_data(date_str)
    if df is None:
        return None

    results = {}

    for symbol in df['symbol'].unique():
        sym_df = df[df['symbol'] == symbol].copy().sort_values('timestamp')
        if len(sym_df) < 50:
            continue

        prices = sym_df['price'].values
        volumes = sym_df['volume'].values
        flags = sym_df['flag'].values
        timestamps = sym_df['timestamp'].values

        # Basic stats
        avg_price = np.mean(prices)
        price_range = (np.max(prices) - np.min(prices)) / avg_price * 100
        tick_size = get_tick_size(avg_price)
        unique_prices = len(np.unique(prices))

        # Calculate VWAP
        cum_vol = np.cumsum(volumes)
        cum_pv = np.cumsum(prices * volumes)
        vwap = cum_pv / cum_vol

        # Deviation from VWAP
        deviations = (prices - vwap) / vwap * 100

        # Count buy signals (price 1.5% below VWAP)
        buy_signals = np.sum(prices <= vwap * 0.985)

        # Mean reversion analysis
        above_vwap = prices > vwap
        vwap_crossings = np.sum(np.diff(above_vwap.astype(int)) != 0)

        # Momentum analysis
        returns = np.diff(prices) / prices[:-1]
        if len(returns) > 1:
            momentum_continuation = np.mean(returns[:-1] * returns[1:] > 0)
        else:
            momentum_continuation = 0

        # Volume imbalance
        buy_vol = volumes[flags == 'Buy'].sum() if 'Buy' in flags else 0
        sell_vol = volumes[flags == 'Sell'].sum() if 'Sell' in flags else 0
        total_vol = buy_vol + sell_vol
        vol_imbalance = (buy_vol - sell_vol) / total_vol * 100 if total_vol > 0 else 0

        # Intraday patterns - split into time periods
        hours = pd.to_datetime(timestamps).hour
        morning_mask = hours < 12
        afternoon_mask = hours >= 12

        morning_range = 0
        afternoon_range = 0
        if np.sum(morning_mask) > 0:
            morning_prices = prices[morning_mask]
            morning_range = (np.max(morning_prices) - np.min(morning_prices)) / np.mean(morning_prices) * 100
        if np.sum(afternoon_mask) > 0:
            afternoon_prices = prices[afternoon_mask]
            afternoon_range = (np.max(afternoon_prices) - np.min(afternoon_prices)) / np.mean(afternoon_prices) * 100

        results[symbol] = {
            'ticks': len(prices),
            'avg_price': avg_price,
            'price_range_pct': price_range,
            'tick_size': tick_size,
            'unique_prices': unique_prices,
            'buy_signals': buy_signals,
            'vwap_crossings': vwap_crossings,
            'momentum_continuation': momentum_continuation,
            'vol_imbalance': vol_imbalance,
            'morning_range': morning_range,
            'afternoon_range': afternoon_range,
            'avg_deviation': np.mean(np.abs(deviations)),
            'max_below_vwap': np.min(deviations),
            'max_above_vwap': np.max(deviations)
        }

    return results


class StrategyBacktester:
    """Backtester for various strategies"""

    def __init__(self, initial_capital=INITIAL_CAPITAL):
        self.initial_capital = initial_capital
        self.reset()

    def reset(self):
        self.cash = self.initial_capital
        self.positions = {}  # symbol -> {'volume': int, 'avg_price': float}
        self.trades = []
        self.nav_history = []

    def get_nav(self, current_prices):
        """Calculate current NAV"""
        nav = self.cash
        for symbol, pos in self.positions.items():
            if symbol in current_prices and pos['volume'] > 0:
                nav += pos['volume'] * current_prices[symbol]
        return nav

    def buy(self, symbol, volume, price, timestamp):
        """Execute buy order"""
        if volume <= 0:
            return False

        # Calculate cost including slippage and commission
        tick_size = get_tick_size(price)
        execution_price = price + tick_size  # Slippage
        cost = volume * execution_price
        commission = cost * COMMISSION_RATE
        total_cost = cost + commission

        if total_cost > self.cash:
            return False

        self.cash -= total_cost

        if symbol not in self.positions:
            self.positions[symbol] = {'volume': 0, 'avg_price': 0, 'entry_time': timestamp}

        old_vol = self.positions[symbol]['volume']
        old_cost = old_vol * self.positions[symbol]['avg_price']
        new_vol = old_vol + volume
        new_cost = old_cost + cost

        self.positions[symbol]['volume'] = new_vol
        self.positions[symbol]['avg_price'] = new_cost / new_vol if new_vol > 0 else 0
        self.positions[symbol]['entry_time'] = timestamp

        self.trades.append({
            'timestamp': timestamp,
            'symbol': symbol,
            'side': 'BUY',
            'volume': volume,
            'price': execution_price,
            'cost': total_cost
        })

        return True

    def sell(self, symbol, volume, price, timestamp):
        """Execute sell order"""
        if symbol not in self.positions or self.positions[symbol]['volume'] < volume:
            return False, 0

        # Calculate proceeds including slippage and commission
        tick_size = get_tick_size(price)
        execution_price = price - tick_size  # Slippage
        proceeds = volume * execution_price
        commission = proceeds * COMMISSION_RATE
        net_proceeds = proceeds - commission

        # Calculate P&L
        entry_price = self.positions[symbol]['avg_price']
        pnl = net_proceeds - (volume * entry_price)

        self.cash += net_proceeds
        self.positions[symbol]['volume'] -= volume

        if self.positions[symbol]['volume'] == 0:
            del self.positions[symbol]

        self.trades.append({
            'timestamp': timestamp,
            'symbol': symbol,
            'side': 'SELL',
            'volume': volume,
            'price': execution_price,
            'pnl': pnl
        })

        return True, pnl

    def get_results(self):
        """Get backtest results"""
        total_trades = len([t for t in self.trades if t['side'] == 'SELL'])
        wins = len([t for t in self.trades if t['side'] == 'SELL' and t.get('pnl', 0) > 0])
        total_pnl = sum([t.get('pnl', 0) for t in self.trades if t['side'] == 'SELL'])

        return {
            'final_nav': self.cash,
            'return_pct': (self.cash - self.initial_capital) / self.initial_capital * 100,
            'total_trades': total_trades,
            'wins': wins,
            'win_rate': wins / total_trades * 100 if total_trades > 0 else 0,
            'total_pnl': total_pnl
        }


def run_vwap_mean_reversion(df, backtester, position_size=500_000, buy_trigger=0.985):
    """Original VWAP Mean Reversion Strategy"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 20)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'vwap_num': 0, 'vwap_den': 0, 'vwap': 0, 'buy_price': 0}

        data = symbol_data[symbol]
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        data['vwap'] = data['vwap_num'] / data['vwap_den']

        # Check if we have position
        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            take_profit = data['vwap']
            stop_loss = pos['avg_price'] * 0.98

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price >= take_profit:
                sell = True
            elif price <= stop_loss:
                sell = True

            if sell:
                backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            if current_time >= stop_trades_time:
                continue

            buy_trigger_price = data['vwap'] * buy_trigger

            if price <= buy_trigger_price and backtester.cash > position_size:
                vol_to_buy = int((position_size / price) // 100 * 100)
                if vol_to_buy >= 100:
                    backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_momentum_strategy(df, backtester, position_size=500_000, lookback=5, threshold=0.5):
    """Momentum Strategy - Buy on upward momentum, sell on reversal"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 20)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'prices': [], 'entry_price': 0}

        data = symbol_data[symbol]
        data['prices'].append(price)

        if len(data['prices']) > lookback:
            data['prices'] = data['prices'][-lookback:]

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            # Sell on momentum reversal or EOD
            if current_time >= liquidate_time:
                backtester.sell(symbol, pos['volume'], price, timestamp)
            elif len(data['prices']) >= lookback:
                recent_return = (price - data['prices'][0]) / data['prices'][0] * 100
                if recent_return < -threshold:  # Momentum reversed
                    backtester.sell(symbol, pos['volume'], price, timestamp)
                elif price >= pos['avg_price'] * 1.01:  # 1% profit target
                    backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            if current_time >= stop_trades_time:
                continue

            if len(data['prices']) >= lookback and backtester.cash > position_size:
                recent_return = (price - data['prices'][0]) / data['prices'][0] * 100
                if recent_return > threshold:  # Positive momentum
                    vol_to_buy = int((position_size / price) // 100 * 100)
                    if vol_to_buy >= 100:
                        backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_range_breakout_strategy(df, backtester, position_size=500_000, range_period=30, breakout_pct=1.0):
    """Range Breakout Strategy - Buy on breakout above range high"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 20)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'prices': [], 'entry_price': 0, 'range_high': 0, 'range_low': float('inf')}

        data = symbol_data[symbol]
        data['prices'].append(price)

        if len(data['prices']) > range_period:
            data['prices'] = data['prices'][-range_period:]
            data['range_high'] = max(data['prices'][:-1])
            data['range_low'] = min(data['prices'][:-1])

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            if current_time >= liquidate_time:
                backtester.sell(symbol, pos['volume'], price, timestamp)
            elif data['range_low'] > 0 and price <= data['range_low']:  # Breakdown - stop loss
                backtester.sell(symbol, pos['volume'], price, timestamp)
            elif price >= pos['avg_price'] * 1.015:  # 1.5% profit target
                backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            if current_time >= stop_trades_time:
                continue

            if len(data['prices']) >= range_period and data['range_high'] > 0:
                breakout_level = data['range_high'] * (1 + breakout_pct / 100)
                if price >= breakout_level and backtester.cash > position_size:
                    vol_to_buy = int((position_size / price) // 100 * 100)
                    if vol_to_buy >= 100:
                        backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_volume_imbalance_strategy(df, backtester, position_size=500_000, imbalance_threshold=60):
    """Volume Imbalance Strategy - Trade in direction of volume flow"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 20)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        flag = row['flag']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'buy_vol': 0, 'sell_vol': 0, 'prices': []}

        data = symbol_data[symbol]

        if flag == 'Buy':
            data['buy_vol'] += volume
        elif flag == 'Sell':
            data['sell_vol'] += volume

        data['prices'].append(price)
        if len(data['prices']) > 20:
            data['prices'] = data['prices'][-20:]

        total_vol = data['buy_vol'] + data['sell_vol']
        buy_pct = data['buy_vol'] / total_vol * 100 if total_vol > 0 else 50

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            if current_time >= liquidate_time:
                backtester.sell(symbol, pos['volume'], price, timestamp)
            elif buy_pct < 40:  # Selling pressure
                backtester.sell(symbol, pos['volume'], price, timestamp)
            elif price >= pos['avg_price'] * 1.01:  # 1% profit
                backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            if current_time >= stop_trades_time:
                continue

            if buy_pct >= imbalance_threshold and backtester.cash > position_size:
                # Strong buying imbalance
                vol_to_buy = int((position_size / price) // 100 * 100)
                if vol_to_buy >= 100:
                    backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_enhanced_vwap_strategy(df, backtester, position_size=400_000, buy_trigger=0.980,
                                target_stocks=None, min_range=2.0):
    """Enhanced VWAP Strategy - Selective stocks, tighter trigger, dynamic sizing"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}
    stock_ranges = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 15)

    # First pass - calculate daily ranges for stock selection
    for symbol in df['symbol'].unique():
        sym_df = df[df['symbol'] == symbol]
        prices = sym_df['price'].values
        if len(prices) > 0:
            stock_ranges[symbol] = (np.max(prices) - np.min(prices)) / np.mean(prices) * 100

    # Select high-range stocks if not specified
    if target_stocks is None:
        target_stocks = [s for s, r in stock_ranges.items() if r >= min_range]

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        # Only trade target stocks
        if symbol not in target_stocks:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'vwap_num': 0, 'vwap_den': 0, 'vwap': 0}

        data = symbol_data[symbol]
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        data['vwap'] = data['vwap_num'] / data['vwap_den']

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            take_profit = data['vwap'] * 0.998  # Sell slightly below VWAP
            stop_loss = pos['avg_price'] * 0.985  # Tighter stop

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price >= take_profit:
                sell = True
            elif price <= stop_loss:
                sell = True

            if sell:
                backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            if current_time >= stop_trades_time:
                continue

            buy_trigger_price = data['vwap'] * buy_trigger

            if price <= buy_trigger_price and backtester.cash > position_size:
                vol_to_buy = int((position_size / price) // 100 * 100)
                if vol_to_buy >= 100:
                    backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_time_based_vwap_strategy(df, backtester, position_size=500_000):
    """Time-Based VWAP - Different triggers at different times of day"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 10)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()
        hour = timestamp.hour

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'vwap_num': 0, 'vwap_den': 0, 'vwap': 0}

        data = symbol_data[symbol]
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        data['vwap'] = data['vwap_num'] / data['vwap_den']

        # Dynamic buy trigger based on time
        if hour < 11:  # Morning - aggressive
            buy_trigger = 0.990  # 1% below VWAP
        elif hour < 14:  # Midday - moderate
            buy_trigger = 0.985  # 1.5% below VWAP
        else:  # Afternoon - conservative (more reliable VWAP)
            buy_trigger = 0.980  # 2% below VWAP

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            take_profit = data['vwap']
            stop_loss = pos['avg_price'] * 0.98

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price >= take_profit:
                sell = True
            elif price <= stop_loss:
                sell = True

            if sell:
                backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            if current_time >= stop_trades_time:
                continue

            buy_trigger_price = data['vwap'] * buy_trigger

            if price <= buy_trigger_price and backtester.cash > position_size:
                vol_to_buy = int((position_size / price) // 100 * 100)
                if vol_to_buy >= 100:
                    backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_double_down_vwap_strategy(df, backtester, position_size=300_000):
    """Double-Down VWAP - Add to winning positions"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 10)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'vwap_num': 0, 'vwap_den': 0, 'vwap': 0, 'buys': 0}

        data = symbol_data[symbol]
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        data['vwap'] = data['vwap_num'] / data['vwap_den']

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            take_profit = data['vwap']
            stop_loss = pos['avg_price'] * 0.98

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price >= take_profit:
                sell = True
            elif price <= stop_loss:
                sell = True

            if sell:
                backtester.sell(symbol, pos['volume'], price, timestamp)
                data['buys'] = 0
            else:
                # Double down if price drops further but still above stop
                if data['buys'] < 2 and price <= pos['avg_price'] * 0.99 and price > stop_loss:
                    if backtester.cash > position_size:
                        vol_to_buy = int((position_size / price) // 100 * 100)
                        if vol_to_buy >= 100:
                            backtester.buy(symbol, vol_to_buy, price, timestamp)
                            data['buys'] += 1
        else:
            data['buys'] = 0
            if current_time >= stop_trades_time:
                continue

            buy_trigger_price = data['vwap'] * 0.985

            if price <= buy_trigger_price and backtester.cash > position_size:
                vol_to_buy = int((position_size / price) // 100 * 100)
                if vol_to_buy >= 100:
                    backtester.buy(symbol, vol_to_buy, price, timestamp)
                    data['buys'] = 1

    return backtester.get_results()


def run_scalping_strategy(df, backtester, position_size=200_000, profit_target=0.3, max_hold_ticks=50):
    """Scalping Strategy - Quick in and out with small profit targets"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 00)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'prices': [], 'hold_ticks': 0}

        data = symbol_data[symbol]
        data['prices'].append(price)
        if len(data['prices']) > 10:
            data['prices'] = data['prices'][-10:]

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            data['hold_ticks'] += 1

            pnl_pct = (price - pos['avg_price']) / pos['avg_price'] * 100

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif pnl_pct >= profit_target:  # Small profit target
                sell = True
            elif pnl_pct <= -0.5:  # Tight stop
                sell = True
            elif data['hold_ticks'] >= max_hold_ticks:  # Time-based exit
                sell = True

            if sell:
                backtester.sell(symbol, pos['volume'], price, timestamp)
                data['hold_ticks'] = 0
        else:
            data['hold_ticks'] = 0
            if current_time >= stop_trades_time:
                continue

            # Buy on small dip
            if len(data['prices']) >= 5:
                recent_high = max(data['prices'][-5:])
                if price <= recent_high * 0.995 and backtester.cash > position_size:  # 0.5% below recent high
                    vol_to_buy = int((position_size / price) // 100 * 100)
                    if vol_to_buy >= 100:
                        backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_deep_discount_vwap(df, backtester, position_size=600_000, buy_trigger=0.975):
    """Deep Discount VWAP - Only buy at significant discount (2.5% below VWAP)"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 15)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'vwap_num': 0, 'vwap_den': 0, 'vwap': 0}

        data = symbol_data[symbol]
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        data['vwap'] = data['vwap_num'] / data['vwap_den']

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            # Higher take profit - 0.5% above VWAP
            take_profit = data['vwap'] * 1.005
            stop_loss = pos['avg_price'] * 0.97  # 3% stop loss

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price >= take_profit:
                sell = True
            elif price <= stop_loss:
                sell = True

            if sell:
                backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            if current_time >= stop_trades_time:
                continue

            # Only buy at deep discount
            buy_trigger_price = data['vwap'] * buy_trigger

            if price <= buy_trigger_price and backtester.cash > position_size:
                vol_to_buy = int((position_size / price) // 100 * 100)
                if vol_to_buy >= 100:
                    backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_afternoon_vwap(df, backtester, position_size=500_000, buy_trigger=0.985):
    """Afternoon Only VWAP - Only trade after 13:00 when VWAP is more stable"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 15)
    start_trades_time = time(13, 0)  # Only start trading in afternoon

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'vwap_num': 0, 'vwap_den': 0, 'vwap': 0}

        data = symbol_data[symbol]
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        data['vwap'] = data['vwap_num'] / data['vwap_den']

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            take_profit = data['vwap']
            stop_loss = pos['avg_price'] * 0.98

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price >= take_profit:
                sell = True
            elif price <= stop_loss:
                sell = True

            if sell:
                backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            # Only trade in afternoon
            if current_time < start_trades_time or current_time >= stop_trades_time:
                continue

            buy_trigger_price = data['vwap'] * buy_trigger

            if price <= buy_trigger_price and backtester.cash > position_size:
                vol_to_buy = int((position_size / price) // 100 * 100)
                if vol_to_buy >= 100:
                    backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_low_price_focus(df, backtester, position_size=400_000, buy_trigger=0.985, max_price=25):
    """Low Price Focus - Only trade stocks under 25 THB for lower transaction costs"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 15)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        # Only trade low price stocks
        if price > max_price:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'vwap_num': 0, 'vwap_den': 0, 'vwap': 0}

        data = symbol_data[symbol]
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        data['vwap'] = data['vwap_num'] / data['vwap_den']

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            take_profit = data['vwap']
            stop_loss = pos['avg_price'] * 0.98

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price >= take_profit:
                sell = True
            elif price <= stop_loss:
                sell = True

            if sell:
                backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            if current_time >= stop_trades_time:
                continue

            buy_trigger_price = data['vwap'] * buy_trigger

            if price <= buy_trigger_price and backtester.cash > position_size:
                vol_to_buy = int((position_size / price) // 100 * 100)
                if vol_to_buy >= 100:
                    backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_conservative_vwap(df, backtester, position_size=300_000, buy_trigger=0.980, max_positions=5):
    """Conservative VWAP - Fewer positions, tighter controls"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 10)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {'vwap_num': 0, 'vwap_den': 0, 'vwap': 0}

        data = symbol_data[symbol]
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        data['vwap'] = data['vwap_num'] / data['vwap_den']

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            take_profit = data['vwap'] * 0.998  # Slightly below VWAP
            stop_loss = pos['avg_price'] * 0.985  # Tighter stop

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price >= take_profit:
                sell = True
            elif price <= stop_loss:
                sell = True

            if sell:
                backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            if current_time >= stop_trades_time:
                continue

            # Limit number of concurrent positions
            if len(backtester.positions) >= max_positions:
                continue

            buy_trigger_price = data['vwap'] * buy_trigger

            if price <= buy_trigger_price and backtester.cash > position_size:
                vol_to_buy = int((position_size / price) // 100 * 100)
                if vol_to_buy >= 100:
                    backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_wait_for_pattern(df, backtester, position_size=500_000):
    """Wait for Pattern - Only trade when price shows specific pattern"""
    backtester.reset()

    symbol_data = {}
    current_prices = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 10)

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        current_prices[symbol] = price

        if symbol not in symbol_data:
            symbol_data[symbol] = {
                'vwap_num': 0, 'vwap_den': 0, 'vwap': 0,
                'prices': [], 'below_vwap_count': 0
            }

        data = symbol_data[symbol]
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        data['vwap'] = data['vwap_num'] / data['vwap_den']

        data['prices'].append(price)
        if len(data['prices']) > 20:
            data['prices'] = data['prices'][-20:]

        # Track consecutive below VWAP
        if price < data['vwap'] * 0.99:
            data['below_vwap_count'] += 1
        else:
            data['below_vwap_count'] = 0

        has_position = symbol in backtester.positions and backtester.positions[symbol]['volume'] > 0

        if has_position:
            pos = backtester.positions[symbol]
            take_profit = data['vwap']
            stop_loss = pos['avg_price'] * 0.98

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price >= take_profit:
                sell = True
            elif price <= stop_loss:
                sell = True

            if sell:
                backtester.sell(symbol, pos['volume'], price, timestamp)
        else:
            if current_time >= stop_trades_time:
                continue

            # Pattern: price below VWAP for 3+ ticks AND showing potential reversal
            if data['below_vwap_count'] >= 3 and len(data['prices']) >= 5:
                recent_low = min(data['prices'][-5:])
                # Price bouncing from recent low
                if price > recent_low * 1.002 and price <= data['vwap'] * 0.985:
                    if backtester.cash > position_size:
                        vol_to_buy = int((position_size / price) // 100 * 100)
                        if vol_to_buy >= 100:
                            backtester.buy(symbol, vol_to_buy, price, timestamp)

    return backtester.get_results()


def run_all_backtests(date_str):
    """Run all strategies on a given date"""
    df = load_tick_data(date_str)
    if df is None:
        return None

    df = df.sort_values('timestamp')
    backtester = StrategyBacktester()

    results = {}

    # Original VWAP Mean Reversion
    results['VWAP Mean Reversion (Original)'] = run_vwap_mean_reversion(df, backtester)

    # Enhanced VWAP (selective stocks)
    results['Enhanced VWAP (Selective)'] = run_enhanced_vwap_strategy(df, backtester)

    # Time-Based VWAP
    results['Time-Based VWAP'] = run_time_based_vwap_strategy(df, backtester)

    # Double-Down VWAP
    results['Double-Down VWAP'] = run_double_down_vwap_strategy(df, backtester)

    # NEW STRATEGIES FOR NORMAL DAYS
    # Deep Discount VWAP
    results['Deep Discount VWAP'] = run_deep_discount_vwap(df, backtester)

    # Afternoon Only VWAP
    results['Afternoon Only VWAP'] = run_afternoon_vwap(df, backtester)

    # Low Price Focus
    results['Low Price Focus'] = run_low_price_focus(df, backtester)

    # Conservative VWAP
    results['Conservative VWAP'] = run_conservative_vwap(df, backtester)

    # Wait for Pattern
    results['Wait for Pattern'] = run_wait_for_pattern(df, backtester)

    return results


def create_visualizations(all_results, normal_days, anomaly_days):
    """Create comprehensive visualizations"""

    # Figure 1: Strategy Returns Comparison (Normal Days)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Collect normal day results
    strategies = list(list(all_results.values())[0].keys())
    normal_returns = {s: [] for s in strategies}
    anomaly_returns = {s: [] for s in strategies}

    for date, results in all_results.items():
        if date in anomaly_days:
            for s, r in results.items():
                anomaly_returns[s].append(r['return_pct'])
        else:
            for s, r in results.items():
                normal_returns[s].append(r['return_pct'])

    # Average returns on normal days
    ax1 = axes[0, 0]
    avg_normal = {s: np.mean(returns) for s, returns in normal_returns.items()}
    colors = ['#2ECC71' if v > 0 else '#E74C3C' for v in avg_normal.values()]
    bars = ax1.barh(list(avg_normal.keys()), list(avg_normal.values()), color=colors)
    ax1.axvline(x=0, color='black', linewidth=0.5)
    ax1.set_xlabel('Average Return (%)')
    ax1.set_title('Average Return on Normal Days', fontsize=14, fontweight='bold')

    # Add value labels
    for bar, val in zip(bars, avg_normal.values()):
        ax1.text(val + 0.05 if val >= 0 else val - 0.3, bar.get_y() + bar.get_height()/2,
                f'{val:.2f}%', va='center', fontsize=9)

    # Average returns on anomaly days
    ax2 = axes[0, 1]
    avg_anomaly = {s: np.mean(returns) if returns else 0 for s, returns in anomaly_returns.items()}
    colors = ['#2ECC71' if v > 0 else '#E74C3C' for v in avg_anomaly.values()]
    bars = ax2.barh(list(avg_anomaly.keys()), list(avg_anomaly.values()), color=colors)
    ax2.axvline(x=0, color='black', linewidth=0.5)
    ax2.set_xlabel('Average Return (%)')
    ax2.set_title('Average Return on Anomaly Days', fontsize=14, fontweight='bold')

    for bar, val in zip(bars, avg_anomaly.values()):
        ax2.text(val + 0.5, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}%', va='center', fontsize=9)

    # Win rate comparison
    ax3 = axes[1, 0]
    normal_wr = {s: np.mean([all_results[d][s]['win_rate'] for d in normal_days if d in all_results])
                 for s in strategies}
    bars = ax3.barh(list(normal_wr.keys()), list(normal_wr.values()), color='#3498DB')
    ax3.axvline(x=50, color='red', linestyle='--', alpha=0.7, label='50% baseline')
    ax3.set_xlabel('Win Rate (%)')
    ax3.set_title('Average Win Rate on Normal Days', fontsize=14, fontweight='bold')
    ax3.legend()

    # Trade count comparison
    ax4 = axes[1, 1]
    normal_trades = {s: np.mean([all_results[d][s]['total_trades'] for d in normal_days if d in all_results])
                     for s in strategies}
    bars = ax4.barh(list(normal_trades.keys()), list(normal_trades.values()), color='#9B59B6')
    ax4.set_xlabel('Average Trade Count')
    ax4.set_title('Average Trades per Day (Normal Days)', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '14_strategy_returns_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 14_strategy_returns_comparison.png")

    # Figure 2: Day-by-Day Performance
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    all_dates = sorted(all_results.keys())
    x = np.arange(len(all_dates))
    width = 0.1

    ax1 = axes[0]
    for i, strategy in enumerate(strategies[:4]):  # First 4 strategies
        returns = [all_results[d][strategy]['return_pct'] for d in all_dates]
        ax1.bar(x + i*width, returns, width, label=strategy)

    ax1.set_xticks(x + width*1.5)
    ax1.set_xticklabels([d[-5:] for d in all_dates], rotation=45)
    ax1.axhline(y=0, color='black', linewidth=0.5)
    ax1.set_ylabel('Return (%)')
    ax1.set_title('Day-by-Day Returns (Group 1)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=8)

    ax2 = axes[1]
    for i, strategy in enumerate(strategies[4:]):  # Remaining strategies
        returns = [all_results[d][strategy]['return_pct'] for d in all_dates]
        ax2.bar(x + i*width, returns, width, label=strategy)

    ax2.set_xticks(x + width*1.5)
    ax2.set_xticklabels([d[-5:] for d in all_dates], rotation=45)
    ax2.axhline(y=0, color='black', linewidth=0.5)
    ax2.set_ylabel('Return (%)')
    ax2.set_title('Day-by-Day Returns (Group 2)', fontsize=14, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=8)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '15_daily_performance.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 15_daily_performance.png")

    # Figure 3: Risk-Adjusted Analysis
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Scatter: Return vs Trade Count
    ax1 = axes[0]
    for strategy in strategies:
        returns = [all_results[d][strategy]['return_pct'] for d in normal_days if d in all_results]
        trades = [all_results[d][strategy]['total_trades'] for d in normal_days if d in all_results]
        ax1.scatter(np.mean(trades), np.mean(returns), s=100, label=strategy, alpha=0.7)

    ax1.axhline(y=0, color='black', linestyle='--', alpha=0.3)
    ax1.set_xlabel('Average Trades per Day')
    ax1.set_ylabel('Average Return (%)')
    ax1.set_title('Return vs Trading Activity (Normal Days)', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=8, loc='upper right')
    ax1.grid(True, alpha=0.3)

    # Return distribution
    ax2 = axes[1]
    data_to_plot = []
    labels = []
    for strategy in strategies:
        returns = [all_results[d][strategy]['return_pct'] for d in normal_days if d in all_results]
        if returns:
            data_to_plot.append(returns)
            labels.append(strategy.replace(' ', '\n'))

    bp = ax2.boxplot(data_to_plot, labels=labels, patch_artist=True)
    colors = plt.cm.Set3(np.linspace(0, 1, len(strategies)))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax2.set_ylabel('Return (%)')
    ax2.set_title('Return Distribution (Normal Days)', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=8)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '16_risk_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 16_risk_analysis.png")

    # Figure 4: Strategy Decision Matrix
    fig, ax = plt.subplots(figsize=(14, 8))

    criteria = ['Normal Day\nReturn', 'Anomaly Day\nReturn', 'Win Rate', 'Consistency',
                'Trade Frequency', 'Risk/Reward']

    # Score each strategy (0-1)
    scores = []
    for strategy in strategies:
        normal_ret = np.mean([all_results[d][strategy]['return_pct'] for d in normal_days if d in all_results])
        anomaly_ret = np.mean([all_results[d][strategy]['return_pct'] for d in anomaly_days if d in all_results])
        win_rate = np.mean([all_results[d][strategy]['win_rate'] for d in normal_days if d in all_results])

        # Normalize scores
        normal_score = min(1, max(0, (normal_ret + 1) / 2))  # -1 to 1 -> 0 to 1
        anomaly_score = min(1, anomaly_ret / 100) if anomaly_ret > 0 else 0  # 0-100% -> 0-1
        wr_score = win_rate / 100  # 0-100 -> 0-1

        returns_list = [all_results[d][strategy]['return_pct'] for d in all_results]
        consistency = 1 - (np.std(returns_list) / (np.abs(np.mean(returns_list)) + 0.1))
        consistency_score = min(1, max(0, consistency))

        trades = np.mean([all_results[d][strategy]['total_trades'] for d in all_results])
        trade_score = min(1, trades / 100)  # Normalize to 0-1

        risk_reward = normal_ret / (np.std(returns_list) + 0.1)
        rr_score = min(1, max(0, (risk_reward + 1) / 2))

        scores.append([normal_score, anomaly_score, wr_score, consistency_score, trade_score, rr_score])

    scores = np.array(scores)

    im = ax.imshow(scores, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('Score (0-1)', rotation=-90, va="bottom", fontsize=12)

    ax.set_xticks(np.arange(len(criteria)))
    ax.set_yticks(np.arange(len(strategies)))
    ax.set_xticklabels(criteria, fontsize=10)
    ax.set_yticklabels(strategies, fontsize=10)

    for i in range(len(strategies)):
        for j in range(len(criteria)):
            ax.text(j, i, f'{scores[i, j]:.2f}', ha="center", va="center", color="black", fontsize=9)

    ax.set_title('Strategy Decision Matrix (Normal Day Focus)', fontsize=14, fontweight='bold')

    # Highlight best normal day performer
    best_normal_idx = np.argmax([np.mean([all_results[d][s]['return_pct'] for d in normal_days if d in all_results])
                                  for s in strategies])
    ax.add_patch(plt.Rectangle((-0.5, best_normal_idx - 0.5), len(criteria), 1,
                               fill=False, edgecolor='blue', linewidth=3))

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '17_strategy_decision_matrix.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 17_strategy_decision_matrix.png")

    # Figure 5: Recommendation Summary
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Top strategies ranking
    ax1 = axes[0, 0]

    # Calculate composite score for normal days
    composite_scores = {}
    for strategy in strategies:
        normal_ret = np.mean([all_results[d][strategy]['return_pct'] for d in normal_days if d in all_results])
        win_rate = np.mean([all_results[d][strategy]['win_rate'] for d in normal_days if d in all_results])
        composite_scores[strategy] = normal_ret * 0.6 + (win_rate - 50) * 0.02 * 0.4

    sorted_strategies = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)

    y_pos = np.arange(len(sorted_strategies))
    colors = ['#2ECC71' if s[1] > 0 else '#E74C3C' for s in sorted_strategies]
    bars = ax1.barh(y_pos, [s[1] for s in sorted_strategies], color=colors)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels([s[0] for s in sorted_strategies])
    ax1.axvline(x=0, color='black', linewidth=0.5)
    ax1.set_xlabel('Composite Score')
    ax1.set_title('Strategy Ranking for Normal Days\n(60% Return + 40% Win Rate)', fontsize=14, fontweight='bold')

    # Best strategy details
    ax2 = axes[0, 1]
    ax2.axis('off')

    best_strategy = sorted_strategies[0][0]
    best_results = {d: all_results[d][best_strategy] for d in all_results}

    details_text = f"""
    ╔══════════════════════════════════════════════════════════╗
    ║              BEST STRATEGY FOR NORMAL DAYS                ║
    ╠══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║  Strategy: {best_strategy:<43} ║
    ║                                                           ║
    ║  NORMAL DAY PERFORMANCE:                                  ║
    ║  ─────────────────────────────────────────────            ║
    ║  • Average Return: {np.mean([best_results[d]['return_pct'] for d in normal_days if d in best_results]):>+6.2f}%                            ║
    ║  • Average Win Rate: {np.mean([best_results[d]['win_rate'] for d in normal_days if d in best_results]):>5.1f}%                            ║
    ║  • Average Trades: {np.mean([best_results[d]['total_trades'] for d in normal_days if d in best_results]):>6.1f}                              ║
    ║                                                           ║
    ║  ANOMALY DAY PERFORMANCE:                                 ║
    ║  ─────────────────────────────────────────────            ║
    ║  • Average Return: {np.mean([best_results[d]['return_pct'] for d in anomaly_days if d in best_results]):>+6.1f}%                            ║
    ║                                                           ║
    ╚══════════════════════════════════════════════════════════╝
    """
    ax2.text(0.5, 0.5, details_text, transform=ax2.transAxes, fontsize=10,
             verticalalignment='center', horizontalalignment='center',
             fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    ax2.set_title('Best Strategy Details', fontsize=14, fontweight='bold')

    # Comparison with original
    ax3 = axes[1, 0]
    original_returns = [all_results[d]['VWAP Mean Reversion (Original)']['return_pct'] for d in normal_days if d in all_results]
    best_returns = [all_results[d][best_strategy]['return_pct'] for d in normal_days if d in all_results]

    x = np.arange(len(normal_days))
    width = 0.35
    ax3.bar(x - width/2, original_returns, width, label='Original VWAP', color='#3498DB')
    ax3.bar(x + width/2, best_returns, width, label=best_strategy, color='#2ECC71')
    ax3.axhline(y=0, color='black', linewidth=0.5)
    ax3.set_xticks(x)
    ax3.set_xticklabels([d[-5:] for d in normal_days], rotation=45)
    ax3.set_ylabel('Return (%)')
    ax3.set_title('Original vs Best Strategy (Normal Days)', fontsize=14, fontweight='bold')
    ax3.legend()

    # Final recommendation
    ax4 = axes[1, 1]
    ax4.axis('off')

    improvement = np.mean(best_returns) - np.mean(original_returns)

    rec_text = f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                    FINAL RECOMMENDATION                   ║
    ╠══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║  Improvement over Original: {improvement:>+5.2f}%                       ║
    ║                                                           ║
    ║  RECOMMENDATION:                                          ║
    ║  ─────────────────────────────────────────────            ║
    """

    if improvement > 0.1:
        rec_text += f"""║  ✓ ADOPT: {best_strategy:<44} ║
    ║                                                           ║
    ║  KEY CHANGES:                                             ║
    ║  • More selective stock targeting                         ║
    ║  • Tighter position management                            ║
    ║  • Time-aware trading triggers                            ║
    """
    else:
        rec_text += """║  ✗ MAINTAIN Original Strategy                               ║
    ║                                                           ║
    ║  REASON:                                                  ║
    ║  • No significant improvement on normal days              ║
    ║  • Original performs excellently on anomaly days          ║
    ║  • Risk of breaking what works                            ║
    """

    rec_text += """║                                                           ║
    ╚══════════════════════════════════════════════════════════╝
    """

    ax4.text(0.5, 0.5, rec_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='center', horizontalalignment='center',
             fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    ax4.set_title('Final Recommendation', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '18_recommendation_summary.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 18_recommendation_summary.png")


def main():
    print("=" * 70)
    print("Normal Day Strategy Analysis - Deep Planning & Validation")
    print("=" * 70)

    # Define test dates
    normal_days = NORMAL_TEST_DAYS
    anomaly_days = ANOMALY_DAYS
    all_test_days = normal_days + anomaly_days

    print(f"\nAnalyzing {len(normal_days)} normal days and {len(anomaly_days)} anomaly days...")

    # Run all backtests
    all_results = {}
    for date in all_test_days:
        print(f"  Backtesting {date}...", end=" ")
        results = run_all_backtests(date)
        if results:
            all_results[date] = results
            print("Done")
        else:
            print("SKIPPED (no data)")

    # Print summary table
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 70)

    strategies = list(list(all_results.values())[0].keys())

    # Normal days summary
    print("\n--- NORMAL DAYS ---")
    print(f"{'Strategy':<35} {'Avg Return':>12} {'Avg WinRate':>12} {'Avg Trades':>12}")
    print("-" * 73)

    for strategy in strategies:
        avg_return = np.mean([all_results[d][strategy]['return_pct'] for d in normal_days if d in all_results])
        avg_wr = np.mean([all_results[d][strategy]['win_rate'] for d in normal_days if d in all_results])
        avg_trades = np.mean([all_results[d][strategy]['total_trades'] for d in normal_days if d in all_results])
        print(f"{strategy:<35} {avg_return:>+11.2f}% {avg_wr:>11.1f}% {avg_trades:>12.0f}")

    # Anomaly days summary
    print("\n--- ANOMALY DAYS ---")
    print(f"{'Strategy':<35} {'Avg Return':>12} {'Avg WinRate':>12} {'Avg Trades':>12}")
    print("-" * 73)

    for strategy in strategies:
        anomaly_results = [all_results[d][strategy] for d in anomaly_days if d in all_results]
        if anomaly_results:
            avg_return = np.mean([r['return_pct'] for r in anomaly_results])
            avg_wr = np.mean([r['win_rate'] for r in anomaly_results])
            avg_trades = np.mean([r['total_trades'] for r in anomaly_results])
            print(f"{strategy:<35} {avg_return:>+11.1f}% {avg_wr:>11.1f}% {avg_trades:>12.0f}")

    # Generate visualizations
    print("\n" + "=" * 70)
    print("Generating Visualizations...")
    print("=" * 70)

    create_visualizations(all_results, normal_days, anomaly_days)

    # Find best strategy for normal days
    best_normal = max(strategies, key=lambda s: np.mean([all_results[d][s]['return_pct']
                                                          for d in normal_days if d in all_results]))
    best_return = np.mean([all_results[d][best_normal]['return_pct'] for d in normal_days if d in all_results])

    original_return = np.mean([all_results[d]['VWAP Mean Reversion (Original)']['return_pct']
                               for d in normal_days if d in all_results])

    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print(f"\nBest Strategy for Normal Days: {best_normal}")
    print(f"  Average Normal Day Return: {best_return:+.2f}%")
    print(f"\nOriginal VWAP Mean Reversion:")
    print(f"  Average Normal Day Return: {original_return:+.2f}%")
    print(f"\nImprovement: {best_return - original_return:+.2f}%")

    print("\n" + "=" * 70)
    print("All visualizations saved to analysis/figures/")
    print("=" * 70)

    return all_results


if __name__ == "__main__":
    main()
