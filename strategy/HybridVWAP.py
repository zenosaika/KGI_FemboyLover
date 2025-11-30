from strategy.Strategies_template import Strategy_template
import datetime

class HybridVWAP(Strategy_template):
    """
    Hybrid VWAP Strategy - Adaptive switching between modes

    - Normal Mode (Deep Discount): Buy at 2.5% below VWAP, fewer high-quality trades
    - Anomaly Mode (Aggressive): Buy at 1.5% below VWAP, capture maximum opportunity

    Switches to Anomaly Mode when Tick Clustering Ratio (TCR) >= 50%
    (TCR = % of stocks trading at <= 2 unique price levels)
    """

    def __init__(self, handler):
        team_name = "FemboyLover"
        strategy_name = "HybridVWAP"

        super().__init__(team_name, strategy_name, handler)

        # Mode tracking
        self.is_anomaly_mode = False
        self.mode_check_time = datetime.time(10, 30)  # Check at 10:30
        self.mode_checked_today = False
        self.current_date = None

        # Deep Discount parameters (Normal mode)
        self.normal_position_size = 600_000
        self.normal_buy_trigger = 0.975      # 2.5% below VWAP
        self.normal_take_profit = 1.005      # 0.5% above VWAP
        self.normal_stop_loss = 0.97         # 3% stop loss

        # Aggressive parameters (Anomaly mode)
        self.anomaly_position_size = 500_000
        self.anomaly_buy_trigger = 0.985     # 1.5% below VWAP
        self.anomaly_take_profit = 1.0       # At VWAP
        self.anomaly_stop_loss = 0.98        # 2% stop loss

        # Active parameters (set based on mode)
        self.position_size_thb = self.normal_position_size
        self.buy_trigger_pct = self.normal_buy_trigger
        self.take_profit_pct = self.normal_take_profit
        self.stop_loss_pct = self.normal_stop_loss

        self.stop_new_trades_time = datetime.time(16, 20)
        self.liquidate_time = datetime.time(16, 25)

        self.symbol_data = {}

    def _init_symbol_data(self, symbol):
        if symbol not in self.symbol_data:
            self.symbol_data[symbol] = {
                'vwap_num': 0.0,
                'vwap_den': 0.0,
                'vwap': 0.0,
                'buy_price': 0.0,
                'unique_prices': set(),
            }

    def _calculate_tcr(self):
        """Calculate Tick Clustering Ratio - % of stocks at <= 2 price levels"""
        if not self.symbol_data:
            return 0

        clustered = 0
        total = 0

        for symbol, data in self.symbol_data.items():
            if data['vwap_den'] > 0:  # Has been traded
                total += 1
                if len(data['unique_prices']) <= 2:
                    clustered += 1

        return (clustered / total * 100) if total > 0 else 0

    def _switch_to_anomaly_mode(self):
        """Switch to aggressive anomaly mode"""
        self.is_anomaly_mode = True
        self.position_size_thb = self.anomaly_position_size
        self.buy_trigger_pct = self.anomaly_buy_trigger
        self.take_profit_pct = self.anomaly_take_profit
        self.stop_loss_pct = self.anomaly_stop_loss

    def _switch_to_normal_mode(self):
        """Switch to conservative normal mode"""
        self.is_anomaly_mode = False
        self.position_size_thb = self.normal_position_size
        self.buy_trigger_pct = self.normal_buy_trigger
        self.take_profit_pct = self.normal_take_profit
        self.stop_loss_pct = self.normal_stop_loss

    def on_data(self, row):
        symbol = row['ShareCode']
        price = row['LastPrice']
        volume = row['Volume']
        timestamp = row['TradeDateTime']
        current_time = timestamp.time()
        current_date = timestamp.date()

        if price <= 0 or volume <= 0:
            return

        # Reset for new day
        if self.current_date != current_date:
            self.current_date = current_date
            self.mode_checked_today = False
            self.is_anomaly_mode = False
            self._switch_to_normal_mode()
            # Reset unique prices tracking for new day
            for sym_data in self.symbol_data.values():
                sym_data['unique_prices'] = set()

        if symbol not in self.symbol_data:
            self._init_symbol_data(symbol)
        data = self.symbol_data[symbol]

        # Track unique prices for TCR calculation
        data['unique_prices'].add(price)

        # Update VWAP
        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        if data['vwap_den'] > 0:
            data['vwap'] = data['vwap_num'] / data['vwap_den']
        else:
            return

        # Check for anomaly mode at 10:30
        if not self.mode_checked_today and current_time >= self.mode_check_time:
            self.mode_checked_today = True
            tcr = self._calculate_tcr()

            if tcr >= 50:
                self._switch_to_anomaly_mode()

        total_volume_held = self.handler.get_total_stock_volume_by_symbol(symbol)
        currently_has_position = total_volume_held > 0

        # Sell Logic
        if currently_has_position:
            if data['buy_price'] == 0.0:
                stocks = self.handler.get_stock_by_symbol(symbol)
                if stocks:
                    total_cost = sum(s.get_buy_price() * s.get_start_vol() for s in stocks)
                    total_vol = sum(s.get_start_vol() for s in stocks)
                    if total_vol > 0:
                        data['buy_price'] = total_cost / total_vol
                    else:
                        return
                else:
                    return

            take_profit_price = data['vwap'] * self.take_profit_pct
            stop_loss_price = data['buy_price'] * self.stop_loss_pct

            sell = False

            # EOD Liquidation
            if current_time >= self.liquidate_time:
                sell = True

            # Take Profit
            elif price >= take_profit_price:
                sell = True

            # Stop Loss
            elif price <= stop_loss_price:
                sell = True

            if sell:
                self.handler.create_order_to_limit(total_volume_held, price, "Sell", symbol)
                data['buy_price'] = 0.0

        # Buy Logic
        else:
            if data['buy_price'] != 0.0:
                data['buy_price'] = 0.0

            # Don't trade near market close
            if current_time >= self.stop_new_trades_time:
                return

            buy_trigger_price = data['vwap'] * self.buy_trigger_pct

            if price <= buy_trigger_price:
                if self.handler.get_cash_balance() > self.position_size_thb:
                    volume_to_buy = (self.position_size_thb / price) // 100 * 100

                    if volume_to_buy >= 100:
                        self.handler.create_order_to_limit(volume_to_buy, price, "Buy", symbol)
                        data['buy_price'] = 1.0
