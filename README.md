# KGI ALGO TRADING - FemboyLover TEAM

# Team & Competition Information:
```
# Team
Our Team Name : FemboyLover
Current Strategy : IntradayMeanReversion (strategy/IntradayMeanReversion.py)

# Competition
Today Date : 2025-11-27 (Based on latest available tick data not real date)
Competition Period : 2025-11-10 to 2025-12-08 (About 7 days left. SET market is closed on Saturdays and Sundays.)

# Current Ranking
1. FemboyLover (Our Team, See the simulation result in result/FemboyLover)
    - % Return Rate : 98.8599746772
    - % Max Drawdown : -5.18
    - % Winrate : 84.1
    - % Calmer Ratio : 19.07095995
2. ShadowTeam (Note: We suspect this team uses an intraday mean reversion strategy similar to ours, but with less aggressive hyperparameters, such as position size and buy_trigger_pct.)
    - % Return Rate : 11.49460698
    - % Max Drawdown : -1.05
    - % Winrate : 77.9
    - % Calmer Ratio : 10.91478789
3. LightTeam
    - % Return Rate : 0.8656674166
    - % Max Drawdown : -1.1
    - % Winrate : 0 (Likely a buy-and-hold strategy)
    - % Calmer Ratio : 0.784248454

# Strategy Note
It is unlikely that other teams can overtake us in the remaining 7 days. Therefore, I propose exploring additional strategies, such as High-Frequency Trading (HFT). We can leverage our significant capital advantage (approximately 2x that of our competitors) to allocate a portion of our profits toward generating further returns. This allows us to pursue upside potential with a very low risk of losing our lead to ShadowTeam.
```

# Rules and Criteria

## Overview
A stock trading competition using simulated trading accounts, operated by coding in the Python language. The competition is restricted to common stocks within the SET50 index. The competition duration is 1 month (SET market is closed on Saturdays and Sundays).

## Ranking Criteria
The daily ranking display throughout the competition will be determined by the trading system's statistics, in the following order:
1.  **% Return** >>> Highest % Return (Focus on maximizing this value)
2.  **Maximum Drawdown** >>> Lowest Drawdown
3.  **Calmar Ratio** >>> Highest Calmar Ratio
4.  **Win Rate** >>> Highest Win Rate

## Minimum Requirements
Investment results at the end of the 1-month competition must meet the following minimum statistical criteria:
1.  % Return > 5%
2.  Maximum Drawdown < 30%
3.  Trades > 20 trades
4.  Win rate > 20%

---

## Calculation Methods
1.  **Return Rate**
    * $Return Rate (\%) = (NAV - Initial Balance) / Initial Balance \times 100$
2.  **Maximum Drawdown:** The largest peak-to-trough decline.
    * $Maximum Drawdown = ((Min\_after\_max\_value\_NAV - Max\_value\_NAV) / Max\_value\_NAV) \times 100$
    * Where: Max\_value\_NAV is the peak value (or NAV) during the analysis period.
    * Min\_after\_max\_value\_NAV is the lowest value (or NAV) that occurred after the peak.
3.  **Calmar Ratio:** A tool used to measure investment risk by comparing the average return to the risk incurred from Drawdown.
    * $Calmar Ratio = Average Annual Rate of Return / Maximum Drawdown$
    * Where (1) Average Annual Rate of Return is the average rate of return (in this case, the Return Rate).
    * (2) Maximum Drawdown is the maximum decline.
4.  **Win Rate:** The rate of successful trades.
    * $Win Rate (\%) = (Number of profitable trades / Total number of trades) \times 100$
    * For example, if there are 100 trades in total and 20 of them are profitable, you will have a win rate of 20% (or (20/100)*100)).

## Competition Rules
1.  Competitors must create a trading strategy written only in the Python language, with the following requirements:
    * The initial investment capital for testing the strategy is set at **10,000,000 THB** and cannot be increased during the competition.
    * Must use a **Cash Balance** account type. Sufficient funds and shares must be available before submitting a Buy/Sell order.
    * A minimum trading activity of **5 unique stock symbols** is required, which will be evaluated at the end of the competition period.
    * Only **Limit Order** or **Market-to-Limit Order** types with **IOC (Immediate or Cancel)** validity are permitted.
    * Executed trades will incur a total **commission fee of 0.157%** of the order value and a **7% VAT** on the commission. There is no minimum commission fee.
    * A **Slippage** of **1 Tick Size** is applied to trades.
