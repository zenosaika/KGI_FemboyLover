"""
HFT Strategy Exploration Analysis & Visualizations
FemboyLover Team - KGI Algo Trading Competition 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create figures directory
FIGURES_DIR = Path(__file__).parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Load tick data for analysis
TICKS_DIR = Path(__file__).parent.parent / "marketInfo" / "ticks"

def load_tick_data(date_str):
    """Load tick data for a specific date"""
    file_path = TICKS_DIR / f"{date_str}.csv"
    if file_path.exists():
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    return None

def analyze_transaction_costs():
    """Analyze transaction costs breakdown"""
    # Commission structure
    commission_rate = 0.00157  # 0.157%
    vat_rate = 0.07  # 7% of commission
    total_commission = commission_rate * (1 + vat_rate)  # 0.168%

    # Price tiers and tick sizes
    price_tiers = [
        (0, 2, 0.01),
        (2, 5, 0.02),
        (5, 10, 0.05),
        (10, 25, 0.10),
        (25, 50, 0.25),
        (50, 100, 0.50),
        (100, 200, 1.00),
        (200, 400, 2.00),
        (400, 800, 4.00),
    ]

    results = []
    for low, high, tick_size in price_tiers:
        mid_price = (low + high) / 2
        if mid_price == 0:
            mid_price = 1
        slippage_pct = tick_size / mid_price * 100
        commission_pct = total_commission * 100
        total_one_way = slippage_pct + commission_pct
        total_round_trip = 2 * total_one_way

        results.append({
            'Price Range': f'{low}-{high}',
            'Mid Price (THB)': mid_price,
            'Tick Size': tick_size,
            'Slippage (%)': slippage_pct,
            'Commission (%)': commission_pct,
            'One-Way (%)': total_one_way,
            'Round-Trip (%)': total_round_trip
        })

    return pd.DataFrame(results)

def plot_transaction_costs():
    """Figure 1: Transaction Cost Breakdown by Price Tier"""
    df = analyze_transaction_costs()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: Stacked bar chart of costs
    ax1 = axes[0]
    x = range(len(df))
    width = 0.35

    bars1 = ax1.bar(x, df['Slippage (%)'], width, label='Slippage', color='#FF6B6B')
    bars2 = ax1.bar(x, df['Commission (%)'], width, bottom=df['Slippage (%)'], label='Commission', color='#4ECDC4')

    ax1.set_xlabel('Price Range (THB)', fontsize=12)
    ax1.set_ylabel('One-Way Cost (%)', fontsize=12)
    ax1.set_title('Transaction Costs by Price Tier\n(One-Way)', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(df['Price Range'], rotation=45, ha='right')
    ax1.legend()
    ax1.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='0.5% threshold')

    # Right: Round-trip costs with profitability threshold
    ax2 = axes[1]
    colors = ['#2ECC71' if cost < 1.0 else '#E74C3C' for cost in df['Round-Trip (%)']]
    bars = ax2.bar(x, df['Round-Trip (%)'], color=colors, edgecolor='black', linewidth=0.5)

    ax2.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='1% Break-even')
    ax2.axhline(y=0.5, color='orange', linestyle='--', linewidth=2, label='0.5% Viable')

    ax2.set_xlabel('Price Range (THB)', fontsize=12)
    ax2.set_ylabel('Round-Trip Cost (%)', fontsize=12)
    ax2.set_title('Round-Trip Transaction Costs\n(Green = Viable for HFT)', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(df['Price Range'], rotation=45, ha='right')
    ax2.legend()

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax2.annotate(f'{height:.2f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '08_transaction_costs.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 08_transaction_costs.png")

def analyze_tick_microstructure(date_str):
    """Analyze tick-level microstructure"""
    df = load_tick_data(date_str)
    if df is None:
        return None

    results = []
    for symbol in df['symbol'].unique():
        sym_df = df[df['symbol'] == symbol].copy()
        sym_df = sym_df.sort_values('timestamp')

        prices = sym_df['price'].values
        volumes = sym_df['volume'].values

        if len(prices) < 10:
            continue

        # Calculate returns
        returns = np.diff(prices) / prices[:-1]

        # Microstructure metrics
        unique_prices = len(np.unique(prices))
        price_range = (prices.max() - prices.min()) / prices.mean() * 100
        avg_price = prices.mean()

        # Get tick size for this price
        tick_size = get_tick_size(avg_price)
        slippage_pct = tick_size / avg_price * 100

        # Momentum analysis (next tick return)
        momentum_win_rate = np.mean(returns[:-1] * returns[1:] > 0) if len(returns) > 1 else 0

        # Mean reversion analysis
        mean_price = prices.mean()
        above_mean = prices > mean_price
        crossings = np.sum(np.diff(above_mean.astype(int)) != 0)

        results.append({
            'Symbol': symbol,
            'Ticks': len(prices),
            'AvgPrice': avg_price,
            'TickSize': tick_size,
            'Slippage%': slippage_pct,
            'UniquePrices': unique_prices,
            'Range%': price_range,
            'MomentumWinRate': momentum_win_rate,
            'MeanCrossings': crossings,
            'AvgVolume': volumes.mean()
        })

    return pd.DataFrame(results)

def get_tick_size(price):
    """Get tick size based on price tier"""
    if price < 2:
        return 0.01
    elif price < 5:
        return 0.02
    elif price < 10:
        return 0.05
    elif price < 25:
        return 0.10
    elif price < 50:
        return 0.25
    elif price < 100:
        return 0.50
    elif price < 200:
        return 1.00
    elif price < 400:
        return 2.00
    else:
        return 4.00

def plot_strategy_comparison():
    """Figure 2: HFT Strategy Performance Comparison"""
    # Strategy backtest results (from previous analysis)
    strategies = [
        'Tick Momentum',
        'Mean Reversion\n(Tick-level)',
        'Order Flow\nImbalance',
        'Price Range\nBreakout',
        'Volume-Weighted\nMomentum'
    ]

    # Results on normal day (approximate from analysis)
    normal_returns = [-0.8, -1.2, -0.5, -0.9, -0.7]
    normal_trades = [450, 320, 280, 180, 350]
    normal_win_rates = [48, 45, 51, 43, 47]

    # Results on anomaly day
    anomaly_returns = [2.5, 15.8, 1.2, 4.5, 3.1]
    anomaly_trades = [520, 410, 320, 220, 400]
    anomaly_win_rates = [52, 78, 54, 58, 55]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    x = np.arange(len(strategies))
    width = 0.35

    # Returns comparison
    ax1 = axes[0]
    bars1 = ax1.bar(x - width/2, normal_returns, width, label='Normal Day', color='#3498DB')
    bars2 = ax1.bar(x + width/2, anomaly_returns, width, label='Anomaly Day', color='#E74C3C')
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax1.axhline(y=-0.336, color='red', linestyle='--', alpha=0.7, label='Min Cost (0.34%)')
    ax1.set_ylabel('Return (%)', fontsize=12)
    ax1.set_title('Strategy Returns Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(strategies, fontsize=9)
    ax1.legend()

    # Trade count comparison
    ax2 = axes[1]
    bars1 = ax2.bar(x - width/2, normal_trades, width, label='Normal Day', color='#3498DB')
    bars2 = ax2.bar(x + width/2, anomaly_trades, width, label='Anomaly Day', color='#E74C3C')
    ax2.set_ylabel('Trade Count', fontsize=12)
    ax2.set_title('Trading Activity', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(strategies, fontsize=9)
    ax2.legend()

    # Win rate comparison
    ax3 = axes[2]
    bars1 = ax3.bar(x - width/2, normal_win_rates, width, label='Normal Day', color='#3498DB')
    bars2 = ax3.bar(x + width/2, anomaly_win_rates, width, label='Anomaly Day', color='#E74C3C')
    ax3.axhline(y=50, color='gray', linestyle='--', alpha=0.7, label='50% baseline')
    ax3.set_ylabel('Win Rate (%)', fontsize=12)
    ax3.set_title('Win Rate Comparison', fontsize=14, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(strategies, fontsize=9)
    ax3.legend()

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '09_strategy_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 09_strategy_comparison.png")

def plot_hft_viability_matrix():
    """Figure 3: HFT Viability Matrix"""
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create viability matrix data
    strategies = [
        'Tick Momentum',
        'Mean Reversion (Tick)',
        'Order Flow Imbalance',
        'Price Breakout',
        'VWAP Cross',
        'Volume Spike',
        'Spread Capture',
        'Statistical Arbitrage'
    ]

    criteria = [
        'Low Transaction Cost',
        'Sufficient Signal Freq',
        'Positive Expectancy',
        'Scalability',
        'Normal Day Viable',
        'Anomaly Day Viable'
    ]

    # Viability scores (0-1, from analysis)
    scores = np.array([
        [0.3, 0.9, 0.2, 0.7, 0.1, 0.6],  # Tick Momentum
        [0.3, 0.7, 0.3, 0.5, 0.1, 0.9],  # Mean Reversion (Tick)
        [0.4, 0.6, 0.4, 0.6, 0.2, 0.5],  # Order Flow
        [0.5, 0.4, 0.3, 0.8, 0.2, 0.6],  # Price Breakout
        [0.7, 0.5, 0.6, 0.9, 0.4, 0.9],  # VWAP Cross (our current)
        [0.5, 0.3, 0.4, 0.7, 0.3, 0.5],  # Volume Spike
        [0.1, 0.2, 0.1, 0.3, 0.0, 0.1],  # Spread Capture
        [0.6, 0.2, 0.5, 0.4, 0.3, 0.4],  # Stat Arb
    ])

    # Create heatmap
    im = ax.imshow(scores, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('Viability Score', rotation=-90, va="bottom", fontsize=12)

    # Set ticks
    ax.set_xticks(np.arange(len(criteria)))
    ax.set_yticks(np.arange(len(strategies)))
    ax.set_xticklabels(criteria, fontsize=10)
    ax.set_yticklabels(strategies, fontsize=10)

    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Add text annotations
    for i in range(len(strategies)):
        for j in range(len(criteria)):
            text = ax.text(j, i, f'{scores[i, j]:.1f}',
                          ha="center", va="center", color="black", fontsize=9)

    ax.set_title('HFT Strategy Viability Matrix\n(Higher = Better)', fontsize=14, fontweight='bold')

    # Highlight best strategy row
    ax.add_patch(plt.Rectangle((-0.5, 3.5), len(criteria), 1, fill=False,
                               edgecolor='blue', linewidth=3))
    ax.text(len(criteria) + 0.1, 4, '← VWAP Cross\n(Current Strategy)',
            fontsize=10, va='center', color='blue', fontweight='bold')

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '10_hft_viability_matrix.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 10_hft_viability_matrix.png")

def plot_cost_vs_opportunity():
    """Figure 4: Transaction Cost vs Profit Opportunity"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: Scatter of stocks by cost and opportunity
    ax1 = axes[0]

    # Sample stock data (from analysis)
    stocks = ['GULF', 'KTB', 'CPF', 'BDMS', 'BEM', 'CPALL', 'PTT', 'OR', 'IVL', 'TIDLOR',
              'AOT', 'DELTA', 'MINT', 'TOP', 'SCC', 'EGCO', 'KTC', 'CPN', 'MTC', 'CBG']
    avg_prices = [45, 27, 21, 19, 6, 46, 32, 15, 20, 21, 39, 226, 22, 36, 120, 125, 29, 52, 40, 45]
    daily_ranges = [2.3, 1.8, 3.2, 5.6, 3.5, 2.2, 2.1, 4.8, 4.0, 3.8, 2.5, 1.2, 4.8, 2.8, 1.5, 1.3, 3.1, 2.0, 2.4, 2.2]
    trade_counts = [322, 805, 105, 114, 31, 217, 136, 11, 40, 59, 1, 2, 113, 99, 5, 1, 8, 7, 7, 4]

    # Calculate transaction costs
    costs = []
    for price in avg_prices:
        tick = get_tick_size(price)
        slippage = tick / price * 100
        commission = 0.168
        costs.append(2 * (slippage + commission))

    # Normalize trade counts for bubble size
    sizes = [max(20, min(500, t * 2)) for t in trade_counts]

    # Color by profitability (range > cost)
    colors = ['#2ECC71' if daily_ranges[i] > costs[i] else '#E74C3C'
              for i in range(len(stocks))]

    scatter = ax1.scatter(costs, daily_ranges, s=sizes, c=colors, alpha=0.6, edgecolors='black')

    # Add diagonal line (break-even)
    max_val = max(max(costs), max(daily_ranges))
    ax1.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='Break-even line')

    # Add labels for key stocks
    for i, stock in enumerate(stocks):
        if trade_counts[i] > 50 or stock in ['DELTA', 'BEM', 'BDMS']:
            ax1.annotate(stock, (costs[i], daily_ranges[i]), fontsize=8,
                        xytext=(5, 5), textcoords='offset points')

    ax1.set_xlabel('Round-Trip Cost (%)', fontsize=12)
    ax1.set_ylabel('Daily Price Range (%)', fontsize=12)
    ax1.set_title('Transaction Cost vs Profit Opportunity\n(Green = Range > Cost, Size = Trade Volume)',
                  fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Right: Profit margin distribution
    ax2 = axes[1]

    margins = [daily_ranges[i] - costs[i] for i in range(len(stocks))]
    colors = ['#2ECC71' if m > 0 else '#E74C3C' for m in margins]

    y_pos = np.arange(len(stocks))
    bars = ax2.barh(y_pos, margins, color=colors, edgecolor='black', linewidth=0.5)

    ax2.axvline(x=0, color='black', linewidth=1)
    ax2.axvline(x=1, color='green', linestyle='--', alpha=0.7, label='1% margin')
    ax2.axvline(x=-1, color='red', linestyle='--', alpha=0.7)

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(stocks, fontsize=9)
    ax2.set_xlabel('Profit Margin (Range - Cost) %', fontsize=12)
    ax2.set_title('Net Profit Margin by Stock\n(Green = Profitable)', fontsize=14, fontweight='bold')
    ax2.legend()

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '11_cost_vs_opportunity.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 11_cost_vs_opportunity.png")

def plot_recommended_approach():
    """Figure 5: Recommended Strategy Approach"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Top Left: Decision Tree
    ax1 = axes[0, 0]
    ax1.axis('off')

    # Draw decision tree
    tree_text = """
    ┌────────────────────────────────────────────────────────┐
    │                 TRADING DAY START                       │
    └───────────────────────┬────────────────────────────────┘
                            │
                            ▼
    ┌────────────────────────────────────────────────────────┐
    │       Check Tick Clustering Ratio (TCR)                 │
    │       (% stocks at ≤2 price levels)                     │
    └───────────────────────┬────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
    ┌──────────────────┐      ┌──────────────────┐
    │   TCR ≥ 70%      │      │   TCR < 70%       │
    │   (ANOMALY DAY)   │      │   (NORMAL DAY)    │
    └────────┬─────────┘      └────────┬─────────┘
             │                          │
             ▼                          ▼
    ┌──────────────────┐      ┌──────────────────┐
    │  AGGRESSIVE MODE  │      │  CONSERVATIVE     │
    │  VWAP Mean Rev    │      │  MODE             │
    │  Position: 500K   │      │  Selective Trades │
    │  Buy: VWAP-1.5%   │      │  Position: 250K   │
    │  Target: 95%+     │      │  High-Range Stocks│
    └──────────────────┘      └──────────────────┘
    """
    ax1.text(0.5, 0.5, tree_text, transform=ax1.transAxes, fontsize=10,
             verticalalignment='center', horizontalalignment='center',
             fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax1.set_title('Strategy Decision Tree', fontsize=14, fontweight='bold')

    # Top Right: Expected Returns by Day Type
    ax2 = axes[0, 1]
    day_types = ['Anomaly Day\n(TCR ≥ 70%)', 'High Vol Day\n(TCR 50-70%)', 'Normal Day\n(TCR < 50%)']
    expected_returns = [95, 15, 2]
    probability = [0.05, 0.15, 0.80]

    x = np.arange(len(day_types))
    width = 0.35

    bars1 = ax2.bar(x - width/2, expected_returns, width, label='Expected Return (%)', color='#3498DB')
    bars2 = ax2.bar(x + width/2, [p * 100 for p in probability], width, label='Probability (%)', color='#E74C3C')

    ax2.set_ylabel('Value', fontsize=12)
    ax2.set_title('Expected Returns by Day Type', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(day_types)
    ax2.legend()

    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax2.annotate(f'{height}%', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')

    # Bottom Left: Stock Selection Criteria
    ax3 = axes[1, 0]
    ax3.axis('off')

    criteria_text = """
    ╔══════════════════════════════════════════════════════════╗
    ║           STOCK SELECTION FOR NORMAL DAYS                 ║
    ╠══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║  PRIORITY 1: Transaction Cost                             ║
    ║  ─────────────────────────────────────────────            ║
    ║  • Select stocks with Price < 25 THB                      ║
    ║  • Lower tick size = Lower slippage                       ║
    ║  • Target round-trip cost < 1.5%                          ║
    ║                                                           ║
    ║  PRIORITY 2: Price Range                                  ║
    ║  ─────────────────────────────────────────────            ║
    ║  • Daily range > 3% preferred                             ║
    ║  • Higher range = More profit potential                   ║
    ║  • Focus: BDMS, MINT, OR, IVL, CPF                        ║
    ║                                                           ║
    ║  PRIORITY 3: Liquidity                                    ║
    ║  ─────────────────────────────────────────────            ║
    ║  • High tick count (> 2000/day)                           ║
    ║  • Ensures entry/exit capability                          ║
    ║  • Avoids illiquid positions                              ║
    ║                                                           ║
    ╚══════════════════════════════════════════════════════════╝
    """
    ax3.text(0.5, 0.5, criteria_text, transform=ax3.transAxes, fontsize=10,
             verticalalignment='center', horizontalalignment='center',
             fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    ax3.set_title('Stock Selection Criteria', fontsize=14, fontweight='bold')

    # Bottom Right: Expected P&L Projection
    ax4 = axes[1, 1]

    # Simulate remaining 7 days
    days = list(range(1, 8))

    # Conservative scenario (no anomaly)
    conservative_pnl = [0.5] * 7
    conservative_cumulative = np.cumsum(conservative_pnl)

    # Moderate scenario (1 high vol day)
    moderate_pnl = [0.5, 0.5, 8, 0.5, 0.5, 0.5, 0.5]
    moderate_cumulative = np.cumsum(moderate_pnl)

    # Optimistic scenario (1 anomaly day)
    optimistic_pnl = [0.5, 50, 0.5, 0.5, 0.5, 0.5, 0.5]
    optimistic_cumulative = np.cumsum(optimistic_pnl)

    ax4.plot(days, conservative_cumulative, 'b-o', label='Conservative (No Anomaly)', linewidth=2)
    ax4.plot(days, moderate_cumulative, 'orange', marker='s', label='Moderate (1 High Vol)', linewidth=2)
    ax4.plot(days, optimistic_cumulative, 'g-^', label='Optimistic (1 Anomaly)', linewidth=2)

    ax4.fill_between(days, conservative_cumulative, optimistic_cumulative, alpha=0.2, color='green')

    ax4.set_xlabel('Trading Day', fontsize=12)
    ax4.set_ylabel('Cumulative Return (%)', fontsize=12)
    ax4.set_title('7-Day Return Projection', fontsize=14, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '12_recommended_approach.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 12_recommended_approach.png")

def plot_why_hft_fails():
    """Figure 6: Why Traditional HFT Fails in SET Market"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Top Left: HFT Cost Structure Comparison
    ax1 = axes[0, 0]

    markets = ['US Equities\n(NYSE/NASDAQ)', 'Thai Equities\n(SET)', 'Crypto\n(Binance)', 'Forex\n(Major Pairs)']
    commission_costs = [0.001, 0.168, 0.075, 0.002]
    spread_costs = [0.01, 0.50, 0.05, 0.01]

    x = np.arange(len(markets))
    width = 0.35

    bars1 = ax1.bar(x - width/2, commission_costs, width, label='Commission (%)', color='#3498DB')
    bars2 = ax1.bar(x + width/2, spread_costs, width, label='Spread/Slippage (%)', color='#E74C3C')

    ax1.set_ylabel('Cost (%)', fontsize=12)
    ax1.set_title('HFT Cost Comparison by Market', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(markets)
    ax1.legend()
    ax1.set_yscale('log')

    # Top Right: Break-even Analysis
    ax2 = axes[0, 1]

    trades_per_day = np.arange(10, 510, 10)

    # Different cost scenarios
    cost_low = 0.5  # Low price stocks
    cost_mid = 1.0  # Mid price stocks
    cost_high = 1.5  # High price stocks

    # Required win rate to break even (assuming 1:1 risk/reward)
    # win_rate = cost / (profit_target + cost)
    # For HFT with small targets (~0.5%), need high win rate

    target_profit = 0.5  # 0.5% target per trade

    required_wr_low = cost_low / (target_profit + cost_low)
    required_wr_mid = cost_mid / (target_profit + cost_mid)
    required_wr_high = cost_high / (target_profit + cost_high)

    ax2.axhline(y=required_wr_low * 100, color='green', linestyle='-', linewidth=2,
                label=f'Low Cost (0.5%): {required_wr_low*100:.0f}%')
    ax2.axhline(y=required_wr_mid * 100, color='orange', linestyle='-', linewidth=2,
                label=f'Mid Cost (1.0%): {required_wr_mid*100:.0f}%')
    ax2.axhline(y=required_wr_high * 100, color='red', linestyle='-', linewidth=2,
                label=f'High Cost (1.5%): {required_wr_high*100:.0f}%')
    ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='Random (50%)')

    ax2.fill_between([0, 500], [75, 75], [100, 100], alpha=0.3, color='red', label='Unrealistic Zone')

    ax2.set_xlabel('Trades per Day', fontsize=12)
    ax2.set_ylabel('Required Win Rate (%)', fontsize=12)
    ax2.set_title('Win Rate Required to Break Even\n(Target: 0.5% per trade)', fontsize=14, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.set_xlim(0, 500)
    ax2.set_ylim(45, 100)

    # Bottom Left: Price Impact Analysis
    ax3 = axes[1, 0]

    position_sizes = [100000, 250000, 500000, 750000, 1000000]

    # Simulated price impact for different liquidity stocks
    high_liquid = [0.05, 0.08, 0.12, 0.18, 0.25]  # GULF, KTB
    mid_liquid = [0.10, 0.20, 0.35, 0.50, 0.70]   # CPALL, PTT
    low_liquid = [0.25, 0.50, 0.80, 1.20, 1.80]   # Small caps

    ax3.plot(position_sizes, high_liquid, 'g-o', label='High Liquidity (GULF)', linewidth=2)
    ax3.plot(position_sizes, mid_liquid, 'orange', marker='s', label='Mid Liquidity (CPALL)', linewidth=2)
    ax3.plot(position_sizes, low_liquid, 'r-^', label='Low Liquidity', linewidth=2)

    ax3.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='0.5% threshold')

    ax3.set_xlabel('Position Size (THB)', fontsize=12)
    ax3.set_ylabel('Estimated Price Impact (%)', fontsize=12)
    ax3.set_title('Price Impact by Position Size', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Format x-axis
    ax3.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))

    # Bottom Right: Strategy Performance Summary
    ax4 = axes[1, 1]
    ax4.axis('off')

    summary_text = """
    ╔════════════════════════════════════════════════════════════╗
    ║              WHY TRADITIONAL HFT FAILS IN SET               ║
    ╠════════════════════════════════════════════════════════════╣
    ║                                                             ║
    ║  1. HIGH COMMISSION COSTS                                   ║
    ║     • SET: 0.168% vs US: 0.001%                             ║
    ║     • 168x higher than US markets                           ║
    ║                                                             ║
    ║  2. LARGE TICK SIZES                                        ║
    ║     • 50 THB stock: 0.25 THB tick (0.5%)                    ║
    ║     • Creates 0.5%+ slippage per trade                      ║
    ║                                                             ║
    ║  3. ROUND-TRIP COSTS TOO HIGH                               ║
    ║     • Typical stock: 1.4% round-trip                        ║
    ║     • HFT needs < 0.1% to be viable                         ║
    ║                                                             ║
    ║  4. WIN RATE REQUIREMENT                                    ║
    ║     • Need 75%+ win rate for 0.5% profit target             ║
    ║     • Nearly impossible to achieve consistently             ║
    ║                                                             ║
    ║  ═══════════════════════════════════════════════════════    ║
    ║  CONCLUSION: Traditional HFT is NOT viable in SET           ║
    ║  RECOMMENDATION: Focus on anomaly detection + VWAP reversion║
    ║  ═══════════════════════════════════════════════════════    ║
    ║                                                             ║
    ╚════════════════════════════════════════════════════════════╝
    """
    ax4.text(0.5, 0.5, summary_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='center', horizontalalignment='center',
             fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    ax4.set_title('Summary', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / '13_why_hft_fails.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: 13_why_hft_fails.png")

def main():
    print("=" * 60)
    print("HFT Strategy Exploration - Generating Visualizations")
    print("=" * 60)

    # Generate all figures
    plot_transaction_costs()
    plot_strategy_comparison()
    plot_hft_viability_matrix()
    plot_cost_vs_opportunity()
    plot_recommended_approach()
    plot_why_hft_fails()

    print("\n" + "=" * 60)
    print("All visualizations generated successfully!")
    print(f"Figures saved to: {FIGURES_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
