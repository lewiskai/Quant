class TradingMonitor:
    def __init__(self):
        self.metrics = {}
        self.alerts = []
        
    def update_metrics(self, current_price, positions, balance):
        self.metrics['current_price'] = current_price
        self.metrics['active_positions'] = len(positions)
        self.metrics['account_balance'] = balance
        self.check_alerts()
        
    def check_alerts(self):
        if self.metrics['active_positions'] >= 3:
            self.alerts.append("Position Warning: Near maximum limit")
        if self.metrics['account_balance'] < self.initial_balance * 0.9:
            self.alerts.append("Balance Warning: Near stop loss level")