2.  Competitors are not allowed to perform **Short Sells**.

---

# Trading Simulator

This simulation platform is built in Python OOP, which is designed to simulate a realistic trading environment using the SET50 daily ticks dataset. It supports core functionalities such as order matching, real-time data streaming, portfolio management, and fee calculations, providing a practical foundation for developing and testing algorithmic trading strategies.

Each trader is provided with an initial cash balance of 10,000,000 baht upon portfolio creation. This amount represents the trader's total available capital for the entire competition. Participants are expected to maximize profits by designing and implementing efficient trading algorithms to compete against other teams.

## Feature contained in the simulation:

### Stock & portfolio management:

  * Initiate & Load portfolio information.
  * Create summarized portfolio information throughout the day of trading.
  * Update the stock market value along with a streaming system.
  * Calculation of the necessary information for creating strategies.
  * Amount Cost
  * Average cost of stock in the portfolio
  * Unrealized & Unrealized in percentage
  * Realized
  * NAV (Net Asset Value)
  * Max draws down
  * Calmar ratio

### Ordering & matching during the streaming of the trading market:

  * Creating an order for selling or buying stock in the market.
  * Ordered stock must be in SET50 & volume required to be in full stock unit at least 100 volume (able to be mod by 100), and unable to order partial volume of stock.
  * For example, 100 volume is acceptable, but 150 (150% $100=50)$ cannot be ordered.
  * Ordering stock must be in either Buy or Sell.
  * When an order buys stocks from the market, if the trader's portfolio doesn't have enough cash balance, the order will be rejected.
  * When an order sells stock from the market, if the portfolio of trade doesn't have enough volume of stock in its portfolio, the order will be rejected.
  * Matching the order with the market streaming situation:
  * Validated orders will be sent to the order book, which will check the streaming market and match the order in terms of volume and price with the market.

## Installing dependency

Before you can run the trading simulator, you need to install the required dependencies. Follow the steps below to set up your Python environment properly:

1.  Ensure Python 3.13 or higher is installed.
    a. (Optional) Install pyenv to handle multiple Python versions.
2.  Download the TradeSim from here.
3.  (Recommended) Create and activate a virtual environment for TradeSim.
    ```shell
    cd path\to\TradeSim
    python -m venv TradeSim-venv
    .\TradeSim-venv\Scripts\activate
    ```
4.  Install required dependencies using the provided `requirements.txt` file:
    ```shell
    pip install -r requirements.txt
    ```
5.  If the Jupyter kernel is running, restart the kernel.

## Introduction to TradeSim

This notebook walks you through the usage of the TradeSim platform. You will learn how to load market data, register your team and strategy, run simulations, and view results. Follow each section to set up and test your trading algorithm correctly.

1.  This code block loads the daily tick data used in the simulation. Please make sure to update the daily tick file provided daily through Google Classroom. Participants must ensure the file path points to the latest version before running the simulation.

    ```python
    #TODO: Change ticks information daily
    daily_ticks = "./marketInfo/ticks/Daily_Ticks.csv"
    df = pd.read_csv(daily_ticks)
    df['TradeDateTime'] = pd.to_datetime(df['TradeDateTime'])
    grouped = df.groupby('ShareCode')
    ```

2.  The following block handles the team name and strategy name setup. Participants are required to assign their team and strategy names according to the specified format. Names must contain only alphanumeric characters, hyphens (-), or underscores (\_) and have a maximum length of 30.

    ```python
    #TODO: Replace with your team name
    team_name = "example"
    strategy_name = "example_strategy"
    pattern = r'^[A-Za-z0-9-_]{1,30}$'
    if not bool(re.match(pattern, team_name)) or not bool(re.match(pattern, strategy_name)):
        raise ValueError("Team name or strategy name is invalid. Please use only alphanumeric characters, hyphens, and underscores, with a maximum length of 30 characters.")

    # Init trade system
    trading_Sim = TradeSim.tradeSim(team_name)
    strategy_runner = trading_Sim.get_strategy_runner()
    ```

