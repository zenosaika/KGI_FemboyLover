#!/usr/bin/env python3
"""
Final Report Analysis & Visualizations
FemboyLover Team - KGI Algo Trading Competition 2025

Generates comprehensive visualizations for the competition report.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, time
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['figure.titlesize'] = 16

# Directories
BASE_DIR = Path(__file__).parent.parent
TICKS_DIR = BASE_DIR / "marketInfo" / "ticks"
FIGURES_DIR = Path(__file__).parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Development period dates (for strategy selection)
DEV_DATES = [
    "2025-09-17", "2025-09-18", "2025-09-19", "2025-09-22", "2025-09-23",
    "2025-09-24", "2025-09-25", "2025-09-26", "2025-09-29", "2025-09-30",
    "2025-10-01", "2025-10-02", "2025-10-03", "2025-10-06", "2025-10-07",
    "2025-10-08", "2025-10-09", "2025-10-10", "2025-10-14", "2025-10-15",
    "2025-10-16", "2025-10-17", "2025-10-20", "2025-10-21", "2025-10-22",
    "2025-10-24", "2025-10-27", "2025-10-28", "2025-10-29", "2025-10-30",
    "2025-11-03", "2025-11-04", "2025-11-05", "2025-11-06", "2025-11-07"
]

# Competition period dates
COMP_DATES = [
    "2025-11-10", "2025-11-11", "2025-11-12", "2025-11-13", "2025-11-14",
    "2025-11-17", "2025-11-18", "2025-11-19", "2025-11-20", "2025-11-21",
    "2025-11-24", "2025-11-25", "2025-11-26", "2025-11-27"
]

COMMISSION_RATE = 0.00157 * 1.07  # 0.168%


def load_tick_data(date_str):
    """Load tick data for a specific date"""
    file_path = TICKS_DIR / f"{date_str}.csv"
    if file_path.exists():
        df = pd.read_csv(file_path)
        df = df.rename(columns={
            'ShareCode': 'symbol', 'TradeDateTime': 'timestamp',
            'LastPrice': 'price', 'Volume': 'volume', 'Flag': 'flag'
        })
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[~df['flag'].str.contains('OPEN', na=False)]
        return df
    return None


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


def analyze_buy_trigger_optimization():
    """Analyze different buy trigger percentages to find optimal value"""
    print("Analyzing buy trigger optimization...")

    triggers = [0.990, 0.988, 0.985, 0.982, 0.980, 0.975, 0.970]
    results = {t: {'returns': [], 'trades': [], 'wins': []} for t in triggers}

    # Test on development period
    test_dates = DEV_DATES[:20]  # First 20 days of dev period

    for date in test_dates:
        df = load_tick_data(date)
        if df is None:
            continue

        for trigger in triggers:
            # Simulate strategy with this trigger
            ret, trades, wins = simulate_vwap_strategy(df, trigger)
            results[trigger]['returns'].append(ret)
            results[trigger]['trades'].append(trades)
            results[trigger]['wins'].append(wins)

    # Calculate averages
    summary = []
    for trigger in triggers:
        if results[trigger]['returns']:
            avg_ret = np.mean(results[trigger]['returns'])
            avg_trades = np.mean(results[trigger]['trades'])
            avg_wins = np.mean(results[trigger]['wins'])
            total_trades = sum(results[trigger]['trades'])
            win_rate = sum(results[trigger]['wins']) / total_trades * 100 if total_trades > 0 else 0

            summary.append({
                'trigger': trigger,
                'trigger_pct': (1 - trigger) * 100,
                'avg_return': avg_ret,
                'avg_trades': avg_trades,
                'win_rate': win_rate,
                'total_trades': total_trades
            })

    return pd.DataFrame(summary)


def simulate_vwap_strategy(df, buy_trigger_pct=0.985, position_size=500000):
    """Simulate VWAP mean reversion strategy on single day"""
    capital = 10_000_000
    cash = capital
    positions = {}
    trades = 0
    wins = 0

    symbol_data = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 20)

    for _, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        volume = row['volume']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0 or volume <= 0:
            continue

        if symbol not in symbol_data:
            symbol_data[symbol] = {'vwap_num': 0, 'vwap_den': 0, 'vwap': 0}

        data = symbol_data[symbol]
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        data['vwap'] = data['vwap_num'] / data['vwap_den']

        has_position = symbol in positions and positions[symbol]['volume'] > 0

        if has_position:
            pos = positions[symbol]
            take_profit = data['vwap']
            stop_loss = pos['entry'] * 0.98

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price >= take_profit:
                sell = True
            elif price <= stop_loss:
                sell = True

            if sell:
                tick = get_tick_size(price)
                exit_price = price - tick
                proceeds = pos['volume'] * exit_price * (1 - COMMISSION_RATE)
                pnl = proceeds - pos['cost']

                cash += proceeds
                trades += 1
                if pnl > 0:
                    wins += 1

                del positions[symbol]
        else:
            if current_time >= stop_trades_time:
                continue

            buy_trigger_price = data['vwap'] * buy_trigger_pct

            if price <= buy_trigger_price and cash > position_size:
                tick = get_tick_size(price)
                entry_price = price + tick
                vol = int((position_size / entry_price) // 100 * 100)

                if vol >= 100:
                    cost = vol * entry_price * (1 + COMMISSION_RATE)
                    cash -= cost
                    positions[symbol] = {'volume': vol, 'entry': entry_price, 'cost': cost}

    # Calculate return
    final_value = cash
    for sym, pos in positions.items():
        final_value += pos['volume'] * pos['entry']  # Approximate

    return_pct = (final_value - capital) / capital * 100
    return return_pct, trades, wins


def analyze_eod_vs_overnight():
    """Analyze EOD liquidation vs overnight holding"""
    print("Analyzing EOD vs Overnight holding...")

    results = {'eod': [], 'overnight': []}

    # Use consecutive day pairs from development period
    for i in range(len(DEV_DATES) - 1):
        date1 = DEV_DATES[i]
        date2 = DEV_DATES[i + 1]

        df1 = load_tick_data(date1)
        df2 = load_tick_data(date2)

        if df1 is None or df2 is None:
            continue

        # Calculate overnight gaps
        for symbol in df1['symbol'].unique():
            sym1 = df1[df1['symbol'] == symbol]
            sym2 = df2[df2['symbol'] == symbol]

            if len(sym1) > 0 and len(sym2) > 0:
                close_price = sym1.iloc[-1]['price']
                open_price = sym2.iloc[0]['price']

                gap_pct = (open_price - close_price) / close_price * 100

                results['overnight'].append({
                    'date': date1,
                    'symbol': symbol,
                    'close': close_price,
                    'open': open_price,
                    'gap_pct': gap_pct
                })

    return pd.DataFrame(results['overnight'])


def analyze_strategy_comparison():
    """Compare Mean Reversion vs Momentum vs Trend Following"""
    print("Comparing strategies...")

    results = {
        'Mean Reversion': {'returns': [], 'trades': [], 'wins': []},
        'Momentum': {'returns': [], 'trades': [], 'wins': []},
        'Trend Following': {'returns': [], 'trades': [], 'wins': []}
    }

    test_dates = DEV_DATES[:15]

    for date in test_dates:
        df = load_tick_data(date)
        if df is None:
            continue

        # Mean Reversion
        ret, trades, wins = simulate_vwap_strategy(df, 0.985)
        results['Mean Reversion']['returns'].append(ret)
        results['Mean Reversion']['trades'].append(trades)
        results['Mean Reversion']['wins'].append(wins)

        # Momentum
        ret, trades, wins = simulate_momentum_strategy(df)
        results['Momentum']['returns'].append(ret)
        results['Momentum']['trades'].append(trades)
        results['Momentum']['wins'].append(wins)

        # Trend Following
        ret, trades, wins = simulate_trend_strategy(df)
        results['Trend Following']['returns'].append(ret)
        results['Trend Following']['trades'].append(trades)
        results['Trend Following']['wins'].append(wins)

    summary = []
    for strategy, data in results.items():
        if data['returns']:
            total_trades = sum(data['trades'])
            total_wins = sum(data['wins'])
            summary.append({
                'Strategy': strategy,
                'Avg Return (%)': np.mean(data['returns']),
                'Total Trades': total_trades,
                'Win Rate (%)': total_wins / total_trades * 100 if total_trades > 0 else 0,
                'Std Dev': np.std(data['returns']),
                'Max Return': np.max(data['returns']),
                'Min Return': np.min(data['returns'])
            })

    return pd.DataFrame(summary)


def simulate_momentum_strategy(df, lookback=10, threshold=0.5, position_size=500000):
    """Simulate momentum strategy"""
    capital = 10_000_000
    cash = capital
    positions = {}
    trades = 0
    wins = 0

    symbol_data = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 20)

    for _, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0:
            continue

        if symbol not in symbol_data:
            symbol_data[symbol] = {'prices': []}

        data = symbol_data[symbol]
        data['prices'].append(price)
        if len(data['prices']) > lookback:
            data['prices'] = data['prices'][-lookback:]

        has_position = symbol in positions and positions[symbol]['volume'] > 0

        if has_position:
            pos = positions[symbol]

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif len(data['prices']) >= lookback:
                recent_ret = (price - data['prices'][0]) / data['prices'][0] * 100
                if recent_ret < -threshold:
                    sell = True
            elif price >= pos['entry'] * 1.01:
                sell = True

            if sell:
                tick = get_tick_size(price)
                exit_price = price - tick
                proceeds = pos['volume'] * exit_price * (1 - COMMISSION_RATE)
                pnl = proceeds - pos['cost']

                cash += proceeds
                trades += 1
                if pnl > 0:
                    wins += 1

                del positions[symbol]
        else:
            if current_time >= stop_trades_time:
                continue

            if len(data['prices']) >= lookback and cash > position_size:
                recent_ret = (price - data['prices'][0]) / data['prices'][0] * 100
                if recent_ret > threshold:
                    tick = get_tick_size(price)
                    entry_price = price + tick
                    vol = int((position_size / entry_price) // 100 * 100)

                    if vol >= 100:
                        cost = vol * entry_price * (1 + COMMISSION_RATE)
                        cash -= cost
                        positions[symbol] = {'volume': vol, 'entry': entry_price, 'cost': cost}

    final_value = cash
    for sym, pos in positions.items():
        final_value += pos['volume'] * pos['entry']

    return_pct = (final_value - capital) / capital * 100
    return return_pct, trades, wins


def simulate_trend_strategy(df, ma_period=20, position_size=500000):
    """Simulate trend following strategy"""
    capital = 10_000_000
    cash = capital
    positions = {}
    trades = 0
    wins = 0

    symbol_data = {}

    liquidate_time = time(16, 25)
    stop_trades_time = time(16, 20)

    for _, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        timestamp = row['timestamp']
        current_time = timestamp.time()

        if price <= 0:
            continue

        if symbol not in symbol_data:
            symbol_data[symbol] = {'prices': []}

        data = symbol_data[symbol]
        data['prices'].append(price)
        if len(data['prices']) > ma_period:
            data['prices'] = data['prices'][-ma_period:]

        ma = np.mean(data['prices']) if len(data['prices']) >= ma_period else price

        has_position = symbol in positions and positions[symbol]['volume'] > 0

        if has_position:
            pos = positions[symbol]

            sell = False
            if current_time >= liquidate_time:
                sell = True
            elif price < ma:  # Price crosses below MA
                sell = True

            if sell:
                tick = get_tick_size(price)
                exit_price = price - tick
                proceeds = pos['volume'] * exit_price * (1 - COMMISSION_RATE)
                pnl = proceeds - pos['cost']

                cash += proceeds
                trades += 1
                if pnl > 0:
                    wins += 1

                del positions[symbol]
        else:
            if current_time >= stop_trades_time:
                continue

            if len(data['prices']) >= ma_period and price > ma and cash > position_size:
                tick = get_tick_size(price)
                entry_price = price + tick
                vol = int((position_size / entry_price) // 100 * 100)

                if vol >= 100:
                    cost = vol * entry_price * (1 + COMMISSION_RATE)
                    cash -= cost
                    positions[symbol] = {'volume': vol, 'entry': entry_price, 'cost': cost}

    final_value = cash
    for sym, pos in positions.items():
        final_value += pos['volume'] * pos['entry']

    return_pct = (final_value - capital) / capital * 100
    return return_pct, trades, wins


def analyze_tick_clustering():
    """Analyze tick clustering patterns across all dates"""
    print("Analyzing tick clustering patterns...")

    results = []

    all_dates = DEV_DATES + COMP_DATES

    for date in all_dates:
        df = load_tick_data(date)
        if df is None:
            continue

        total_symbols = 0
        clustered_symbols = 0

        for symbol in df['symbol'].unique():
            sym_df = df[df['symbol'] == symbol]
            unique_prices = len(sym_df['price'].unique())

            total_symbols += 1
            if unique_prices <= 2:
                clustered_symbols += 1

        tcr = clustered_symbols / total_symbols * 100 if total_symbols > 0 else 0

        results.append({
            'date': date,
            'total_symbols': total_symbols,
            'clustered': clustered_symbols,
            'tcr': tcr,
            'is_anomaly': tcr >= 50
        })

    return pd.DataFrame(results)


def plot_buy_trigger_optimization(trigger_df):
    """Plot buy trigger optimization analysis"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Return vs Trigger
    ax1 = axes[0, 0]
    colors = ['green' if r > 0 else 'red' for r in trigger_df['avg_return']]
    bars = ax1.bar(trigger_df['trigger_pct'], trigger_df['avg_return'], color=colors, edgecolor='black')
    ax1.axhline(y=0, color='black', linewidth=0.5)
    ax1.set_xlabel('Buy Trigger (% below VWAP)')
    ax1.set_ylabel('Average Daily Return (%)')
    ax1.set_title('Return vs Buy Trigger Threshold', fontweight='bold')

    # Highlight optimal
    optimal_idx = trigger_df['avg_return'].idxmax()
    ax1.get_children()[optimal_idx].set_color('gold')
    ax1.get_children()[optimal_idx].set_edgecolor('black')
    ax1.get_children()[optimal_idx].set_linewidth(2)

    # Add annotation
    optimal = trigger_df.iloc[optimal_idx]
    ax1.annotate(f'Optimal: {optimal["trigger_pct"]:.1f}%\nReturn: {optimal["avg_return"]:.2f}%',
                xy=(optimal['trigger_pct'], optimal['avg_return']),
                xytext=(optimal['trigger_pct'] + 0.5, optimal['avg_return'] + 0.3),
                fontsize=10, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='black'))

    # Trade count vs Trigger
    ax2 = axes[0, 1]
    ax2.bar(trigger_df['trigger_pct'], trigger_df['avg_trades'], color='steelblue', edgecolor='black')
    ax2.set_xlabel('Buy Trigger (% below VWAP)')
    ax2.set_ylabel('Average Trades per Day')
    ax2.set_title('Trade Frequency vs Buy Trigger', fontweight='bold')

    # Win rate vs Trigger
    ax3 = axes[1, 0]
    ax3.bar(trigger_df['trigger_pct'], trigger_df['win_rate'], color='seagreen', edgecolor='black')
    ax3.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50% baseline')
    ax3.set_xlabel('Buy Trigger (% below VWAP)')
    ax3.set_ylabel('Win Rate (%)')
    ax3.set_title('Win Rate vs Buy Trigger', fontweight='bold')
    ax3.legend()

    # Risk-Reward tradeoff
    ax4 = axes[1, 1]
    scatter = ax4.scatter(trigger_df['avg_trades'], trigger_df['avg_return'],
                          c=trigger_df['win_rate'], cmap='RdYlGn', s=200, edgecolors='black')

    for idx, row in trigger_df.iterrows():
        ax4.annotate(f"{row['trigger_pct']:.1f}%",
                    (row['avg_trades'], row['avg_return']),
                    textcoords="offset points", xytext=(5, 5), fontsize=9)

    ax4.set_xlabel('Average Trades per Day')
    ax4.set_ylabel('Average Daily Return (%)')
    ax4.set_title('Risk-Reward Tradeoff by Trigger', fontweight='bold')
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.3)

    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('Win Rate (%)')

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '20_buy_trigger_optimization.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 20_buy_trigger_optimization.png")


