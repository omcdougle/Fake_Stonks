import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter, DayLocator
import numpy as np
import matplotlib.dates as mdates
import mplfinance as mpf

class FakeStockTradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fake Stock Trading App")
        self.root.geometry("1200x800")
        
        # Initialize user portfolio data
        self.initial_balance = 100000.00  # Start with $100,000
        self.portfolio_file = "portfolio.json"
        self.load_portfolio()
        
        # Current stock data
        self.current_stock = None
        self.current_price = 0.0
        
        # Auto trading variables
        self.buy_trade_count = 0
        self.sell_trade_count = 0
        self.last_trade_time = datetime.now()
        
        # Create main frames
        self.create_frames()
        
        # Create widgets
        self.create_widgets()
        
        # Update portfolio display
        self.update_portfolio_display()
        
        # Update stock prices periodically
        self.update_stock_prices()

    def load_portfolio(self):
        """Load portfolio from file or create a new one"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    self.portfolio = json.load(f)
            except:
                self.initialize_portfolio()
        else:
            self.initialize_portfolio()
    
    def initialize_portfolio(self):
        """Create a new portfolio with default values"""
        self.portfolio = {
            "cash_balance": self.initial_balance,
            "stocks": {},
            "transaction_history": []
        }
        self.save_portfolio()
    
    def save_portfolio(self):
        """Save portfolio to file"""
        with open(self.portfolio_file, 'w') as f:
            json.dump(self.portfolio, f, indent=4)

    def create_frames(self):
        """Create the main frames for the app"""
        # Main container frame
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for search and trading (fixed height)
        self.top_frame = ttk.Frame(self.main_container, padding="10")
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Middle frame for stock info and trading (fixed height)
        self.middle_frame = ttk.Frame(self.main_container, padding="10")
        self.middle_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create a paned window to allow resizing between chart and portfolio
        self.paned_window = ttk.PanedWindow(self.main_container, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Chart frame for candlestick chart (resizable)
        self.chart_frame = ttk.LabelFrame(self.paned_window, text="Price Chart", padding="10")
        
        # Bottom frame for portfolio and transaction history (resizable)
        self.bottom_frame = ttk.Frame(self.paned_window, padding="10")
        
        # Add frames to paned window with initial sizes
        self.paned_window.add(self.chart_frame, weight=1)
        self.paned_window.add(self.bottom_frame, weight=1)
        
        # Split bottom frame into portfolio and history
        self.portfolio_frame = ttk.LabelFrame(self.bottom_frame, text="Your Portfolio", padding="10")
        self.portfolio_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.history_frame = ttk.LabelFrame(self.bottom_frame, text="Transaction History", padding="10")
        self.history_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

    def create_widgets(self):
        """Create all widgets for the app"""
        # Top frame widgets - Search and account info
        ttk.Label(self.top_frame, text="Stock Symbol:").pack(side=tk.LEFT, padx=5)
        self.symbol_entry = ttk.Entry(self.top_frame, width=10)
        self.symbol_entry.pack(side=tk.LEFT, padx=5)
        self.symbol_entry.insert(0, "AAPL")
        
        ttk.Button(self.top_frame, text="Search", command=self.search_stock).pack(side=tk.LEFT, padx=5)
        
        # Period selection for chart
        ttk.Label(self.top_frame, text="Period:").pack(side=tk.LEFT, padx=10)
        self.period_var = tk.StringVar(value="1mo")
        period_combo = ttk.Combobox(self.top_frame, textvariable=self.period_var, 
                                    values=["1d", "5d", "1mo", "3mo", "6mo", "1y"], 
                                    width=5, state="readonly")
        period_combo.pack(side=tk.LEFT, padx=5)
        period_combo.bind("<<ComboboxSelected>>", lambda e: self.update_chart())
        
        self.balance_label = ttk.Label(self.top_frame, text=f"Cash Balance: ${self.portfolio['cash_balance']:.2f}")
        self.balance_label.pack(side=tk.RIGHT, padx=10)
        
        # Add frequency selection for auto trading
        ttk.Label(self.top_frame, text="Auto Trade Frequency:").pack(side=tk.LEFT, padx=10)
        self.frequency_var = tk.StringVar(value="5m")  # Default frequency
        frequency_combo = ttk.Combobox(self.top_frame, textvariable=self.frequency_var, 
                                        values=["1m", "5m", "10m", "15m", "30m", "1h"], 
                                        width=5, state="readonly")
        frequency_combo.pack(side=tk.LEFT, padx=5)
        
        # Add technical indicators selection
        ttk.Label(self.top_frame, text="Indicators:").pack(side=tk.LEFT, padx=10)
        self.show_ma = tk.BooleanVar(value=True)
        self.show_rsi = tk.BooleanVar(value=False)
        self.show_macd = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(self.top_frame, text="MA", variable=self.show_ma, 
                       command=self.update_chart).pack(side=tk.LEFT)
        ttk.Checkbutton(self.top_frame, text="RSI", variable=self.show_rsi, 
                       command=self.update_chart).pack(side=tk.LEFT)
        ttk.Checkbutton(self.top_frame, text="MACD", variable=self.show_macd, 
                       command=self.update_chart).pack(side=tk.LEFT)
        
        # Add reset button
        self.reset_button = ttk.Button(self.top_frame, text="Reset Account", command=self.reset_account)
        self.reset_button.pack(side=tk.LEFT, padx=10)

        # Middle frame widgets - Stock info and trading
        self.stock_info_frame = ttk.LabelFrame(self.middle_frame, text="Stock Information", padding="10")
        self.stock_info_frame.pack(fill=tk.X, pady=5)
        
        self.stock_name_label = ttk.Label(self.stock_info_frame, text="Stock: Not selected")
        self.stock_name_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.stock_price_label = ttk.Label(self.stock_info_frame, text="Current Price: N/A")
        self.stock_price_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.stock_change_label = ttk.Label(self.stock_info_frame, text="Change: N/A")
        self.stock_change_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        
        # Trading controls
        self.trading_frame = ttk.LabelFrame(self.middle_frame, text="Trade", padding="10")
        self.trading_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.trading_frame, text="Quantity:").grid(row=0, column=0, padx=5, pady=5)
        self.quantity_entry = ttk.Entry(self.trading_frame, width=10)
        self.quantity_entry.grid(row=0, column=1, padx=5, pady=5)
        self.quantity_entry.insert(0, "1")
        
        ttk.Label(self.trading_frame, text="Total Cost:").grid(row=0, column=2, padx=5, pady=5)
        self.total_cost_label = ttk.Label(self.trading_frame, text="$0.00")
        self.total_cost_label.grid(row=0, column=3, padx=5, pady=5)
        
        self.buy_button = ttk.Button(self.trading_frame, text="Buy", command=self.buy_stock)
        self.buy_button.grid(row=0, column=4, padx=5, pady=5)
        
        self.sell_button = ttk.Button(self.trading_frame, text="Sell", command=self.sell_stock)
        self.sell_button.grid(row=0, column=5, padx=5, pady=5)
        
        # Add auto-trading controls to the trading frame
        ttk.Separator(self.trading_frame, orient=tk.HORIZONTAL).grid(row=1, column=0, columnspan=6, sticky="ew", pady=5)
        
        # Auto-trading frame
        auto_trade_frame = ttk.LabelFrame(self.trading_frame, text="Auto Trading", padding="5")
        auto_trade_frame.grid(row=2, column=0, columnspan=6, sticky="ew", pady=5)
        
        # Auto-trading controls
        self.auto_trade_var = tk.BooleanVar(value=False)
        self.auto_trade_cb = ttk.Checkbutton(auto_trade_frame, text="Enable Auto Trading", 
                                             variable=self.auto_trade_var,
                                             command=self.toggle_auto_trading)
        self.auto_trade_cb.grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Label(auto_trade_frame, text="Auto Quantity:").grid(row=0, column=1, padx=5, pady=5)
        self.auto_quantity_entry = ttk.Entry(auto_trade_frame, width=8)
        self.auto_quantity_entry.grid(row=0, column=2, padx=5, pady=5)
        self.auto_quantity_entry.insert(0, "10")
        
        ttk.Label(auto_trade_frame, text="Max Investment:").grid(row=0, column=3, padx=5, pady=5)
        self.max_investment_entry = ttk.Entry(auto_trade_frame, width=10)
        self.max_investment_entry.grid(row=0, column=4, padx=5, pady=5)
        self.max_investment_entry.insert(0, "10000")
        
        self.auto_status_label = ttk.Label(auto_trade_frame, text="Auto Trading: Disabled", foreground="gray")
        self.auto_status_label.grid(row=0, column=5, padx=5, pady=5)
        
        # Create candlestick chart
        self.setup_chart()
        
        # Portfolio display with scrollbar
        portfolio_container = ttk.Frame(self.portfolio_frame)
        portfolio_container.pack(fill=tk.BOTH, expand=True)

        self.portfolio_tree = ttk.Treeview(portfolio_container, columns=("Symbol", "Shares", "Avg Price", "Current Price", "Value", "Gain/Loss"))
        self.portfolio_tree.heading("#0", text="")
        self.portfolio_tree.heading("Symbol", text="Symbol")
        self.portfolio_tree.heading("Shares", text="Shares")
        self.portfolio_tree.heading("Avg Price", text="Avg Price")
        self.portfolio_tree.heading("Current Price", text="Current Price")
        self.portfolio_tree.heading("Value", text="Value")
        self.portfolio_tree.heading("Gain/Loss", text="Gain/Loss")

        self.portfolio_tree.column("#0", width=0, stretch=tk.NO)
        self.portfolio_tree.column("Symbol", width=80)
        self.portfolio_tree.column("Shares", width=80)
        self.portfolio_tree.column("Avg Price", width=100)
        self.portfolio_tree.column("Current Price", width=100)
        self.portfolio_tree.column("Value", width=100)
        self.portfolio_tree.column("Gain/Loss", width=100)

        # Add scrollbar to portfolio tree
        portfolio_scrollbar = ttk.Scrollbar(portfolio_container, orient="vertical", command=self.portfolio_tree.yview)
        self.portfolio_tree.configure(yscrollcommand=portfolio_scrollbar.set)
        portfolio_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.portfolio_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Transaction history display with scrollbar
        history_container = ttk.Frame(self.history_frame)
        history_container.pack(fill=tk.BOTH, expand=True)

        self.history_tree = ttk.Treeview(history_container, columns=("Date", "Type", "Symbol", "Shares", "Price", "Total", "Commission"))
        self.history_tree.heading("#0", text="")
        self.history_tree.heading("Date", text="Date")
        self.history_tree.heading("Type", text="Type")
        self.history_tree.heading("Symbol", text="Symbol")
        self.history_tree.heading("Shares", text="Shares")
        self.history_tree.heading("Price", text="Price")
        self.history_tree.heading("Total", text="Total")
        self.history_tree.heading("Commission", text="Commission")

        self.history_tree.column("#0", width=0, stretch=tk.NO)
        self.history_tree.column("Date", width=150)
        self.history_tree.column("Type", width=80)
        self.history_tree.column("Symbol", width=80)
        self.history_tree.column("Shares", width=80)
        self.history_tree.column("Price", width=100)
        self.history_tree.column("Total", width=100)
        self.history_tree.column("Commission", width=100)

        # Add scrollbar to history tree
        history_scrollbar = ttk.Scrollbar(history_container, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind quantity entry to update total cost
        self.quantity_entry.bind("<KeyRelease>", self.update_total_cost)

    def update_total_cost(self, event):
        """Update the total cost based on quantity and current price"""
        try:
            quantity = int(self.quantity_entry.get())
            total_cost = quantity * self.current_price
            self.total_cost_label.config(text=f"${total_cost:.2f}")
        except ValueError:
            self.total_cost_label.config(text="$0.00")

    def toggle_auto_trading(self):
        """Enable or disable auto trading"""
        if self.auto_trade_var.get():
            # Validate settings before enabling
            try:
                auto_quantity = int(self.auto_quantity_entry.get())
                max_investment = float(self.max_investment_entry.get())
                
                if auto_quantity <= 0 or max_investment <= 0:
                    messagebox.showerror("Error", "Auto quantity and max investment must be positive")
                    self.auto_trade_var.set(False)
                    return
                    
                # Enable auto trading
                self.auto_status_label.config(text="Auto Trading: Enabled", foreground="green")
                messagebox.showinfo("Auto Trading", "Auto trading has been enabled. The system will automatically execute trades based on technical indicators.")
                
                # Start monitoring for signals
                self.check_for_trading_signals()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for auto quantity and max investment")
                self.auto_trade_var.set(False)
        else:
            # Disable auto trading
            self.auto_status_label.config(text="Auto Trading: Disabled", foreground="gray")
            messagebox.showinfo("Auto Trading", "Auto trading has been disabled.")

    def check_for_trading_signals(self):
        """Check for trading signals and execute trades if auto trading is enabled"""
        if not self.auto_trade_var.get():
            return
        
        # Only proceed if we have a current stock
        if self.current_stock:
            # Get the latest recommendation
            if hasattr(self, 'recommendation_label'):
                recommendation = self.recommendation_label.cget('text')
                
                # Execute trade based on recommendation
                if "BUY" in recommendation:
                    self.execute_auto_trade("BUY")
                elif "SELL" in recommendation:
                    self.execute_auto_trade("SELL")
        
        # Schedule next check based on selected frequency
        frequency_mapping = {
            "1m": 60000,  # 1 minute
            "5m": 300000,  # 5 minutes
            "10m": 600000,  # 10 minutes
            "15m": 900000,  # 15 minutes
            "30m": 1800000,  # 30 minutes
            "1h": 3600000,  # 1 hour
        }
        
        frequency = frequency_mapping.get(self.frequency_var.get(), 300000)  # Default to 5 minutes
        self.root.after(frequency, self.check_for_trading_signals)

    def execute_auto_trade(self, trade_type):
        """Execute an automatic trade based on signals"""
        if not self.current_stock:
            return
        
        # Check if 24 hours have passed since the last trade
        if (datetime.now() - self.last_trade_time).total_seconds() >= 86400:
            self.buy_trade_count = 0
            self.sell_trade_count = 0
        
        try:
            auto_quantity = int(self.auto_quantity_entry.get())
            max_investment = float(self.max_investment_entry.get())
            
            # Calculate potential cost
            potential_cost = auto_quantity * self.current_price
            
            if trade_type == "BUY":
                # Check if we have enough cash and if the investment is within limits
                if potential_cost > self.portfolio['cash_balance']:
                    print(f"Auto Trade: Not enough cash for {auto_quantity} shares of {self.current_stock}")
                    return
                    
                if potential_cost > max_investment:
                    print(f"Auto Trade: Cost exceeds max investment limit (${potential_cost:.2f} > ${max_investment:.2f})")
                    return
                
                # Check if buy limit is reached
                if self.buy_trade_count >= 10:
                    print("Auto Trade: Buy limit reached for the day.")
                    return
                
                # Execute buy
                self.execute_auto_buy(auto_quantity)
                self.buy_trade_count += 1
                
            elif trade_type == "SELL":
                # Check if we own the stock
                if self.current_stock not in self.portfolio['stocks']:
                    print(f"Auto Trade: You don't own any shares of {self.current_stock}")
                    return
                    
                # Get owned shares
                owned_shares = self.portfolio['stocks'][self.current_stock]['shares']
                
                # Adjust quantity if needed
                sell_quantity = min(auto_quantity, owned_shares)
                
                if sell_quantity <= 0:
                    return
                
                # Check if sell limit is reached
                if self.sell_trade_count >= 10:
                    print("Auto Trade: Sell limit reached for the day.")
                    return
                
                # Execute sell
                self.execute_auto_sell(sell_quantity)
                self.sell_trade_count += 1
                
            # Update last trade time
            self.last_trade_time = datetime.now()
            
        except ValueError:
            print("Auto Trade: Invalid quantity or max investment values")

    def execute_auto_buy(self, quantity):
        """Execute an automatic buy trade"""
        total_cost = quantity * self.current_price
        
        # Update portfolio
        if self.current_stock in self.portfolio['stocks']:
            # Update existing position
            current_shares = self.portfolio['stocks'][self.current_stock]['shares']
            current_avg_price = self.portfolio['stocks'][self.current_stock]['avg_price']
            
            # Calculate new average price
            new_shares = current_shares + quantity
            new_avg_price = ((current_shares * current_avg_price) + total_cost) / new_shares
            
            self.portfolio['stocks'][self.current_stock]['shares'] = new_shares
            self.portfolio['stocks'][self.current_stock]['avg_price'] = new_avg_price
        else:
            # Add new position
            self.portfolio['stocks'][self.current_stock] = {
                'shares': quantity,
                'avg_price': self.current_price
            }
        
        # Deduct cash
        self.portfolio['cash_balance'] -= total_cost
        
        # Add transaction to history
        transaction = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'AUTO BUY',
            'symbol': self.current_stock,
            'shares': quantity,
            'price': self.current_price,
            'total': total_cost,
            'commission': 0.0
        }
        self.portfolio['transaction_history'].append(transaction)
        
        # Save portfolio
        self.save_portfolio()
        
        # Update displays
        self.update_portfolio_display()
        self.balance_label.config(text=f"Cash Balance: ${self.portfolio['cash_balance']:.2f}")
        
        # Log the auto trade
        print(f"Auto Trade: Bought {quantity} shares of {self.current_stock} for ${total_cost:.2f}")
        
        # Show notification
        self.show_auto_trade_notification("BUY", quantity, total_cost)

    def execute_auto_sell(self, quantity):
        """Execute an automatic sell trade"""
        total_value = quantity * self.current_price
        
        # Update portfolio
        if quantity == self.portfolio['stocks'][self.current_stock]['shares']:
            # Remove the stock if selling all shares
            del self.portfolio['stocks'][self.current_stock]
        else:
            # Update shares count
            self.portfolio['stocks'][self.current_stock]['shares'] -= quantity
        
        # Add cash
        self.portfolio['cash_balance'] += total_value
        
        # Add transaction to history
        transaction = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'AUTO SELL',
            'symbol': self.current_stock,
            'shares': quantity,
            'price': self.current_price,
            'total': total_value,
            'commission': 0.0
        }
        self.portfolio['transaction_history'].append(transaction)
        
        # Save portfolio
        self.save_portfolio()
        
        # Update displays
        self.update_portfolio_display()
        self.balance_label.config(text=f"Cash Balance: ${self.portfolio['cash_balance']:.2f}")
        
        # Log the auto trade
        print(f"Auto Trade: Sold {quantity} shares of {self.current_stock} for ${total_value:.2f}")
        
        # Show notification
        self.show_auto_trade_notification("SELL", quantity, total_value)

    def show_auto_trade_notification(self, trade_type, quantity, amount):
        """Show a notification for an auto trade"""
        # Create a popup that automatically closes after a few seconds
        notification = tk.Toplevel(self.root)
        notification.title("Auto Trade Executed")
        notification.geometry("300x150")
        notification.attributes("-topmost", True)
        
        # Add notification content
        if trade_type == "BUY":
            message = f"Auto Trading Bot purchased {quantity} shares of {self.current_stock} for ${amount:.2f}"
            color = "green"
        else:
            message = f"Auto Trading Bot sold {quantity} shares of {self.current_stock} for ${amount:.2f}"
            color = "red"
        
        ttk.Label(notification, text="Auto Trade Executed", font=("Helvetica", 12, "bold")).pack(pady=10)
        ttk.Label(notification, text=message, foreground=color).pack(pady=10)
        ttk.Label(notification, text=datetime.now().strftime("%Y-%m-%d %H:%M:%S")).pack(pady=5)
        
        # Auto close after 5 seconds
        notification.after(5000, notification.destroy)

    def search_stock(self):
        """Search for the stock and update the stock information"""
        stock_symbol = self.symbol_entry.get().strip().upper()
        
        if not stock_symbol:
            messagebox.showerror("Error", "Please enter a stock symbol.")
            return
        
        try:
            stock = yf.Ticker(stock_symbol)
            self.current_stock = stock_symbol
            self.current_price = stock.info['regularMarketPrice']
            
            # Update stock information labels
            self.stock_name_label.config(text=f"Stock: {self.current_stock}")
            self.stock_price_label.config(text=f"Current Price: ${self.current_price:.2f}")
            
            # Update the chart with the latest data
            self.update_chart()
            
            # Update total cost based on the current price
            self.update_total_cost(None)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not retrieve data for {stock_symbol}. Please check the symbol and try again.")
            print(f"Error fetching stock data: {e}")

    def update_chart(self):
        """Update the candlestick chart with current stock data"""
        if not self.current_stock:
            return
        
        try:
            # Get historical data for the last 90 days
            stock = yf.Ticker(self.current_stock)
            hist_data = stock.history(period="90d")
            
            if hist_data.empty:
                self.stock_price_label.config(text="Current Price: N/A")
                return
            
            # Clear the previous chart
            self.ax.clear()
            
            # Prepare data for candlestick chart
            hist_data['Date'] = hist_data.index
            hist_data['Date'] = mdates.date2num(hist_data['Date'])  # Convert dates to matplotlib format
            
            # Create a DataFrame for mplfinance
            ohlc_data = hist_data[['Date', 'Open', 'High', 'Low', 'Close']]
            ohlc_data.columns = ['Date', 'Open', 'High', 'Low', 'Close']
            
            # Plot candlestick chart using mplfinance
            mpf.plot(ohlc_data, type='candle', ax=self.ax, style='charles', title=f"{self.current_stock} Price Chart", ylabel='Price ($)')
            
            # Format x-axis
            self.ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
            self.ax.xaxis.set_major_locator(DayLocator(interval=10))
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add gridlines
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            # Adjust layout
            self.fig.tight_layout()
            
            # Update the canvas
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating chart: {e}")

    def reset_account(self):
        """Reset the portfolio to its initial state"""
        self.portfolio = {
            "cash_balance": self.initial_balance,  # Reset to initial balance
            "stocks": {},
            "transaction_history": []
        }
        self.save_portfolio()
        self.update_portfolio_display()
        messagebox.showinfo("Account Reset", "Your account has been reset to the initial state.")

    def buy_stock(self):
        """Execute a buy order for the current stock"""
        if not self.current_stock:
            messagebox.showerror("Error", "No stock selected.")
            return
        
        try:
            quantity = int(self.quantity_entry.get())
            total_cost = quantity * self.current_price
            
            # Check if user has enough cash
            if total_cost > self.portfolio['cash_balance']:
                messagebox.showerror("Error", "Not enough cash for this purchase")
                return
            
            # Update portfolio
            if self.current_stock in self.portfolio['stocks']:
                # Update existing position
                current_shares = self.portfolio['stocks'][self.current_stock]['shares']
                current_avg_price = self.portfolio['stocks'][self.current_stock]['avg_price']
                
                # Calculate new average price
                new_shares = current_shares + quantity
                new_avg_price = ((current_shares * current_avg_price) + total_cost) / new_shares
                
                self.portfolio['stocks'][self.current_stock]['shares'] = new_shares
                self.portfolio['stocks'][self.current_stock]['avg_price'] = new_avg_price
            else:
                # Add new position
                self.portfolio['stocks'][self.current_stock] = {
                    'shares': quantity,
                    'avg_price': self.current_price
                }
            
            # Deduct cash
            self.portfolio['cash_balance'] -= total_cost
            
            # Add transaction to history
            transaction = {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'BUY',
                'symbol': self.current_stock,
                'shares': quantity,
                'price': self.current_price,
                'total': total_cost
            }
            self.portfolio['transaction_history'].append(transaction)
            
            # Save portfolio
            self.save_portfolio()
            
            # Update displays
            self.update_portfolio_display()
            self.balance_label.config(text=f"Cash Balance: ${self.portfolio['cash_balance']:.2f}")
            
            # Log the trade
            print(f"Bought {quantity} shares of {self.current_stock} for ${total_cost:.2f}")
            
            # Show notification
            messagebox.showinfo("Success", f"Bought {quantity} shares of {self.current_stock} for ${total_cost:.2f}")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity.")

    def sell_stock(self):
        """Execute a sell order for the current stock"""
        if not self.current_stock:
            messagebox.showerror("Error", "No stock selected.")
            return
        
        try:
            quantity = int(self.quantity_entry.get())
            
            # Check if the stock is in the portfolio
            if self.current_stock not in self.portfolio['stocks']:
                messagebox.showerror("Error", "You do not own any shares of this stock.")
                return
            
            current_shares = self.portfolio['stocks'][self.current_stock]['shares']
            
            # Check if user has enough shares to sell
            if quantity > current_shares:
                messagebox.showerror("Error", "Not enough shares to sell.")
                return
            
            total_value = quantity * self.current_price
            
            # Update portfolio
            if quantity == current_shares:
                # Remove the stock if selling all shares
                del self.portfolio['stocks'][self.current_stock]
            else:
                # Update shares count
                self.portfolio['stocks'][self.current_stock]['shares'] -= quantity
            
            # Add cash
            self.portfolio['cash_balance'] += total_value
            
            # Add transaction to history
            transaction = {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'type': 'SELL',
                'symbol': self.current_stock,
                'shares': quantity,
                'price': self.current_price,
                'total': total_value
            }
            self.portfolio['transaction_history'].append(transaction)
            
            # Save portfolio
            self.save_portfolio()
            
            # Update displays
            self.update_portfolio_display()
            self.balance_label.config(text=f"Cash Balance: ${self.portfolio['cash_balance']:.2f}")
            
            # Log the trade
            print(f"Sold {quantity} shares of {self.current_stock} for ${total_value:.2f}")
            
            # Show notification
            messagebox.showinfo("Success", f"Sold {quantity} shares of {self.current_stock} for ${total_value:.2f}")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity.")

    def setup_chart(self):
        """Set up the candlestick chart for displaying stock prices"""
        self.fig = Figure(figsize=(10, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Create a canvas to display the figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial empty chart
        self.ax.set_title("Price Chart")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Price ($)")
        self.ax.grid(True)

    def update_portfolio_display(self):
        """Update the portfolio display with current data"""
        # Update cash balance label
        self.balance_label.config(text=f"Cash Balance: ${self.portfolio['cash_balance']:.2f}")
        
        # Clear the portfolio tree
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)
        
        # Populate the portfolio tree with current stocks
        for symbol, data in self.portfolio['stocks'].items():
            shares = data['shares']
            avg_price = data['avg_price']
            current_price = self.get_current_price(symbol)  # You may need to implement this method
            value = shares * current_price
            gain_loss = value - (shares * avg_price)
            
            self.portfolio_tree.insert("", "end", values=(symbol, shares, f"${avg_price:.2f}", f"${current_price:.2f}", f"${value:.2f}", f"${gain_loss:.2f}"))
        
        # Clear the transaction history tree
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Populate the transaction history tree
        for transaction in self.portfolio['transaction_history']:
            self.history_tree.insert("", "end", values=(transaction['date'], transaction['type'], transaction['symbol'], transaction['shares'], f"${transaction['price']:.2f}", f"${transaction['total']:.2f}"))

    def get_current_price(self, symbol):
        """Get the current price of the stock"""
        try:
            stock = yf.Ticker(symbol)
            return stock.info['regularMarketPrice']
        except Exception as e:
            print(f"Error fetching current price for {symbol}: {e}")
            return 0.0

    def update_stock_prices(self):
        """Update the current prices of stocks in the portfolio"""
        for symbol in self.portfolio['stocks']:
            try:
                stock = yf.Ticker(symbol)
                current_price = stock.info['regularMarketPrice']
                self.portfolio['stocks'][symbol]['current_price'] = current_price
            except Exception as e:
                print(f"Error fetching price for {symbol}: {e}")
        
        # Update the portfolio display to reflect the new prices
        self.update_portfolio_display()
        
        # Schedule the next update
        self.root.after(60000, self.update_stock_prices)  # Update every 60 seconds

if __name__ == "__main__":
    # Create main window
    root = tk.Tk()
    app = FakeStockTradingApp(root)
    root.mainloop()