3.  This block handles the import and initialization of the trading strategy. If there is an error during import (e.g., the file or class is missing), it will be printed out, and the simulation will continue without a strategy. This allows participants to observe market behavior before implementing their strategy logic. For more information on implementing a strategy, please see Implement a Strategy.

    ```python
    try:
        strategy_module = importlib.import_module(f"strategy.{strategy_name}")
        importlib.reload(strategy_module)
    except ImportError as e:
        active_strategy_fn = None
        print(f"Error in strategy module: {e}")
    strategy_class = getattr(strategy_module, strategy_name, None)
    ```

4.  This block runs the full market simulation, where each tick is streamed and processed in real-time. The simulation supports two execution modes:

      * `with_visual = True`: Runs in visual mode, simulating real-time streaming with delays, ideal for demonstration or debugging.
      * `with_visual = False`: Runs in headless mode, reduces the runtime of the simulation, ideal for faster testing and evaluation.

    Use the `with_visual` flag to toggle between modes based on your preference.

    ```python
    #TODO: Change the with_visual according to your preference
    # True if you want to see the visual simulation
    # False if you want to finish the simulation faster
    with_visual = False
    threads = []
    latest_prices = {}
    def stream_symbol(symbol, data):
        # ... (rest of the simulation logic)

    # ... (code to run simulation)

    trading_Sim.flushTransactionLog()
    trading_Sim.create_transaction_summarize(team_name)
    trading_Sim.save_portfolio()
    trading_date = df['TradeDateTime'].dt.date.iloc[0]
    trading_Sim.save_summary_csv(trading_date)
    ```

## Implementing a Strategy

All custom strategies must be implemented inside the `strategy/` directory. You will find two important Python files:

  * `Strategies_template.py`: the abstract base class you must inherit from
  * `Example_strategy.py`: a basic example to help you get started

**TODO: Create your strategy class; you need to inherit from Strategies\_template.py**

### `Strategies_template.py`: The Base Class

This file defines the strategy interface. Your strategy must inherit from `Strategy_template` and implement the required `on_data()` method:

```python
from abc import ABC, abstractmethod
from datetime import timedelta

class Strategy_template(ABC):
    def __init__(self, owner, strategy_name, handler):
        self.owner = owner
        self.strategy_name = strategy_name
        self.handler = handler

    @abstractmethod
    def on_data(self, row):
        # MUST be implemented by subclass
        # DO NOT EDIT THIS CLASS
        pass
```

### `Example_strategy.py`: A Sample Strategy

The following class is a simple example of a custom strategy that buys and sells selected stocks based on basic rules:

```python
from strategy.Strategies_template import Strategy_template

class Example_strategy(Strategy_template):
    def __init__(self, handler):
        super().__init__("example", "Example_strategy", handler)
        self.buy_counts = {s: 0 for s in ["ADVANC", "AOT", "AWC", "BANPU", "BBL"]}
        self.sell_counts = {s: 0 for s in ["ADVANC", "AOT", "AWC", "BANPU", "BBL"]}

    def on_data(self, row):
        symbol = row['ShareCode']
        price = row['LastPrice']
        if not self.handler.check_port_has_stock(symbol, 100):
            self.handler.create_order_to_limit(100, price, "Buy", symbol)
        else:
            stocks = self.handler.get_stock_by_symbol(symbol)
            if stocks:
                buy_price = stocks[0].get_buy_price()
                if price > buy_price:
                    self.handler.create_order_to_limit(100, price, "Sell", symbol)
```

To ensure your strategy is loaded correctly, the following naming rules must be strictly followed:

  * The `team_name` and `strategy_name` declared in your main script (`TradingSimulation.ipynb`) must match the arguments passed to `super().__init__()` inside your strategy class.
    ```python
    #TODO: Replace with your team name
    team_name = "example"
    strategy_name = "example_strategy"
    ```
  * `Team_name` must be the first parameter in the class constructor.
  * `Strategy_name` must be the second parameter in the class constructor, and the class name.
    ```python
    class example_strategy(Strategy_template):
        def __init__(self, handler):
            super().__init__("example", "example_strategy", handler)
    ```
  * The `strategy_name` must also match the Python file name (without the `.py` extension).