def plot_eod_analysis(overnight_df):
    """Plot EOD vs Overnight analysis"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Overnight gap distribution
    ax1 = axes[0, 0]
    ax1.hist(overnight_df['gap_pct'], bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    ax1.axvline(x=0, color='red', linestyle='--', linewidth=2, label='No Gap')
    ax1.axvline(x=overnight_df['gap_pct'].mean(), color='green', linestyle='-', linewidth=2,
                label=f'Mean: {overnight_df["gap_pct"].mean():.2f}%')
    ax1.set_xlabel('Overnight Gap (%)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of Overnight Price Gaps', fontweight='bold')
    ax1.legend()

    # Gap risk by magnitude
    ax2 = axes[0, 1]
    gaps_negative = overnight_df[overnight_df['gap_pct'] < 0]['gap_pct']
    gaps_positive = overnight_df[overnight_df['gap_pct'] > 0]['gap_pct']

    data = [gaps_negative, gaps_positive]
    bp = ax2.boxplot(data, labels=['Negative Gaps', 'Positive Gaps'], patch_artist=True)
    bp['boxes'][0].set_facecolor('red')
    bp['boxes'][1].set_facecolor('green')
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.3)
    ax2.set_ylabel('Gap Magnitude (%)')
    ax2.set_title('Overnight Gap Risk Analysis', fontweight='bold')

    # Statistics text
    stats_text = f"""
    Overnight Gap Statistics:
    ─────────────────────────
    Total Observations: {len(overnight_df):,}

    Negative Gaps:
    • Count: {len(gaps_negative):,} ({len(gaps_negative)/len(overnight_df)*100:.1f}%)
    • Mean: {gaps_negative.mean():.2f}%
    • Max Loss: {gaps_negative.min():.2f}%

    Positive Gaps:
    • Count: {len(gaps_positive):,} ({len(gaps_positive)/len(overnight_df)*100:.1f}%)
    • Mean: {gaps_positive.mean():.2f}%
    • Max Gain: {gaps_positive.max():.2f}%
    """

    ax3 = axes[1, 0]
    ax3.axis('off')
    ax3.text(0.1, 0.5, stats_text, transform=ax3.transAxes, fontsize=11,
             verticalalignment='center', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    ax3.set_title('Overnight Risk Statistics', fontweight='bold')

    # EOD vs Overnight comparison
    ax4 = axes[1, 1]

    # Calculate risk metrics
    eod_risk = 0  # No overnight exposure
    overnight_risk = np.std(overnight_df['gap_pct'])
    max_overnight_loss = abs(overnight_df['gap_pct'].min())

    strategies = ['EOD Liquidation', 'Overnight Hold']
    overnight_exposure = [0, overnight_risk]
    max_loss_risk = [0, max_overnight_loss]

    x = np.arange(len(strategies))
    width = 0.35

    bars1 = ax4.bar(x - width/2, overnight_exposure, width, label='Overnight Vol (%)', color='steelblue')
    bars2 = ax4.bar(x + width/2, max_loss_risk, width, label='Max Overnight Loss (%)', color='coral')

    ax4.set_ylabel('Risk (%)')
    ax4.set_title('EOD vs Overnight Risk Comparison', fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(strategies)
    ax4.legend()

    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax4.annotate(f'{height:.2f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', fontsize=10)
    for bar in bars2:
        height = bar.get_height()
        ax4.annotate(f'{height:.2f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '21_eod_vs_overnight.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 21_eod_vs_overnight.png")


def plot_strategy_comparison(comparison_df):
    """Plot strategy comparison"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    strategies = comparison_df['Strategy'].tolist()

    # Average return comparison
    ax1 = axes[0, 0]
    colors = ['green' if r > 0 else 'red' for r in comparison_df['Avg Return (%)']]
    bars = ax1.bar(strategies, comparison_df['Avg Return (%)'], color=colors, edgecolor='black')
    ax1.axhline(y=0, color='black', linewidth=0.5)
    ax1.set_ylabel('Average Daily Return (%)')
    ax1.set_title('Strategy Returns Comparison\n(Development Period)', fontweight='bold')

    # Add value labels
    for bar, val in zip(bars, comparison_df['Avg Return (%)']):
        ax1.annotate(f'{val:.2f}%', xy=(bar.get_x() + bar.get_width()/2, val),
                    xytext=(0, 3 if val >= 0 else -12), textcoords="offset points",
                    ha='center', fontsize=10, fontweight='bold')

    # Win rate comparison
    ax2 = axes[0, 1]
    bars = ax2.bar(strategies, comparison_df['Win Rate (%)'], color='steelblue', edgecolor='black')
    ax2.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50% baseline')
    ax2.set_ylabel('Win Rate (%)')
    ax2.set_title('Win Rate Comparison', fontweight='bold')
    ax2.legend()

    for bar, val in zip(bars, comparison_df['Win Rate (%)']):
        ax2.annotate(f'{val:.1f}%', xy=(bar.get_x() + bar.get_width()/2, val),
                    xytext=(0, 3), textcoords="offset points", ha='center', fontsize=10)

    # Risk (Std Dev) comparison
    ax3 = axes[1, 0]
    bars = ax3.bar(strategies, comparison_df['Std Dev'], color='coral', edgecolor='black')
    ax3.set_ylabel('Return Std Dev (%)')
    ax3.set_title('Risk (Volatility) Comparison', fontweight='bold')

    # Return range
    ax4 = axes[1, 1]
    for i, (_, row) in enumerate(comparison_df.iterrows()):
        ax4.plot([i, i], [row['Min Return'], row['Max Return']], 'ko-', linewidth=2, markersize=8)
        ax4.plot(i, row['Avg Return (%)'], 'g^', markersize=12, label='Avg' if i == 0 else '')

    ax4.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax4.set_xticks(range(len(strategies)))
    ax4.set_xticklabels(strategies)
    ax4.set_ylabel('Return (%)')
    ax4.set_title('Return Range (Min-Max)', fontweight='bold')

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '22_strategy_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 22_strategy_comparison.png")


