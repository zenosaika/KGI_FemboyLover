#!/usr/bin/env python3
"""
Run the trading simulation for the competition period (2025-11-10 to 2025-11-27)
"""

import pandas as pd
import importlib
import re
import os
from datetime import datetime

# Import trading library
from tradeSim import TradeSim
from tradeSim import StrategyHandler

# Competition dates (weekdays only, excluding holidays)
COMPETITION_DATES = [
    "2025-11-10",
    "2025-11-11",
    "2025-11-12",
    "2025-11-13",
    "2025-11-14",
    "2025-11-17",
    "2025-11-18",
    "2025-11-19",
    "2025-11-20",
    "2025-11-21",
    "2025-11-24",
    "2025-11-25",
    "2025-11-26",
    "2025-11-27",
]

team_name = "FemboyLover"
strategy_name = "IntradayMeanReversion"

# Validate team name
pattern = r'^[A-Za-z0-9-_]{1,30}$'
if not bool(re.match(pattern, team_name)) or not bool(re.match(pattern, strategy_name)):
    raise ValueError("Team name or strategy name is invalid.")

# Load strategy module
try:
    strategy_module = importlib.import_module(f"strategy.{strategy_name}")
    importlib.reload(strategy_module)
except ImportError as e:
    print(f"Error in strategy module: {e}")
    raise

strategy_class = getattr(strategy_module, strategy_name, None)
if strategy_class is None:
    raise ValueError(f"Strategy class {strategy_name} not found in module")

print(f"=" * 60)
print(f"KGI ALGO TRADING COMPETITION - Team: {team_name}")
print(f"Strategy: {strategy_name}")
print(f"Competition Period: 2025-11-10 to 2025-11-27")
print(f"=" * 60)

# Check which dates have tick files
available_dates = []
for date in COMPETITION_DATES:
    tick_file = f"./marketInfo/ticks/{date}.csv"
    if os.path.exists(tick_file):
        available_dates.append(date)
    else:
        print(f"[WARNING] Tick file not found for {date}")

print(f"\nAvailable trading days: {len(available_dates)}")
print(f"Dates: {', '.join(available_dates)}")
print(f"=" * 60)

# Run simulation for each day
for i, date in enumerate(available_dates):
    daily_ticks = f"./marketInfo/ticks/{date}.csv"

    print(f"\n[Day {i+1}/{len(available_dates)}] Processing {date}...")

    # Load tick data
    df = pd.read_csv(daily_ticks)
    df['TradeDateTime'] = pd.to_datetime(df['TradeDateTime'])
    grouped = df.groupby('ShareCode')

    # Initialize trade system (loads existing portfolio if available)
    trading_Sim = TradeSim.tradeSim(team_name)
    strategy_runner = trading_Sim.get_strategy_runner()

    # Create handlers for each symbol
    handlers = {
        symbol: StrategyHandler.StrategyHandler(strategy_class, strategy_runner)
        for symbol, _ in grouped
    }

    max_length = max(len(group) for _, group in grouped)
    latest_prices = {}

    # Run simulation (headless mode for speed)
    for tick in range(max_length):
        for symbol, data in grouped:
            if tick >= len(data):
                continue

            row = data.iloc[tick]
            price_update = {row['ShareCode']: row['LastPrice']}

            handler = handlers[symbol]
            handler.process_row(row)

            if not trading_Sim.isOrderbooksEmpty():
                trading_Sim.isMatch(row)

            trading_Sim.update_market_prices(price_update)

            latest_prices[symbol] = {
                "price": row['LastPrice'],
                "volume": row['Volume'],
                "Flag": row['Flag']
            }

    # Flush logs and save results
    trading_Sim.flushTransactionLog()
    trading_Sim.flushErrorLogger()
    trading_Sim.create_transaction_summarize(team_name)
    trading_Sim.save_portfolio()

    trading_date = df['TradeDateTime'].dt.date.iloc[0]
    trading_Sim.save_summary_csv(trading_date)

    # Print daily summary
    port_info = strategy_runner.get_portfolio_info()
    print(f"  NAV: {port_info['Net Asset Value']:,.2f} THB")
    print(f"  Return: {port_info['Return rate']:.4f}%")
    print(f"  Max Drawdown: {port_info['Max Drawdown (%)']:.2f}%" if port_info['Max Drawdown (%)'] else "  Max Drawdown: N/A")
    print(f"  Wins/Sells: {port_info['Number of Wins']}/{port_info['Number of Sells']}")
    print(f"  Win Rate: {port_info['Win Rate']:.2f}%")

# Final summary
print(f"\n{'=' * 60}")
print("FINAL COMPETITION RESULTS")
print(f"{'=' * 60}")

# Reload final portfolio
trading_Sim = TradeSim.tradeSim(team_name)
strategy_runner = trading_Sim.get_strategy_runner()
port_info = strategy_runner.get_portfolio_info()

print(f"\nTeam: {port_info['Owner']}")
print(f"Initial Capital: 10,000,000.00 THB")
print(f"Final NAV: {port_info['Net Asset Value']:,.2f} THB")
print(f"Cash Balance: {port_info['Cash Balance']:,.2f} THB")
print(f"Stocks Held: {port_info['Number of Stocks']}")
print(f"\n--- Performance Metrics ---")
print(f"Return Rate: {port_info['Return rate']:.4f}%")
print(f"Max Drawdown: {port_info['Max Drawdown (%)']:.2f}%" if port_info['Max Drawdown (%)'] else "Max Drawdown: N/A")
print(f"Calmar Ratio: {port_info['Calmar Ratio']:.4f}" if port_info['Calmar Ratio'] else "Calmar Ratio: N/A")
print(f"Total Trades (Sells): {port_info['Number of Sells']}")
print(f"Winning Trades: {port_info['Number of Wins']}")
print(f"Win Rate: {port_info['Win Rate']:.2f}%")

print(f"\n--- Competition Minimum Requirements Check ---")
return_ok = port_info['Return rate'] > 5
dd_ok = port_info['Max Drawdown (%)'] is None or abs(port_info['Max Drawdown (%)']) < 30
trades_ok = port_info['Number of Sells'] > 20
wr_ok = port_info['Win Rate'] > 20

print(f"[{'PASS' if return_ok else 'FAIL'}] Return > 5%: {port_info['Return rate']:.4f}%")
print(f"[{'PASS' if dd_ok else 'FAIL'}] Max Drawdown < 30%: {abs(port_info['Max Drawdown (%)'] or 0):.2f}%")
print(f"[{'PASS' if trades_ok else 'FAIL'}] Trades > 20: {port_info['Number of Sells']}")
print(f"[{'PASS' if wr_ok else 'FAIL'}] Win Rate > 20%: {port_info['Win Rate']:.2f}%")

if all([return_ok, dd_ok, trades_ok, wr_ok]):
    print(f"\n*** ALL MINIMUM REQUIREMENTS MET ***")
else:
    print(f"\n*** SOME REQUIREMENTS NOT MET ***")

print(f"\nResults saved to: result/{team_name}/")