### A guide to create a buy/sell order

To place an order in your strategy, use the method provided by the `handler` object. There are two variations of the create order method you can use: `create_order_to_limit()` and `create_order_at_market()`.

**The parameter:**

| Parameter | Type | Description |
| :--- | :--- | :--- |
| volume | int | Must be a multiple of 100 (e.g., 100, 200). |
| price | float | The price at which you want to trade. |
| side | string | Either "Buy" or "Sell" (case-insensitive). |
| symbol | str | Stock symbol (e.g., "AOT", must be in the SET50). |

#### Create order to limit

Place a limit order at the specified price. A limit order will only be executed at the given price or better. Use this method when you want more control over the execution price.
`create_order_to_limit(volume, price, side, symbol)`

**Example usage:**

```python
self.handler.create_order_to_limit(100, 35.67, "Buy", "AOT")
self.handler.create_order_to_limit(100, 39.89, "Sell", "PTT")
```

#### Create order at the market

Place a market order, which will be executed immediately at the best available price. Use this method when volume is more important than price precision.
`create_order_at_market(volume, side, symbol)`

**Example usage:**

```python
self.handler.create_order_at_market(1000, "Buy", "AOT")
self.handler.create_order_at_market(5000, "Sell", "PTT")
```

#### Return value from Create order

Both `create_order_to_limit()` and `create_order_at_market()` return a string message that indicates whether the order was successfully placed or rejected. This allows your strategy to confirm the outcome of the order and handle errors appropriately.

**Example of a valid order:**

```python
order_result = self.handler.create_order_to_limit(100, 58, "Buy", "AOT")
print(order_result)
```

**Output:**

```
Order for AOT (Vol: 100, Price: 58.0, Side: Buy) created successfully.
```

If the order is invalid, such as due to insufficient holdings or an incorrect volume, it will not be registered. Instead, an error message will be returned with the reason.

**Example of invalid order:**

```python
order_result = self.handler.create_order_to_limit(500, 58, "Sell", "AOT")
print(order_result)
```

**Output:**

```
[ERROR] Order for AOT (Vol: 500, Price: 58.0, Side: Sell) skipped due to Cannot sell AOT as it is not in the portfolio or insufficient volume.
```

## Accessing information in the daily ticks row

The `row` parameter passed to your strategy's `on_data()` method represents a single tick (data point) for a stock symbol at a specific time.

**Sample Structure of `row`:**

```json
{
    'ShareCode': 'EGCO',
    'TradeDateTime': Timestamp('2025-01-10 09:55:28'),
    'LastPrice': 113.0,
    'Volume': 7100,
    'Value': 802300.0,
    'Flag': 'BUY'
}
```

The data can be accessed as follows:

```python
symbol = row["ShareCode"]
price = row["LastPrice"]
timestamp = row["TradeDateTime"]
volume = row["Volume"]
```

This allows you to build condition-based logic using real-time tick information.

The following are key data from the `row`:

| Key | Type | Description |
| :--- | :--- | :--- |
| ShareCode | str | Stock symbol (e.g., "AOT") |
| TradeDateTime | pandas.Timestamp | Exact datetime of the trade tick. |
| LastPrice | float | The most recent traded price of the stock at this moment. |
| Volume | int | Number of shares traded in this tick. |
| Value | float | Number of shares traded in this tick. |
| Flag | str | Market condition flag |

**Note:** The `row` variable is set as read-only to prevent any value from being assigned.

## Accessing Portfolio Data

The following methods are available for participants to inspect the current state of their portfolio. These can be used during or after the simulation to monitor holdings, cash balance, or export results.

### Get information from the portfolio

`get_portfolio_info()`

A competitor can retrieve a summary of portfolio information from this method.
**Return:** Summary of information in portfolio

**Example:**