def plot_tick_clustering_analysis(tcr_df):
    """Plot tick clustering ratio analysis"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # TCR over time
    ax1 = axes[0, 0]
    colors = ['red' if a else 'steelblue' for a in tcr_df['is_anomaly']]
    ax1.bar(range(len(tcr_df)), tcr_df['tcr'], color=colors, edgecolor='black', alpha=0.7)
    ax1.axhline(y=50, color='red', linestyle='--', linewidth=2, label='Anomaly Threshold (50%)')
    ax1.set_xlabel('Trading Day')
    ax1.set_ylabel('Tick Clustering Ratio (%)')
    ax1.set_title('Tick Clustering Ratio Over Time', fontweight='bold')
    ax1.legend()

    # Mark development vs competition
    dev_end = len(DEV_DATES)
    ax1.axvline(x=dev_end - 0.5, color='green', linestyle='-', linewidth=2, alpha=0.7)
    ax1.text(dev_end - 5, ax1.get_ylim()[1] * 0.9, 'Development', fontsize=10, color='green')
    ax1.text(dev_end + 2, ax1.get_ylim()[1] * 0.9, 'Competition', fontsize=10, color='blue')

    # TCR distribution
    ax2 = axes[0, 1]
    ax2.hist(tcr_df['tcr'], bins=20, color='steelblue', edgecolor='black', alpha=0.7)
    ax2.axvline(x=50, color='red', linestyle='--', linewidth=2, label='Anomaly Threshold')
    ax2.set_xlabel('Tick Clustering Ratio (%)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('TCR Distribution', fontweight='bold')
    ax2.legend()

    # Anomaly detection
    ax3 = axes[1, 0]
    anomaly_count = tcr_df['is_anomaly'].sum()
    normal_count = len(tcr_df) - anomaly_count

    sizes = [normal_count, anomaly_count]
    labels = [f'Normal Days\n({normal_count})', f'Anomaly Days\n({anomaly_count})']
    colors = ['steelblue', 'red']
    explode = (0, 0.1)

    ax3.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax3.set_title('Day Type Distribution', fontweight='bold')

    # Anomaly dates
    ax4 = axes[1, 1]
    ax4.axis('off')

    anomaly_dates = tcr_df[tcr_df['is_anomaly']]['date'].tolist()

    text = """
    ANOMALY DAYS DETECTED
    ═════════════════════════════════════════

    Dates with TCR ≥ 50%:
    """

    for date in anomaly_dates:
        row = tcr_df[tcr_df['date'] == date].iloc[0]
        text += f"\n    • {date}: TCR = {row['tcr']:.1f}%"

    text += """

    ═════════════════════════════════════════

    KEY INSIGHT:
    Anomaly days are characterized by extreme
    tick clustering where most stocks trade
    at only 1-2 price levels, creating ideal
    conditions for mean reversion.
    """

    ax4.text(0.1, 0.5, text, transform=ax4.transAxes, fontsize=11,
             verticalalignment='center', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '23_tick_clustering_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 23_tick_clustering_analysis.png")


def plot_vwap_explanation():
    """Create VWAP explanation visualization"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Simulated price and VWAP
    np.random.seed(42)
    n_points = 100
    t = np.linspace(0, 1, n_points)

    # Base price with random walk
    price = 100 + np.cumsum(np.random.randn(n_points) * 0.3)

    # Simulated volume
    volume = np.random.uniform(1000, 5000, n_points)

    # Calculate VWAP
    cum_pv = np.cumsum(price * volume)
    cum_v = np.cumsum(volume)
    vwap = cum_pv / cum_v

    # Buy trigger
    buy_trigger = vwap * 0.985

    ax1 = axes[0]
    ax1.plot(t, price, 'b-', linewidth=1.5, label='Price', alpha=0.8)
    ax1.plot(t, vwap, 'r-', linewidth=2, label='VWAP')
    ax1.plot(t, buy_trigger, 'g--', linewidth=1.5, label='Buy Trigger (VWAP - 1.5%)')
    ax1.fill_between(t, buy_trigger, price, where=(price <= buy_trigger),
                     color='green', alpha=0.3, label='Buy Zone')

    ax1.set_xlabel('Time (Trading Session)')
    ax1.set_ylabel('Price (THB)')
    ax1.set_title('VWAP Mean Reversion Strategy Visualization', fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # Add annotations
    buy_points = np.where(price <= buy_trigger)[0]
    if len(buy_points) > 0:
        first_buy = buy_points[0]
        ax1.annotate('BUY Signal', xy=(t[first_buy], price[first_buy]),
                    xytext=(t[first_buy] + 0.1, price[first_buy] - 2),
                    fontsize=10, color='green', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='green'))

    # VWAP explanation
    ax2 = axes[1]
    ax2.axis('off')

    explanation = """
    VWAP (Volume Weighted Average Price)
    ════════════════════════════════════════════════════════

    FORMULA:
    ┌─────────────────────────────────────────────────────┐
    │                 Σ (Price × Volume)                  │
    │   VWAP  =  ─────────────────────────                │
    │                    Σ Volume                         │
    └─────────────────────────────────────────────────────┘

    INTERPRETATION:
    • VWAP represents the "fair value" of a stock
    • Weighted by trading volume (more volume = more weight)
    • Institutional traders often use VWAP as benchmark
    • Prices tend to revert to VWAP throughout the day

    STRATEGY LOGIC:
    ┌─────────────────────────────────────────────────────┐
    │  BUY when:  Price ≤ VWAP × 0.985 (1.5% discount)   │
    │  SELL when: Price ≥ VWAP (back to fair value)      │
    │  STOP when: Price ≤ Entry × 0.98 (2% loss limit)   │
    └─────────────────────────────────────────────────────┘

    WHY IT WORKS:
    • Prices deviate from VWAP due to temporary imbalances
    • These deviations usually correct within the day
    • Buy low, sell at fair value = consistent profits
    """

    ax2.text(0.05, 0.5, explanation, transform=ax2.transAxes, fontsize=11,
             verticalalignment='center', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.8))

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '24_vwap_explanation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 24_vwap_explanation.png")


