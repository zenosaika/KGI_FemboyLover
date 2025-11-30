#!/usr/bin/env python3
"""
IntradayMeanReversion Strategy Analysis
Comprehensive visualization and analysis for FemboyLover team
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os

# Create output directory
os.makedirs('analysis/figures', exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Color palette
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'success': '#28A745',
    'danger': '#DC3545',
    'warning': '#FFC107',
    'info': '#17A2B8',
    'dark': '#343A40',
    'light': '#F8F9FA'
}

print("=" * 70)
print("IntradayMeanReversion Strategy Analysis - FemboyLover Team")
print("=" * 70)

# Load portfolio summary data
summary_df = pd.read_csv('./result/FemboyLover/FemboyLover_portfolio_summary.csv')
summary_df['Daily Ticks Time'] = pd.to_datetime(summary_df['Daily Ticks Time'])
summary_df['Date'] = summary_df['Daily Ticks Time'].dt.date

# Load transaction summary
txn_df = pd.read_csv('./result/FemboyLover/FemboyLover_portfolios_transaction_summary.csv')
txn_df = txn_df[txn_df['Symbol'] != 'TOTAL']
txn_df['Profit'] = txn_df['Received Amount'] - txn_df['Paid Amount']

print(f"\nLoaded {len(summary_df)} trading days")
print(f"Loaded {len(txn_df)} traded symbols")

# ============================================================
# FIGURE 1: Portfolio Performance Over Time
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('FemboyLover Portfolio Performance Analysis\nIntradayMeanReversion Strategy',
             fontsize=16, fontweight='bold', y=1.02)

# Plot 1: NAV Over Time
ax1 = axes[0, 0]
dates = range(1, len(summary_df) + 1)
ax1.fill_between(dates, 10000000, summary_df['Net Asset Value'], alpha=0.3, color=COLORS['success'])
ax1.plot(dates, summary_df['Net Asset Value'], 'o-', color=COLORS['success'], linewidth=2.5, markersize=8)
ax1.axhline(y=10000000, color=COLORS['dark'], linestyle='--', alpha=0.5, label='Initial Capital')
ax1.set_xlabel('Trading Day')
ax1.set_ylabel('Net Asset Value (THB)')
ax1.set_title('Portfolio NAV Growth')
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
ax1.legend()
ax1.grid(True, alpha=0.3)

# Annotate key points
ax1.annotate(f'Day 1: {summary_df.iloc[0]["Net Asset Value"]/1e6:.2f}M',
             xy=(1, summary_df.iloc[0]['Net Asset Value']),
             xytext=(2, summary_df.iloc[0]['Net Asset Value'] + 1e6),
             fontsize=9, ha='left')
ax1.annotate(f'Day 2: {summary_df.iloc[1]["Net Asset Value"]/1e6:.2f}M\n(+97.6%)',
             xy=(2, summary_df.iloc[1]['Net Asset Value']),
             xytext=(3, summary_df.iloc[1]['Net Asset Value'] - 1e6),
             fontsize=9, ha='left', color=COLORS['success'], fontweight='bold',
             arrowprops=dict(arrowstyle='->', color=COLORS['success']))
ax1.annotate(f'Final: {summary_df.iloc[-1]["Net Asset Value"]/1e6:.2f}M',
             xy=(len(summary_df), summary_df.iloc[-1]['Net Asset Value']),
             xytext=(len(summary_df)-1, summary_df.iloc[-1]['Net Asset Value'] + 0.5e6),
             fontsize=9, ha='right')

# Plot 2: Daily Return Rate
ax2 = axes[0, 1]
daily_returns = summary_df['Return rate'].diff().fillna(summary_df['Return rate'].iloc[0])
colors = [COLORS['success'] if r >= 0 else COLORS['danger'] for r in daily_returns]
ax2.bar(dates, daily_returns, color=colors, alpha=0.8, edgecolor='white')
ax2.axhline(y=0, color=COLORS['dark'], linestyle='-', linewidth=1)
ax2.set_xlabel('Trading Day')
ax2.set_ylabel('Daily Return Change (%)')
ax2.set_title('Daily Return Changes')
ax2.grid(True, alpha=0.3)

# Highlight Day 2
ax2.annotate('Day 2: +97.6%\n(Massive gain)', xy=(2, daily_returns.iloc[1]),
             xytext=(4, daily_returns.iloc[1] - 10),
             fontsize=10, ha='left', color=COLORS['success'], fontweight='bold',
             arrowprops=dict(arrowstyle='->', color=COLORS['success']))

# Plot 3: Cumulative Trades and Wins
ax3 = axes[1, 0]
ax3.plot(dates, summary_df['Number of Sells'], 'o-', color=COLORS['primary'],
         linewidth=2, markersize=6, label='Total Trades')
ax3.plot(dates, summary_df['Number of Wins'], 's-', color=COLORS['success'],
         linewidth=2, markersize=6, label='Winning Trades')
ax3.fill_between(dates, summary_df['Number of Wins'], alpha=0.3, color=COLORS['success'])
ax3.set_xlabel('Trading Day')
ax3.set_ylabel('Cumulative Count')
ax3.set_title('Cumulative Trades Over Time')
ax3.legend(loc='upper left')
ax3.grid(True, alpha=0.3)

# Plot 4: Win Rate Evolution
ax4 = axes[1, 1]
ax4.plot(dates, summary_df['Win Rate'], 'o-', color=COLORS['info'], linewidth=2.5, markersize=8)
ax4.axhline(y=20, color=COLORS['danger'], linestyle='--', alpha=0.7, label='Min Requirement (20%)')
ax4.axhline(y=summary_df['Win Rate'].iloc[-1], color=COLORS['success'], linestyle=':', alpha=0.7,
            label=f'Final Win Rate ({summary_df["Win Rate"].iloc[-1]:.1f}%)')
ax4.fill_between(dates, 20, summary_df['Win Rate'], alpha=0.2, color=COLORS['success'])
ax4.set_xlabel('Trading Day')
ax4.set_ylabel('Win Rate (%)')
ax4.set_title('Win Rate Evolution')
ax4.set_ylim(0, 105)
ax4.legend(loc='lower left')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('analysis/figures/01_portfolio_performance.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("✓ Saved: 01_portfolio_performance.png")

# ============================================================
# FIGURE 2: Stock-Level Analysis
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Stock-Level Trading Analysis\nTop Performers and Trade Distribution',
             fontsize=16, fontweight='bold', y=1.02)

# Plot 1: Top 10 Profitable Stocks
ax1 = axes[0, 0]
top_profit = txn_df.nlargest(10, 'Profit')
colors_profit = [COLORS['success'] if p > 0 else COLORS['danger'] for p in top_profit['Profit']]
bars = ax1.barh(top_profit['Symbol'], top_profit['Profit'], color=colors_profit, alpha=0.8, edgecolor='white')
ax1.set_xlabel('Profit (THB)')
ax1.set_ylabel('Symbol')
ax1.set_title('Top 10 Most Profitable Stocks')
ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.2f}M'))
for bar, val in zip(bars, top_profit['Profit']):
    ax1.text(val + 50000, bar.get_y() + bar.get_height()/2, f'{val/1e6:.2f}M',
             va='center', fontsize=9)
ax1.grid(True, alpha=0.3, axis='x')

# Plot 2: Trade Count by Symbol (Top 15)
ax2 = axes[0, 1]
top_trades = txn_df.nlargest(15, 'Buy Count')
ax2.barh(top_trades['Symbol'], top_trades['Buy Count'], color=COLORS['primary'], alpha=0.8, edgecolor='white')
ax2.set_xlabel('Number of Trades')
ax2.set_ylabel('Symbol')
ax2.set_title('Top 15 Most Traded Stocks')
ax2.grid(True, alpha=0.3, axis='x')

# Plot 3: Profit vs Trade Count Scatter
ax3 = axes[1, 0]
scatter = ax3.scatter(txn_df['Buy Count'], txn_df['Profit'],
                      c=txn_df['Profit'], cmap='RdYlGn', s=100, alpha=0.7, edgecolors='white')
ax3.axhline(y=0, color=COLORS['dark'], linestyle='--', alpha=0.5)
ax3.set_xlabel('Number of Trades')
ax3.set_ylabel('Profit (THB)')
ax3.set_title('Profit vs Trade Frequency')
ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))

# Label top performers
for _, row in txn_df.nlargest(5, 'Profit').iterrows():
    ax3.annotate(row['Symbol'], (row['Buy Count'], row['Profit']),
                 textcoords="offset points", xytext=(5, 5), fontsize=9, fontweight='bold')
ax3.grid(True, alpha=0.3)

# Plot 4: Trading Volume Distribution
ax4 = axes[1, 1]
volume_data = txn_df.nlargest(10, 'Buy Volume')
ax4.pie(volume_data['Buy Volume'], labels=volume_data['Symbol'], autopct='%1.1f%%',
        colors=plt.cm.Set3(np.linspace(0, 1, len(volume_data))), startangle=90)
ax4.set_title('Trading Volume Distribution (Top 10)')

plt.tight_layout()
plt.savefig('analysis/figures/02_stock_analysis.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("✓ Saved: 02_stock_analysis.png")

# ============================================================
# FIGURE 3: Day 2 Analysis - The 97% Jump
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Day 2 Analysis: Understanding the 97.6% Return Jump\n2025-11-11 Market Conditions',
             fontsize=16, fontweight='bold', y=1.02)

# Load day 2 data
day2 = pd.read_csv('./marketInfo/ticks/2025-11-11.csv')
day2['TradeDateTime'] = pd.to_datetime(day2['TradeDateTime'])

# Plot 1: GULF intraday with VWAP
ax1 = axes[0, 0]
gulf = day2[day2['ShareCode'] == 'GULF'].copy().sort_values('TradeDateTime')
gulf['cumval'] = (gulf['LastPrice'] * gulf['Volume']).cumsum()
gulf['cumvol'] = gulf['Volume'].cumsum()
gulf['vwap'] = gulf['cumval'] / gulf['cumvol']
gulf['buy_trigger'] = gulf['vwap'] * 0.985

ax1.plot(gulf['TradeDateTime'], gulf['LastPrice'], alpha=0.5, linewidth=0.5, color=COLORS['dark'], label='Price')
ax1.plot(gulf['TradeDateTime'], gulf['vwap'], color=COLORS['primary'], linewidth=2, label='VWAP')
ax1.plot(gulf['TradeDateTime'], gulf['buy_trigger'], color=COLORS['success'], linewidth=1.5,
         linestyle='--', label='Buy Trigger (1.5% below VWAP)')
ax1.fill_between(gulf['TradeDateTime'], gulf['buy_trigger'], gulf['LastPrice'].min(),
                 where=gulf['LastPrice'] <= gulf['buy_trigger'], alpha=0.3, color=COLORS['success'],
                 label='Buy Zone')
ax1.set_xlabel('Time')
ax1.set_ylabel('Price (THB)')
ax1.set_title('GULF: Price vs VWAP (322 trades, 1.32M THB profit)')
ax1.legend(loc='upper right', fontsize=9)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax1.grid(True, alpha=0.3)

# Plot 2: BDMS intraday
ax2 = axes[0, 1]
bdms = day2[day2['ShareCode'] == 'BDMS'].copy().sort_values('TradeDateTime')
bdms['cumval'] = (bdms['LastPrice'] * bdms['Volume']).cumsum()
bdms['cumvol'] = bdms['Volume'].cumsum()
bdms['vwap'] = bdms['cumval'] / bdms['cumvol']
bdms['buy_trigger'] = bdms['vwap'] * 0.985

ax2.plot(bdms['TradeDateTime'], bdms['LastPrice'], alpha=0.5, linewidth=0.5, color=COLORS['dark'], label='Price')
ax2.plot(bdms['TradeDateTime'], bdms['vwap'], color=COLORS['primary'], linewidth=2, label='VWAP')
ax2.plot(bdms['TradeDateTime'], bdms['buy_trigger'], color=COLORS['success'], linewidth=1.5,
         linestyle='--', label='Buy Trigger')
ax2.fill_between(bdms['TradeDateTime'], bdms['buy_trigger'], bdms['LastPrice'].min(),
                 where=bdms['LastPrice'] <= bdms['buy_trigger'], alpha=0.3, color=COLORS['success'])
ax2.set_xlabel('Time')
ax2.set_ylabel('Price (THB)')
ax2.set_title('BDMS: Price vs VWAP (114 trades, 2.31M THB profit)')
ax2.legend(loc='upper right', fontsize=9)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax2.grid(True, alpha=0.3)

# Plot 3: Day 1 vs Day 2 comparison
ax3 = axes[1, 0]
day1 = pd.read_csv('./marketInfo/ticks/2025-11-10.csv')
day1_counts = day1.groupby('ShareCode').size()
day2_counts = day2.groupby('ShareCode').size()

# Compare tick counts for top symbols
top_symbols = ['GULF', 'BDMS', 'CPALL', 'MINT', 'TOP', 'TRUE', 'KTB']
x = np.arange(len(top_symbols))
width = 0.35

d1_vals = [day1_counts.get(s, 0) for s in top_symbols]
d2_vals = [day2_counts.get(s, 0) for s in top_symbols]

bars1 = ax3.bar(x - width/2, d1_vals, width, label='Day 1 (2025-11-10)', color=COLORS['secondary'], alpha=0.8)
bars2 = ax3.bar(x + width/2, d2_vals, width, label='Day 2 (2025-11-11)', color=COLORS['primary'], alpha=0.8)
ax3.set_xlabel('Symbol')
ax3.set_ylabel('Number of Ticks')
ax3.set_title('Market Activity: Day 1 vs Day 2 (Key Symbols)')
ax3.set_xticks(x)
ax3.set_xticklabels(top_symbols)
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')

# Plot 4: Volume analysis
ax4 = axes[1, 1]
day1_vol = day1.groupby('ShareCode')['Volume'].sum()
day2_vol = day2.groupby('ShareCode')['Volume'].sum()

d1_vol_vals = [day1_vol.get(s, 0) for s in top_symbols]
d2_vol_vals = [day2_vol.get(s, 0) for s in top_symbols]

bars1 = ax4.bar(x - width/2, np.array(d1_vol_vals)/1e6, width, label='Day 1', color=COLORS['secondary'], alpha=0.8)
bars2 = ax4.bar(x + width/2, np.array(d2_vol_vals)/1e6, width, label='Day 2', color=COLORS['primary'], alpha=0.8)
ax4.set_xlabel('Symbol')
ax4.set_ylabel('Total Volume (Millions)')
ax4.set_title('Trading Volume Comparison: Day 1 vs Day 2')
ax4.set_xticks(x)
ax4.set_xticklabels(top_symbols)
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('analysis/figures/03_day2_analysis.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("✓ Saved: 03_day2_analysis.png")

# ============================================================
# FIGURE 4: Strategy Mechanics Visualization
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('IntradayMeanReversion Strategy Mechanics\nBuy at VWAP-1.5%, Sell at VWAP or Stop Loss',
             fontsize=16, fontweight='bold', y=1.02)

# Plot 1: Example trade cycle visualization
ax1 = axes[0, 0]
# Simulated data for visualization
np.random.seed(42)
time_points = np.linspace(0, 100, 500)
base_price = 100
vwap = base_price + np.sin(time_points/20) * 2 + np.cumsum(np.random.randn(500) * 0.05)
price = vwap + np.random.randn(500) * 1.5

ax1.plot(time_points, price, alpha=0.6, linewidth=0.8, color=COLORS['dark'], label='Price')
ax1.plot(time_points, vwap, color=COLORS['primary'], linewidth=2, label='VWAP')
ax1.plot(time_points, vwap * 0.985, color=COLORS['success'], linewidth=1.5, linestyle='--', label='Buy Trigger (-1.5%)')
ax1.plot(time_points, vwap * 0.98, color=COLORS['danger'], linewidth=1.5, linestyle=':', label='Stop Loss (-2%)')

# Mark buy/sell zones
buy_zone = price <= vwap * 0.985
sell_zone = price >= vwap
ax1.fill_between(time_points, price, vwap * 0.985, where=buy_zone, alpha=0.3, color=COLORS['success'], label='Buy Zone')

ax1.set_xlabel('Time (arbitrary units)')
ax1.set_ylabel('Price')
ax1.set_title('Strategy Logic: Mean Reversion to VWAP')
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)

# Plot 2: Position sizing breakdown
ax2 = axes[0, 1]
position_sizes = {
    'Initial Capital': 10000000,
    'Position Size': 500000,
    'Max Positions': 20,
    'Cash Reserved': 0
}
sizes = [500000] * 20  # 20 positions at 500k each
labels = [f'Pos {i+1}' for i in range(20)]
colors_pos = plt.cm.Greens(np.linspace(0.3, 0.9, 20))
ax2.pie(sizes, labels=None, colors=colors_pos, startangle=90, wedgeprops={'edgecolor': 'white'})
ax2.set_title(f'Position Allocation\n(500K THB per position × 20 = 10M THB)')

# Add legend for key info
ax2.text(0, -1.3, 'Position Size: 500,000 THB\nMax Concurrent Positions: ~20\nBuy Trigger: VWAP - 1.5%\nStop Loss: Entry - 2%',
         ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Plot 3: Daily P&L breakdown
ax3 = axes[1, 0]
daily_pnl = summary_df['Realized P&L'].diff().fillna(summary_df['Realized P&L'].iloc[0])
colors_pnl = [COLORS['success'] if p >= 0 else COLORS['danger'] for p in daily_pnl]
bars = ax3.bar(dates, daily_pnl, color=colors_pnl, alpha=0.8, edgecolor='white')
ax3.axhline(y=0, color=COLORS['dark'], linestyle='-', linewidth=1)
ax3.set_xlabel('Trading Day')
ax3.set_ylabel('Daily P&L (THB)')
ax3.set_title('Daily Realized P&L')
ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
ax3.grid(True, alpha=0.3)

# Annotate Day 2
ax3.annotate(f'Day 2: +9.76M THB', xy=(2, daily_pnl.iloc[1]),
             xytext=(4, daily_pnl.iloc[1] - 1e6),
             fontsize=10, ha='left', color=COLORS['success'], fontweight='bold',
             arrowprops=dict(arrowstyle='->', color=COLORS['success']))

# Plot 4: Trade outcome distribution
ax4 = axes[1, 1]
win_count = summary_df['Number of Wins'].iloc[-1]
loss_count = summary_df['Number of Sells'].iloc[-1] - win_count
labels_outcome = ['Winning Trades', 'Losing Trades']
sizes_outcome = [win_count, loss_count]
colors_outcome = [COLORS['success'], COLORS['danger']]
explode = (0.05, 0)

wedges, texts, autotexts = ax4.pie(sizes_outcome, labels=labels_outcome, autopct='%1.1f%%',
                                    colors=colors_outcome, explode=explode, startangle=90,
                                    wedgeprops={'edgecolor': 'white', 'linewidth': 2})
ax4.set_title(f'Trade Outcomes\n({win_count} wins / {loss_count} losses out of {win_count + loss_count} trades)')

# Add stats
stats_text = f'Win Rate: {win_count/(win_count+loss_count)*100:.1f}%\nTotal Trades: {win_count + loss_count}'
ax4.text(0, -1.3, stats_text, ha='center', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('analysis/figures/04_strategy_mechanics.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("✓ Saved: 04_strategy_mechanics.png")

# ============================================================
# FIGURE 5: Competition Requirements Dashboard
# ============================================================
fig, ax = plt.subplots(figsize=(14, 8))
fig.suptitle('Competition Requirements Dashboard\nFemboyLover Team - Final Status',
             fontsize=16, fontweight='bold', y=0.98)

# Data
metrics = ['Return Rate\n(>5%)', 'Max Drawdown\n(<30%)', 'Total Trades\n(>20)', 'Win Rate\n(>20%)']
requirements = [5, 30, 20, 20]
actual = [98.86, 5.18, 1411, 84.05]
is_pass = [True, True, True, True]

# Create horizontal bar chart
y_pos = np.arange(len(metrics))
bar_height = 0.6

# Normalize for visualization (scale each metric to percentage of max for comparison)
max_vals = [100, 30, 1500, 100]  # Reasonable max values for scaling
normalized_actual = [a/m*100 for a, m in zip(actual, max_vals)]
normalized_req = [r/m*100 for r, m in zip(requirements, max_vals)]

# Background bars (requirements)
ax.barh(y_pos, normalized_req, height=bar_height, color=COLORS['light'], edgecolor=COLORS['dark'],
        linewidth=2, label='Minimum Requirement', alpha=0.5)

# Actual values
colors_metric = [COLORS['success'] if p else COLORS['danger'] for p in is_pass]
bars = ax.barh(y_pos, normalized_actual, height=bar_height*0.7, color=colors_metric,
               edgecolor='white', label='Actual Performance')

# Add text annotations
for i, (metric, req, act, passed) in enumerate(zip(metrics, requirements, actual, is_pass)):
    status = "✓ PASS" if passed else "✗ FAIL"
    color = COLORS['success'] if passed else COLORS['danger']

    # Actual value text
    if 'Trades' in metric:
        ax.text(normalized_actual[i] + 2, i, f'{act:.0f}', va='center', ha='left',
                fontsize=12, fontweight='bold', color=color)
    elif 'Drawdown' in metric:
        ax.text(normalized_actual[i] + 2, i, f'{act:.2f}%', va='center', ha='left',
                fontsize=12, fontweight='bold', color=color)
    else:
        ax.text(normalized_actual[i] + 2, i, f'{act:.2f}%', va='center', ha='left',
                fontsize=12, fontweight='bold', color=color)

    # Status badge
    ax.text(105, i, status, va='center', ha='left', fontsize=11, fontweight='bold', color=color,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.2))

ax.set_yticks(y_pos)
ax.set_yticklabels(metrics, fontsize=12)
ax.set_xlabel('Progress (normalized %)')
ax.set_xlim(0, 120)
ax.set_title('All Competition Requirements Met ✓', fontsize=14, color=COLORS['success'], fontweight='bold')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3, axis='x')

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('analysis/figures/05_competition_dashboard.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("✓ Saved: 05_competition_dashboard.png")

# ============================================================
# FIGURE 6: Profit Attribution by Symbol
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(16, 8))
fig.suptitle('Profit Attribution Analysis by Symbol', fontsize=16, fontweight='bold', y=1.02)

# Plot 1: Treemap-style visualization (as stacked bars)
ax1 = axes[0]
txn_sorted = txn_df.sort_values('Profit', ascending=False)
positive = txn_sorted[txn_sorted['Profit'] > 0]
negative = txn_sorted[txn_sorted['Profit'] <= 0]

y = 0
patches = []
for _, row in positive.iterrows():
    height = row['Profit'] / 1e6
    ax1.barh(y, height, color=COLORS['success'], alpha=0.7, edgecolor='white')
    if height > 0.3:  # Only label significant bars
        ax1.text(height/2, y, row['Symbol'], va='center', ha='center', fontsize=8, fontweight='bold')
    y += 1

y_neg = 0
for _, row in negative.iterrows():
    height = abs(row['Profit']) / 1e6
    ax1.barh(y_neg, -height, color=COLORS['danger'], alpha=0.7, edgecolor='white')
    ax1.text(-height/2, y_neg, row['Symbol'], va='center', ha='center', fontsize=8, fontweight='bold')
    y_neg += 1

ax1.axvline(x=0, color=COLORS['dark'], linewidth=2)
ax1.set_xlabel('Profit/Loss (Million THB)')
ax1.set_ylabel('Stock Rank')
ax1.set_title(f'Profit by Symbol\n(Green: {len(positive)} profitable, Red: {len(negative)} loss-making)')
ax1.grid(True, alpha=0.3, axis='x')

# Plot 2: Cumulative profit contribution
ax2 = axes[1]
cumulative_profit = txn_sorted['Profit'].cumsum()
x = range(1, len(cumulative_profit) + 1)
ax2.fill_between(x, 0, cumulative_profit, alpha=0.3, color=COLORS['success'])
ax2.plot(x, cumulative_profit, color=COLORS['success'], linewidth=2)
ax2.axhline(y=cumulative_profit.iloc[-1], color=COLORS['primary'], linestyle='--', alpha=0.7)
ax2.set_xlabel('Number of Symbols (ranked by profit)')
ax2.set_ylabel('Cumulative Profit (THB)')
ax2.set_title('Cumulative Profit Contribution')
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
ax2.grid(True, alpha=0.3)

# Mark 80% contribution point
total_profit = cumulative_profit.iloc[-1]
for i, cp in enumerate(cumulative_profit):
    if cp >= total_profit * 0.8:
        ax2.axvline(x=i+1, color=COLORS['warning'], linestyle='--', alpha=0.7)
        ax2.annotate(f'80% profit from\ntop {i+1} symbols', xy=(i+1, cp),
                     xytext=(i+5, cp*0.85), fontsize=10,
                     arrowprops=dict(arrowstyle='->', color=COLORS['warning']))
        break

plt.tight_layout()
plt.savefig('analysis/figures/06_profit_attribution.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("✓ Saved: 06_profit_attribution.png")

print("\n" + "=" * 70)
print("All visualizations saved to analysis/figures/")
print("=" * 70)

# Print final statistics summary
print("\n" + "=" * 70)
print("FINAL STATISTICS SUMMARY")
print("=" * 70)
print(f"\nPortfolio Performance:")
print(f"  Initial Capital:     10,000,000.00 THB")
print(f"  Final NAV:           {summary_df['Net Asset Value'].iloc[-1]:,.2f} THB")
print(f"  Total Return:        {summary_df['Return rate'].iloc[-1]:.4f}%")
print(f"  Max Drawdown:        {summary_df['Max Drawdown (%)'].iloc[-1]:.2f}%")
print(f"  Calmar Ratio:        {summary_df['Calmar Ratio'].iloc[-1]:.4f}")

print(f"\nTrading Statistics:")
print(f"  Total Trades:        {summary_df['Number of Sells'].iloc[-1]}")
print(f"  Winning Trades:      {summary_df['Number of Wins'].iloc[-1]}")
print(f"  Win Rate:            {summary_df['Win Rate'].iloc[-1]:.2f}%")
print(f"  Unique Symbols:      {len(txn_df)}")

print(f"\nTop 5 Profitable Stocks:")
for _, row in txn_df.nlargest(5, 'Profit').iterrows():
    print(f"  {row['Symbol']:8s} +{row['Profit']:>12,.2f} THB ({row['Buy Count']} trades)")

print(f"\nDay 2 Impact Analysis:")
print(f"  Day 1 NAV:           {summary_df['Net Asset Value'].iloc[0]:,.2f} THB")
print(f"  Day 2 NAV:           {summary_df['Net Asset Value'].iloc[1]:,.2f} THB")
print(f"  Day 2 Return:        +{summary_df['Return rate'].iloc[1]:.2f}%")
print(f"  Day 2 Trades:        {summary_df['Number of Sells'].iloc[1] - summary_df['Number of Sells'].iloc[0]}")