```python
pprint(self.handler.get_portfolio_info())
```

**Output:**

```json
{
    'Calmar Ratio': -17.836228391479434,
    'Cash Balance': 10074723.68,
    'Max Drawdown (%)': -28.44,
    'Max NAV': 10104164.72,
    'Min NAV': 7269444.2,
    'Net Asset Value': 10074723.68,
    'Number of Sells': 8,
    'Number of Stocks': 0,
    'Number of Wins': 8,
    'Owner': 'Testing',
    'Previous Day Max DD (%)': -28.44,
    'Realized P&L': 74723.68,
    'Relative Drawdown': -1.7145955018322022e-07,
    'Return rate': 507.31890610747763,
    'Total Cost': 0.0,
    'Unrealized %': 0.0,
    'Unrealized P&L': 0.0,
    'Win Rate': 100.0
}
```

### Get information from the stocks in the portfolio

`get_all_stocks_info()`

Competitors can retrieve information about their stocks that are in their portfolio from this method.
**Return:** Dicts of all stock information in the portfolio

**Example:**

```python
pprint(self.handler.get_all_stocks_info())
```

**Output:**

```json
[{
    'Symbol': 'AOT', 
    'Buy Price': 35.23, 
    'Actual Volume': 200, 
    'Average Cost': 0.0,
    'Market Price': 35, 
    'Amount Cost': 0.0, 
    'Market Value': 0.0, 
    'Unrealized P&L': 0.0,
    'Unrealized %': 0.0, 
    'Realized P&L': 0.0, 
    'Buy_time': '2025-06-23 11:27:53'
}]
```

### Get information from the stocks in the portfolio by symbol

`get_stock_by_symbol(symbol)`

Competitors can get specific stock by providing a preferred symbol of stock.
**Parameter:**

  * `symbol`: (string) - symbol

**Return:** List of stocks with the same symbol in the parameter

**Example:**

```python
print(self.handler.get_stock_by_symbol('AOT')[0].get_stock_info())
print(self.handler.get_stock_by_symbol('AOT')[1].get_stock_info())
```

**Output:**

```json
{'Symbol': 'AOT', 'Actual Volume': 100, 'Buy Price': 30.2, 'Market Price': 30, 'Average Cost': 0.0, 'Amount Cost': 0.0, 'Market Value': 0.0, 'Unrealized P&L': 0.0, 'Unrealized %': 0.0, 'Realized P&L': 0.0, 'Buy_time': '2025-06-23 11:54:48'}
{'Symbol': 'AOT', 'Actual Volume': 100, 'Buy Price': 35.23, 'Market Price': 35, 'Average Cost': 0.0, 'Amount Cost': 0.0, 'Market Value': 0.0, 'Unrealized P&L': 0.0, 'Unrealized %': 0.0, 'Realized P&L': 0.0, 'Buy_time': '2025-06-23 11:54:48'}
```

### Check if portfolio has stock in the provided symbol

`has_stock(symbol, volume)`

A competitor can check if their portfolio has a stock of the preferred symbol and volume or not with this method.
**Parameter:**

  * `symbol`: (string) - symbol
  * `volume`: (integer) - volume

**Return:** Boolean (True or False)

**Example:**

```python
print(self.handler.has_stock('AOT', 100))
```

**Output:**

```
True
```

## Additional getter method for strategy runner

The `self.handler` object provides several getter methods to help participants monitor their portfolio throughout the simulation. These methods can be used to retrieve information such as holdings, cash balance, NAV, drawdowns, and performance metrics. Below is a list of available getter methods:

| Method | Description |
| :--- | :--- |
| **Portfolio Checks** | |
| `check_port_has_stock(symbol, volume)` | Returns True if the portfolio holds at least a volume of the symbol. |
| **Portfolio Info** | |
| `get_owner()` | Returns the team name. |
| `get_all_stocks_info()` | Returns a list of summarized stock info, grouped by symbol. |
| `get_portfolio_info()` | Returns a summary of the current portfolio. |
| `get_stock_by_symbol(symbol)` | Returns a specific stock object by symbol. |
| `get_total_stock_volume_by_symbol(symbol)` | Returns the total number of shares held for a specific symbol. |
| `get_cash_balance()` | Returns the current cash available in the portfolio. |
| **Performance Metrics** | |
| `get_roi()` | Returns the portfolio's current Return on Investment. |
| `get_max_draw_down()` | Returns the maximum drawdown encountered so far. |
| `get_number_of_wins()` | Returns the total number of profitable trades executed. |
| `get_number_of_sells()` | Returns the total number of sell transactions executed. |

