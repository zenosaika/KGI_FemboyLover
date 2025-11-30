from strategy.Strategies_template import Strategy_template
import datetime

class IntradayMeanReversion(Strategy_template):
    def __init__(self, handler):

        team_name = "FemboyLover"  
        strategy_name = "IntradayMeanReversion"
        
        super().__init__(team_name, strategy_name, handler)

        self.position_size_thb = 500_000
        self.buy_trigger_pct = 0.985
        self.stop_loss_pct = 0.98
        
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
            }

    def on_data(self, row):
        symbol = row['ShareCode']
        price = row['LastPrice']
        volume = row['Volume']
        timestamp = row['TradeDateTime']
        current_time = timestamp.time()
        
        if price <= 0 or volume <= 0:
            return
        
        if symbol not in self.symbol_data:
            self._init_symbol_data(symbol)
        data = self.symbol_data[symbol]

        data['vwap_num'] += price * volume
        data['vwap_den'] += volume
        if data['vwap_den'] > 0:
            data['vwap'] = data['vwap_num'] / data['vwap_den']
        else:
            return

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
            
            take_profit_price = data['vwap']
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
                return # Too late to open a new position
                
            # Check Buy Signal : Price 1.5% below VWAP
            buy_trigger_price = data['vwap'] * self.buy_trigger_pct
            
            if price <= buy_trigger_price:
                if self.handler.get_cash_balance() > self.position_size_thb:
                    volume_to_buy = (self.position_size_thb / price) // 100 * 100
                    
                    if volume_to_buy >= 100:
                        self.handler.create_order_to_limit(volume_to_buy, price, "Buy", symbol)
                        data['buy_price'] = 1.0