def plot_final_performance_summary():
    """Plot final competition performance summary"""
    fig = plt.figure(figsize=(16, 12))

    # Create grid
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # Load competition results
    comp_results = pd.read_csv('result/FemboyLover/FemboyLover_portfolio_summary.csv')

    # NAV progression
    ax1 = fig.add_subplot(gs[0, :2])
    dates = pd.to_datetime(comp_results['Daily Ticks Time']).dt.strftime('%m-%d')
    ax1.plot(dates, comp_results['Net Asset Value'] / 1e6, 'b-o', linewidth=2, markersize=6)
    ax1.axhline(y=10, color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
    ax1.fill_between(dates, 10, comp_results['Net Asset Value'] / 1e6, alpha=0.3)
    ax1.set_xlabel('Date')
    ax1.set_ylabel('NAV (Million THB)')
    ax1.set_title('Portfolio Net Asset Value Progression', fontweight='bold', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

    # Key metrics box
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.axis('off')

    final = comp_results.iloc[-1]
    metrics_text = f"""
    FINAL RESULTS
    ═══════════════════════

    Return:     {final['Return rate']:.2f}%
    Final NAV:  {final['Net Asset Value']/1e6:.2f}M
    Max DD:     {final['Max Drawdown (%)']:.2f}%
    Calmar:     {final['Calmar Ratio']:.2f}

    Trades:     {final['Number of Sells']:.0f}
    Wins:       {final['Number of Wins']:.0f}
    Win Rate:   {final['Win Rate']:.1f}%
    """

    ax2.text(0.1, 0.5, metrics_text, transform=ax2.transAxes, fontsize=12,
             verticalalignment='center', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

    # Daily returns
    ax3 = fig.add_subplot(gs[1, 0])
    daily_returns = comp_results['Return rate'].diff().fillna(comp_results['Return rate'].iloc[0])
    colors = ['green' if r >= 0 else 'red' for r in daily_returns]
    ax3.bar(range(len(daily_returns)), daily_returns, color=colors, edgecolor='black')
    ax3.axhline(y=0, color='black', linewidth=0.5)
    ax3.set_xlabel('Day')
    ax3.set_ylabel('Daily Return (%)')
    ax3.set_title('Daily Returns', fontweight='bold')

    # Win rate progression
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.plot(dates, comp_results['Win Rate'], 'g-o', linewidth=2, markersize=4)
    ax4.axhline(y=80, color='gold', linestyle='--', alpha=0.7, label='80% target')
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Win Rate (%)')
    ax4.set_title('Win Rate Progression', fontweight='bold')
    ax4.legend()
    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)

    # Trade distribution
    ax5 = fig.add_subplot(gs[1, 2])
    daily_trades = comp_results['Number of Sells'].diff().fillna(comp_results['Number of Sells'].iloc[0])
    ax5.bar(range(len(daily_trades)), daily_trades, color='steelblue', edgecolor='black')
    ax5.set_xlabel('Day')
    ax5.set_ylabel('Trades')
    ax5.set_title('Daily Trade Count', fontweight='bold')

    # Competition requirements check
    ax6 = fig.add_subplot(gs[2, :])
    ax6.axis('off')

    req_text = """
    ╔════════════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                              COMPETITION REQUIREMENTS CHECK                                         ║
    ╠════════════════════════════════════════════════════════════════════════════════════════════════════╣
    ║                                                                                                     ║
    ║   Requirement                          Target          Achieved              Status                 ║
    ║   ─────────────────────────────────────────────────────────────────────────────────────────────    ║
    """

    requirements = [
        ("Return Rate", "> 5%", f"{final['Return rate']:.2f}%", final['Return rate'] > 5),
        ("Max Drawdown", "< 30%", f"{abs(final['Max Drawdown (%)']):.2f}%", abs(final['Max Drawdown (%)']) < 30),
        ("Total Trades", "> 20", f"{final['Number of Sells']:.0f}", final['Number of Sells'] > 20),
        ("Win Rate", "> 20%", f"{final['Win Rate']:.1f}%", final['Win Rate'] > 20),
    ]

    for req, target, achieved, passed in requirements:
        status = "✅ PASS" if passed else "❌ FAIL"
        req_text += f"║   {req:<30} {target:<15} {achieved:<20} {status:<20}    ║\n"

    req_text += """║                                                                                                     ║
    ╚════════════════════════════════════════════════════════════════════════════════════════════════════╝
    """

    ax6.text(0.5, 0.5, req_text, transform=ax6.transAxes, fontsize=10,
             verticalalignment='center', horizontalalignment='center',
             fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.savefig(FIGURES_DIR / '25_final_performance_summary.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 25_final_performance_summary.png")


def main():
    print("=" * 70)
    print("FINAL REPORT ANALYSIS - Generating Visualizations")
    print("=" * 70)

    # 1. Buy trigger optimization
    print("\n[1/6] Analyzing buy trigger optimization...")
    trigger_df = analyze_buy_trigger_optimization()
    plot_buy_trigger_optimization(trigger_df)
    print(trigger_df.to_string(index=False))

    # 2. EOD vs Overnight analysis
    print("\n[2/6] Analyzing EOD vs Overnight holding...")
    overnight_df = analyze_eod_vs_overnight()
    plot_eod_analysis(overnight_df)

    # 3. Strategy comparison
    print("\n[3/6] Comparing strategies...")
    comparison_df = analyze_strategy_comparison()
    plot_strategy_comparison(comparison_df)
    print(comparison_df.to_string(index=False))

    # 4. Tick clustering analysis
    print("\n[4/6] Analyzing tick clustering...")
    tcr_df = analyze_tick_clustering()
    plot_tick_clustering_analysis(tcr_df)

    # 5. VWAP explanation
    print("\n[5/6] Creating VWAP explanation...")
    plot_vwap_explanation()

    # 6. Final performance summary
    print("\n[6/6] Creating final performance summary...")
    plot_final_performance_summary()

    print("\n" + "=" * 70)
    print("All visualizations generated successfully!")
    print(f"Figures saved to: {FIGURES_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