## Get information from stock in portfolio

The portfolio itself summarizes and totals all of the information from the stock. If a competitor would like to use more detailed stock information, competitors are required to call it via a specific method.

`get_stock_info()`

A competitor can call this method to get all of the information about the stock.
**Return:** Dicts of stock information

**Example:**

```python
print(self.handler.get_stock_by_symbol('AOT')[0].get_stock_info())
print(self.handler.get_stock_by_symbol('ADVANC')[0].get_stock_info())
```

**Output:**

```json
{'Symbol': 'AOT', 'Actual Volume': 100, 'Buy Price': 30.2, 'Market Price': 30, 'Average Cost': 0.0, 'Amount Cost': 0.0, 'Market Value': 0.0, 'Unrealized P&L': 0.0, 'Unrealized %': 0.0, 'Realized P&L': 0.0, 'Buy_time': '2025-06-23 12:42:14'}
{'Symbol': 'ADVANC', 'Actual Volume': 100, 'Buy Price': 280.87, 'Market Price': 279, 'Average Cost': 0.0, 'Amount Cost': 0.0, 'Market Value': 0.0, 'Unrealized P&L': 0.0, 'Unrealized %': 0.0, 'Realized P&L': 0.0, 'Buy_time': '2025-06-23 12:42:14'}
```

Keep in mind that a stock that has been bought can only be accessed via the `get_stock_by_symbol()` method as shown in the example. Once competitors can access a stock in the portfolio, these following getter methods are now available to be used.

## Additional getter method for stock

The following methods are available to retrieve detailed information about a stock position held in the portfolio. These can be useful for analysis, logging, or debugging a strategy during simulation.

| Method | Description |
| :--- | :--- |
| **Basic Info** | |
| `get_symbol()` | Returns the stock symbol (e.g., "AOT", "PTT"). |
| **Trade Details** | |
| `get_buy_price()` | Returns the price per share at which the stock was purchased. |
| `get_start_vol()` | Returns the initial number of shares bought. |
| `get_actual_vol()` | Returns the remaining shares currently held. |
| `get_buy_time_str()` | Returns the timestamp of the purchase in a readable format. |
| **Valuation** | |
| `get_mkt_price()` | Returns the current market price of the stock. |
| `get_amount_cost()` | Returns the total cost spent on this stock (buy\_price \* volume). |
| `get_market_value()` | Returns the current market value of the held stock (market\_price \* volume). |
| **Performance** | |
| `get_unrealized()` | Returns the current unrealized profit/loss. |
| `get_unrealized_in_percentage()` | Returns unrealized profit/loss as a percentage. |
| `get_realized()` | Returns realized profit/loss (from partial sells). |

## Penalties for Unauthorized Modification of the Trading System

To ensure fairness and integrity in this trading simulation, the following rules and penalties apply:

### Prohibited Actions

Any developer found to have intentionally modified any part of the trading system other than the designated strategy section for the purpose of gaining an unfair advantage or bypassing system rules will be subject to penalties, including:

  * Modifying order execution logic
  * Altering portfolio/account handling mechanisms
  * Changing the data feed or timing
  * Interfering with result tracking or logging processes
  * Any code manipulation that affects global behavior or evaluation outcomes

### Intention and Scope

If our team detects intentional modification aimed at benefiting a specific team by cheating or bypassing the agent rules of the competition:

  * Your team's simulation results will be disqualified and not counted in the final evaluation.
  * Your strategy will be removed from the pool of valid entries.

### Permitted Area

You are allowed to:

  * Modify or implement your strategy within the designated strategy file that was inherited from `strategy_template.py`
  * Use public APIs and allow utility/helper functions that do not compromise the system's fairness

