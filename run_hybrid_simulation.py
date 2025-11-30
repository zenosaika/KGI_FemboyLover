#!/usr/bin/env python3
"""
Run the Hybrid VWAP strategy simulation for comparison with original
Competition period: 2025-11-10 to 2025-11-27
"""

import pandas as pd
import importlib
import re
import os
import shutil
from datetime import datetime

# Import trading library
from tradeSim import TradeSim
from tradeSim import StrategyHandler

# Competition dates
COMPETITION_DATES = [
    "2025-11-10", "2025-11-11", "2025-11-12", "2025-11-13", "2025-11-14",
    "2025-11-17", "2025-11-18", "2025-11-19", "2025-11-20", "2025-11-21",
    "2025-11-24", "2025-11-25", "2025-11-26", "2025-11-27",
]

team_name = "FemboyLover_Hybrid"
strategy_name = "HybridVWAP"

# Clean up old results
result_dir = f"./result/{team_name}"
if os.path.exists(result_dir):
    shutil.rmtree(result_dir)

# Load strategy
strategy_module = importlib.import_module(f"strategy.{strategy_name}")
importlib.reload(strategy_module)
strategy_class = getattr(strategy_module, strategy_name)

print(f"=" * 60)
print(f"HYBRID VWAP STRATEGY SIMULATION")
print(f"(Normal: Deep Discount | Anomaly: Aggressive)")
print(f"=" * 60)

# Get available dates
available_dates = [d for d in COMPETITION_DATES if os.path.exists(f"./marketInfo/ticks/{d}.csv")]
print(f"Trading days: {len(available_dates)}")

daily_results = []

for i, date in enumerate(available_dates):
    print(f"\n[Day {i+1}/{len(available_dates)}] {date}...", end=" ")

    df = pd.read_csv(f"./marketInfo/ticks/{date}.csv")
    df['TradeDateTime'] = pd.to_datetime(df['TradeDateTime'])
    grouped = df.groupby('ShareCode')

    trading_Sim = TradeSim.tradeSim(team_name)
    strategy_runner = trading_Sim.get_strategy_runner()

    handlers = {symbol: StrategyHandler.StrategyHandler(strategy_class, strategy_runner)
                for symbol, _ in grouped}

    max_length = max(len(group) for _, group in grouped)

    for tick in range(max_length):
        for symbol, data in grouped:
            if tick >= len(data):
                continue
            row = data.iloc[tick]
            handlers[symbol].process_row(row)
            if not trading_Sim.isOrderbooksEmpty():
                trading_Sim.isMatch(row)
            trading_Sim.update_market_prices({row['ShareCode']: row['LastPrice']})

    trading_Sim.flushTransactionLog()
    trading_Sim.flushErrorLogger()
    trading_Sim.create_transaction_summarize(team_name)
    trading_Sim.save_portfolio()
    trading_Sim.save_summary_csv(df['TradeDateTime'].dt.date.iloc[0])

    port_info = strategy_runner.get_portfolio_info()
    print(f"NAV: {port_info['Net Asset Value']:,.0f} | Return: {port_info['Return rate']:.2f}% | W/S: {port_info['Number of Wins']}/{port_info['Number of Sells']}")

    daily_results.append({
        'date': date, 'nav': port_info['Net Asset Value'],
        'return_pct': port_info['Return rate'],
        'wins': port_info['Number of Wins'], 'sells': port_info['Number of Sells']
    })

# Final results
print(f"\n{'=' * 60}")
print("HYBRID VWAP - FINAL RESULTS")
print(f"{'=' * 60}")

trading_Sim = TradeSim.tradeSim(team_name)
port_info = trading_Sim.get_strategy_runner().get_portfolio_info()

print(f"Final NAV: {port_info['Net Asset Value']:,.2f} THB")
print(f"Return: {port_info['Return rate']:.2f}%")
print(f"Max DD: {port_info['Max Drawdown (%)']:.2f}%" if port_info['Max Drawdown (%)'] else "Max DD: N/A")
print(f"Trades: {port_info['Number of Sells']} | Wins: {port_info['Number of Wins']} | WR: {port_info['Win Rate']:.1f}%")

pd.DataFrame(daily_results).to_csv(f"result/{team_name}/daily_results.csv", index=False)
print(f"\nSaved to: result/{team_name}/")