### Final Decision

All decisions regarding disqualification and result invalidation are final and at the discretion of the organizing team.

## Run The Simulation

-----

```python
import pandas as pd
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
import importlib
import re

# Import trading library
from tradeSim import TradeSim
from tradeSim import StrategyHandler
```

-----

Welcome to the simulation platform\!

This Python-based environment is designed to replicate a realistic trading experience using the SET50 daily ticks dataset. It supports essential features like real-time data streaming, order matching, portfolio management, and fee calculations, giving you everything you need to build and test your algorithmic trading strategies.

Each participant begins with a virtual portfolio containing 10,000,000 Baht in starting capital. Your challenge is to design effective trading algorithms and compete with other teams to generate the highest return. Think smart, trade fast, and enjoy the competition\!

-----

-----

### **Import Daily ticks information for trading infomation**

For each day within compitition, the tick information will be provided daily

-----

```python
#TODO: Change ticks information daily
daily_ticks = "./marketInfo/ticks/2025-10-24.csv"

df = pd.read_csv(daily_ticks)
df['TradeDateTime'] = pd.to_datetime(df['TradeDateTime'])
grouped = df.groupby('ShareCode')
```

-----

### **Now, name your team\!**

The code section below will create your trading simulation class using the team name you provide.

  - Your team name will be set as the `owner` of the `TraderPortfolio` from `trading_sim`.
  - The `SimExecution` class will handle order execution for buying stocks in the market.

**Team name requirements:**

  - Must use English letters or numbers
  - No spaces allowed
  - Hyphens (`-`) and underscores (`_`) are allowed
  - Must be **30 characters or fewer**

-----

```python
team_name = "FemboyLover"
strategy_name = "IntradayMeanReversion"

pattern = r'^[A-Za-z0-9-_]{1,30}$'
if not bool(re.match(pattern, team_name)) or not bool(re.match(pattern, strategy_name)):
    raise ValueError("Team name or strategy name is invalid. Please use only alphanumeric characters, hyphens, and underscores, with a maximum length of 30 characters.")

# Init trade system
trading_Sim = TradeSim.tradeSim(team_name) 
strategy_runner = trading_Sim.get_strategy_runner()
```

-----

### **Craft Your Strategy**

To simulate your trading strategy within the platform,  
you must create your own strategy class by inheriting from the `strategy_template` class.

Once you've finished writing or are ready to test it,  
run the code below to import your strategy into this notebook.

-----

```python
try:
    strategy_module = importlib.import_module(f"strategy.{strategy_name}")
    importlib.reload(strategy_module)
except ImportError as e:
    active_strategy_fn = None
    print(f"Error in strategy module: {e}")
    
strategy_class = getattr(strategy_module, strategy_name, None)
```

-----

-----

### **The Simulation**

The simulation models a real-time market environment using a thread handler, where each thread streams data for a specific symbol in the SET50 index, as provided in `marketInfo/ticks`. This section of the code iterates through all entries in the CSV file, applying each competitor’s strategy based on the current market data. During the streaming process, the system attempts to match any pending orders in the order books and updates the market prices in the competitors’ portfolios for any held stocks.

##### *For more detailed explanation please look at document file*

> By setting `with_visual` to `False`, the simulation runs significantly faster.

-----

```python
#TODO: Change the `with_visual` according to your preference
# True if you want to see the visual simulation  
# False if you want to finish the simulation faster
with_visual = False
```

-----

```python
latest_prices = {}

# === Render Helpers ===
def render_market_table():
    table = Table(title="📈 Market Stream")
    table.add_column("Symbol")
    table.add_column("Last Price", justify="right")
    table.add_column("Volume", justify="right")
    table.add_column("Flag", justify="right")

    snapshot = dict(latest_prices)  # copy to avoid mid-update issues

    for sym, data in snapshot.items():
        table.add_row(
            sym,
            f"{data['price']:.2f}",
            str(data["volume"]),
            data["Flag"]
        )
    return table


def render_portfolio_table():
    table = Table(title=f"💼 Portfolio: {strategy_runner.get_owner()}", expand=True)
    table.add_column("Cash Balance", no_wrap=True, width=18)
    table.add_column("Symbol")
    table.add_column("Actual Vol", justify="right")
    table.add_column("Buy Price", justify="right")
    table.add_column("Market Price", justify="right")
    table.add_column("Average Cost", justify="right")
    table.add_column("Amount Cost", justify="right")
    table.add_column("Market Value", justify="right")
    table.add_column("Unrealized", justify="right")
    table.add_column("Unreal. %", justify="right")
    table.add_column("Realized", justify="right")
    table.add_column("Buy Time", justify="center")

    stock_infos = strategy_runner.get_all_stocks_info()
    cash_str = f"{strategy_runner.get_cash_balance():,.2f}"
    cash_displayed = False

    if not stock_infos:
        table.add_row(cash_str, "-", "0", "-", "-", "-", "-", "-", "-", "-", "-", "-")
    else:
        for stock in stock_infos:
            table.add_row(
                cash_str if not cash_displayed else "",
                stock["Symbol"],
                str(stock["Actual Volume"]),
                f"{stock['Buy Price']:.2f}",
                f"{stock['Market Price']:.2f}",
                f"{stock['Average Cost']:.2f}",
                f"{stock['Amount Cost']:.2f}",
                f"{stock['Market Value']:.2f}",
                f"{stock['Unrealized P&L']:.2f}",
                f"{stock['Unrealized %']:.2f}%",
                f"{stock['Realized P&L']:.2f}",
                stock["Buy time"]
            )
            cash_displayed = True

    # Add metrics summary
    table.add_section()
    table.add_row("🔢 Metrics", "", "", "", "", "", "", "", "", "", "", "")
    table.add_row("ROI (%)", f"{strategy_runner.get_roi():.2f}%", "", "", "", "", "", "", "", "", "", "")
    table.add_row("Max Drawdown (%)", f"{strategy_runner.get_max_draw_down():.2f}%", "", "", "", "", "", "", "", "", "", "")
    table.add_row("Win Count", str(strategy_runner.get_number_of_wins()), "", "", "", "", "", "", "", "", "", "")
    table.add_row("Sell Count", str(strategy_runner.get_number_of_sells()), "", "", "", "", "", "", "", "", "", "")
    return table


def render_layout():
    layout = Layout()
    layout.split_column(
        Layout(Panel(render_market_table(), expand=True), name="market"),
        Layout(Panel(render_portfolio_table(), expand=True), name="portfolio")
    )
    return layout


# === Simulation Core ===
handlers = {
    symbol: StrategyHandler.StrategyHandler(strategy_class, strategy_runner)
    for symbol, _ in grouped
}

max_length = max(len(group) for _, group in grouped)
layout = render_layout()

if with_visual:
    with Live(layout, refresh_per_second=2):
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

            layout["market"].update(Panel(render_market_table()))
            layout["portfolio"].update(Panel(render_portfolio_table()))

else:
    # Headless (no visual mode)
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

# === Final flush/save ===
layout["market"].update(Panel(render_market_table()))
layout["portfolio"].update(Panel(render_portfolio_table()))

trading_Sim.flushTransactionLog()
trading_Sim.flushErrorLogger()
trading_Sim.create_transaction_summarize(team_name)
trading_Sim.save_portfolio()

trading_date = df['TradeDateTime'].dt.date.iloc[0]
trading_Sim.save_summary_csv(trading_date)
```

-----

### **Examine Portfolio Information**

You can view portfolio statistics using the provided methods.

For example:

```
strategy_runner.get_all_stock_info() -> Returns a summary of each stock in the portfolio.
strategy_runner.get_portfolio_info() -> Returns a summary of portfolio details such as cash balance, NAV, and ROI.
```

Full documentation is available in the provided PDF.

-----

```python
portInfo = strategy_runner.get_portfolio_info()
stockInfo = strategy_runner.get_all_stocks_info()
pd.DataFrame([portInfo]).T
```

-----

```python
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000) 
pd.set_option('display.max_rows', None)

df = pd.DataFrame(stockInfo)
print(df)
```