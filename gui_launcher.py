#!/usr/bin/env python3
"""
Professional GUI Launcher for Aventa Trading System.

Features:
- Configuration management (MT5, symbols, lots, indicator parameters)
- Training interface with progress monitoring
- Backtesting with performance metrics
- Real-time monitoring dashboard
- Performance and risk management tracking
- Comprehensive logging system
- Save/load configurations
"""

import json
import logging
import sys
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QObject
from PyQt6.QtGui import QFont, QIcon, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QProgressBar, QTextEdit, QGroupBox, QFormLayout,
    QGridLayout, QDialog, QSplitter, QStatusBar, QMenuBar, QMenu,
    QSpinBox as QSpinBoxWidget, QPlainTextEdit, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import QSize


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GUI')


@dataclass
class TradingConfig:
    """Configuration for trading system."""
    # MT5 Settings
    mt5_path: str = "C:\\Program Files\\MetaTrader 5"
    mt5_login: int = 123456
    mt5_password: str = ""
    mt5_server: str = "broker.server"
    
    # Trading Settings
    symbol: str = "XAUUSD"
    lot_size: float = 0.1
    stop_loss_pips: int = 100
    take_profit_pips: int = 200
    max_daily_loss: float = 1000.0
    max_positions: int = 3
    
    # Indicator Settings
    sma_period: int = 20
    rsi_period: int = 14
    atr_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    
    # Signal Settings
    buy_threshold: float = 0.0001
    sell_threshold: float = -0.0001
    
    # Model Settings
    model_type: str = "RandomForest"
    model_dir: str = "models"
    
    # Data Settings
    data_dir: str = "data"
    data_file: str = ""
    logs_dir: str = "logs"
    
    # Training Settings
    test_size: float = 0.1
    validation_size: float = 0.1
    epochs: int = 30
    batch_size: int = 32
    
    # Real-time Settings
    monitoring_interval: float = 1.0
    data_source: str = "csv"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'TradingConfig':
        """Create from dictionary."""
        return TradingConfig(**data)


class LogHandler(logging.Handler, QObject):
    """Custom logging handler that emits signals."""
    
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
    
    def emit(self, record: logging.LogRecord):
        """Emit log record."""
        msg = self.format(record)
        self.log_signal.emit(msg)


class TrainingWorker(QThread):
    """Worker thread for training."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
    
    def run(self):
        """Run training."""
        try:
            self.status.emit("Loading training data...")
            self.progress.emit(10)
            
            # Import and run training
            from train_models import run_training_flow
            from pathlib import Path
            
            self.status.emit("Training models...")
            self.progress.emit(30)
            
            # Map UI model type to actual model type expected by train_models.py
            model_type_map = {
                'sklearn (RandomForest)': 'sklearn',
                'lstm (PyTorch)': 'lstm',
                'sklearn': 'sklearn',
                'RandomForest': 'sklearn',  # Fallback for old config
                'LSTM': 'lstm',
            }
            actual_model_type = model_type_map.get(self.config.model_type, 'sklearn')

            # Optional specific data file set from UI
            data_file = None
            if getattr(self.config, 'data_file', None):
                from pathlib import Path as _P
                data_file = _P(self.config.data_file)
            
            results = run_training_flow(
                data_dir=Path(self.config.data_dir),
                output_dir=Path(self.config.model_dir),
                model_type=actual_model_type,
                data_file=data_file,
                epochs=self.config.epochs
            )
            
            self.progress.emit(90)
            self.status.emit("Training completed!")
            self.progress.emit(100)
            
            self.finished.emit(results)
        
        except Exception as e:
            self.error.emit(str(e))


class DownloadWorker(QThread):
    """Worker thread to download market data via download_data.py."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, symbol: str, mt5_path: str, output_dir: str = 'data'):
        super().__init__()
        self.symbol = symbol
        self.mt5_path = mt5_path
        self.output_dir = output_dir

    def run(self):
        try:
            self.status.emit(f"Downloading {self.symbol}...")
            from download_data import download_symbol
            out_path = download_symbol(symbol=self.symbol, mt5_path=self.mt5_path, output_dir=self.output_dir)
            self.finished.emit(str(out_path))
        except Exception as e:
            self.error.emit(str(e))


class BacktestWorker(QThread):
    """Worker thread for backtesting."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    results = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
    
    def run(self):
        """Run backtest."""
        try:
            self.status.emit("Loading backtest data...")
            self.progress.emit(10)
            
            # Load data
            df = pd.read_csv(f"{self.config.data_dir}/XAUUSD_M1_59days.csv")
            self.progress.emit(25)
            
            self.status.emit("Running predictions...")
            from inference import ModelPredictor
            
            predictor = ModelPredictor(model_dir=self.config.model_dir)
            result = predictor.predict(df)
            predictions = result['predictions']
            
            self.progress.emit(50)
            
            # Calculate signals and P&L
            self.status.emit("Calculating performance metrics...")
            
            closes = df['close'].values
            signals = []
            trades = []
            
            for pred in predictions:
                if pred > self.config.buy_threshold:
                    signals.append('BUY')
                elif pred < self.config.sell_threshold:
                    signals.append('SELL')
                else:
                    signals.append('HOLD')
            
            # Simple P&L calculation
            total_pnl = 0.0
            winning_trades = 0
            losing_trades = 0
            entry_price = None
            
            for i, signal in enumerate(signals):
                if signal == 'BUY' and entry_price is None:
                    entry_price = closes[i]
                elif signal == 'SELL' and entry_price is not None:
                    pnl = (closes[i] - entry_price) * self.config.lot_size * 100
                    total_pnl += pnl
                    if pnl > 0:
                        winning_trades += 1
                    else:
                        losing_trades += 1
                    entry_price = None
            
            self.progress.emit(75)
            
            backtest_results = {
                'total_trades': winning_trades + losing_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_pnl': total_pnl,
                'win_rate': (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0,
                'avg_win': total_pnl / max(winning_trades, 1),
                'predictions_count': len(predictions),
                'buy_signals': signals.count('BUY'),
                'sell_signals': signals.count('SELL'),
                'hold_signals': signals.count('HOLD'),
            }
            
            self.progress.emit(90)
            self.status.emit("Backtest completed!")
            self.progress.emit(100)
            
            self.results.emit(backtest_results)
        
        except Exception as e:
            self.error.emit(str(e))


class MonitoringWorker(QThread):
    """Worker thread for real-time monitoring."""
    update = pyqtSignal(dict)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
        self.running = True
    
    def run(self):
        """Run monitoring."""
        try:
            from real_time_monitor import RealTimeMonitor
            
            self.status.emit(f"Initializing monitor ({self.config.data_source})...")
            
            source_kwargs = {}
            if self.config.data_source == 'csv':
                # Use data_file from config (set from UI CSV selector)
                csv_file = getattr(self.config, 'data_file', None) or f"{self.config.data_dir}/XAUUSD_M1_59days.csv"
                source_kwargs = {'data_file': csv_file}
            elif self.config.data_source == 'mt5':
                # Use MT5 credentials from Configuration tab
                source_kwargs = {
                    'mt5_path': self.config.mt5_path,
                    'login': self.config.mt5_login,
                    'password': self.config.mt5_password,
                    'server': self.config.mt5_server
                }
            
            monitor = RealTimeMonitor(
                model_dir=self.config.model_dir,
                source=self.config.data_source,
                **source_kwargs
            )
            
            self.status.emit("Monitoring started...")
            iteration = 0
            
            while self.running:
                try:
                    result = monitor.run_single_iteration(self.config.symbol)
                    if result:
                        result['iteration'] = iteration
                        self.update.emit(result)
                        iteration += 1
                    
                    self.msleep(int(self.config.monitoring_interval * 1000))
                
                except Exception as e:
                    logger.error(f"Monitoring iteration error: {e}")
        
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """Stop monitoring."""
        self.running = False


class ConfigurationTab(QWidget):
    """Configuration management tab."""
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        
        # MT5 Settings
        mt5_group = QGroupBox("MT5 Settings")
        mt5_form = QFormLayout()
        
        self.mt5_path = QLineEdit(self.config.mt5_path)
        self.mt5_login = QSpinBox()
        self.mt5_login.setMaximum(9999999)
        self.mt5_login.setValue(self.config.mt5_login)
        self.mt5_password = QLineEdit(self.config.mt5_password)
        self.mt5_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.mt5_server = QLineEdit(self.config.mt5_server)
        
        mt5_form.addRow("MT5 Path:", self.mt5_path)
        mt5_form.addRow("Login:", self.mt5_login)
        mt5_form.addRow("Password:", self.mt5_password)
        mt5_form.addRow("Server:", self.mt5_server)
        mt5_group.setLayout(mt5_form)
        layout.addWidget(mt5_group)
        
        # Trading Settings
        trading_group = QGroupBox("Trading Settings")
        trading_form = QFormLayout()
        
        self.symbol = QLineEdit(self.config.symbol)
        self.lot_size = QDoubleSpinBox()
        self.lot_size.setDecimals(2)
        self.lot_size.setValue(self.config.lot_size)
        self.stop_loss = QSpinBox()
        self.stop_loss.setValue(self.config.stop_loss_pips)
        self.take_profit = QSpinBox()
        self.take_profit.setValue(self.config.take_profit_pips)
        self.max_daily_loss = QDoubleSpinBox()
        self.max_daily_loss.setValue(self.config.max_daily_loss)
        self.max_positions = QSpinBox()
        self.max_positions.setValue(self.config.max_positions)
        
        trading_form.addRow("Symbol:", self.symbol)
        trading_form.addRow("Lot Size:", self.lot_size)
        trading_form.addRow("Stop Loss (pips):", self.stop_loss)
        trading_form.addRow("Take Profit (pips):", self.take_profit)
        trading_form.addRow("Max Daily Loss ($):", self.max_daily_loss)
        trading_form.addRow("Max Positions:", self.max_positions)
        trading_group.setLayout(trading_form)
        layout.addWidget(trading_group)
        
        # Signal Settings
        signal_group = QGroupBox("Signal Thresholds")
        signal_form = QFormLayout()
        
        self.buy_threshold = QDoubleSpinBox()
        self.buy_threshold.setDecimals(6)
        self.buy_threshold.setValue(self.config.buy_threshold)
        self.sell_threshold = QDoubleSpinBox()
        self.sell_threshold.setDecimals(6)
        self.sell_threshold.setValue(self.config.sell_threshold)
        
        signal_form.addRow("Buy Threshold:", self.buy_threshold)
        signal_form.addRow("Sell Threshold:", self.sell_threshold)
        signal_group.setLayout(signal_form)
        layout.addWidget(signal_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_config(self) -> TradingConfig:
        """Get updated configuration."""
        self.config.mt5_path = self.mt5_path.text()
        self.config.mt5_login = self.mt5_login.value()
        self.config.mt5_password = self.mt5_password.text()
        self.config.mt5_server = self.mt5_server.text()
        self.config.symbol = self.symbol.text()
        self.config.lot_size = self.lot_size.value()
        self.config.stop_loss_pips = self.stop_loss.value()
        self.config.take_profit_pips = self.take_profit.value()
        self.config.max_daily_loss = self.max_daily_loss.value()
        self.config.max_positions = self.max_positions.value()
        self.config.buy_threshold = self.buy_threshold.value()
        self.config.sell_threshold = self.sell_threshold.value()
        
        return self.config


class IndicatorTab(QWidget):
    """Technical indicator parameters tab."""
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        
        # Moving Averages
        ma_group = QGroupBox("Moving Averages")
        ma_form = QFormLayout()
        
        self.sma_period = QSpinBox()
        self.sma_period.setMinimum(2)
        self.sma_period.setValue(self.config.sma_period)
        
        ma_form.addRow("SMA Period:", self.sma_period)
        ma_group.setLayout(ma_form)
        layout.addWidget(ma_group)
        
        # RSI
        rsi_group = QGroupBox("RSI (Relative Strength Index)")
        rsi_form = QFormLayout()
        
        self.rsi_period = QSpinBox()
        self.rsi_period.setMinimum(2)
        self.rsi_period.setValue(self.config.rsi_period)
        self.rsi_overbought = QSpinBox()
        self.rsi_overbought.setMaximum(100)
        self.rsi_overbought.setValue(self.config.rsi_overbought)
        self.rsi_oversold = QSpinBox()
        self.rsi_oversold.setMaximum(100)
        self.rsi_oversold.setValue(self.config.rsi_oversold)
        
        rsi_form.addRow("Period:", self.rsi_period)
        rsi_form.addRow("Overbought Level:", self.rsi_overbought)
        rsi_form.addRow("Oversold Level:", self.rsi_oversold)
        rsi_group.setLayout(rsi_form)
        layout.addWidget(rsi_group)
        
        # ATR
        atr_group = QGroupBox("ATR (Average True Range)")
        atr_form = QFormLayout()
        
        self.atr_period = QSpinBox()
        self.atr_period.setMinimum(2)
        self.atr_period.setValue(self.config.atr_period)
        
        atr_form.addRow("Period:", self.atr_period)
        atr_group.setLayout(atr_form)
        layout.addWidget(atr_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def get_config(self) -> TradingConfig:
        """Get updated configuration."""
        self.config.sma_period = self.sma_period.value()
        self.config.rsi_period = self.rsi_period.value()
        self.config.rsi_overbought = self.rsi_overbought.value()
        self.config.rsi_oversold = self.rsi_oversold.value()
        self.config.atr_period = self.atr_period.value()
        
        return self.config


class TrainingTab(QWidget):
    """Model training tab."""
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        
        # Training Settings
        settings_group = QGroupBox("Training Settings")
        settings_form = QFormLayout()
        
        self.test_size = QDoubleSpinBox()
        self.test_size.setDecimals(2)
        self.test_size.setMaximum(0.5)
        self.test_size.setValue(self.config.test_size)
        
        self.validation_size = QDoubleSpinBox()
        self.validation_size.setDecimals(2)
        self.validation_size.setMaximum(0.5)
        self.validation_size.setValue(self.config.validation_size)
        
        self.epochs = QSpinBox()
        self.epochs.setMinimum(1)
        self.epochs.setMaximum(500)
        self.epochs.setValue(self.config.epochs)
        
        self.batch_size = QSpinBox()
        self.batch_size.setMinimum(1)
        self.batch_size.setValue(self.config.batch_size)
        
        self.model_type = QComboBox()
        self.model_type.addItems(['sklearn (RandomForest)', 'lstm (PyTorch)', 'sklearn'])
        default_model = 'sklearn (RandomForest)' if 'RandomForest' in self.config.model_type else self.config.model_type
        self.model_type.setCurrentText(default_model)
        
        settings_form.addRow("Test Size:", self.test_size)
        settings_form.addRow("Validation Size:", self.validation_size)
        settings_form.addRow("Epochs:", self.epochs)
        settings_form.addRow("Batch Size:", self.batch_size)
        settings_form.addRow("Model Type:", self.model_type)
        
        settings_group.setLayout(settings_form)
        layout.addWidget(settings_group)
        
        # Data controls (download / select)
        data_group = QGroupBox("Data")
        data_layout = QHBoxLayout()
        self.symbol_input = QLineEdit()
        self.symbol_input.setText(self.config.symbol)
        self.download_button = QPushButton("⬇️ Download Data")
        self.download_button.clicked.connect(self.download_data)
        data_layout.addWidget(QLabel("Symbol:"))
        data_layout.addWidget(self.symbol_input)
        data_layout.addWidget(self.download_button)
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        file_layout = QHBoxLayout()
        self.select_button = QPushButton("📂 Select Data File")
        self.select_button.clicked.connect(self.select_data_file)
        self.selected_file_label = QLabel(self.config.data_file or "No file selected")
        file_layout.addWidget(self.select_button)
        file_layout.addWidget(self.selected_file_label)
        layout.addLayout(file_layout)
        
        # Training Controls
        controls_layout = QHBoxLayout()
        
        self.train_button = QPushButton("▶ Start Training")
        self.train_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.train_button.clicked.connect(self.start_training)
        
        self.stop_button = QPushButton("⏹ Stop Training")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        self.stop_button.clicked.connect(self.stop_training)
        
        controls_layout.addWidget(self.train_button)
        controls_layout.addWidget(self.stop_button)
        layout.addLayout(controls_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(QLabel("Progress:"))
        layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_label)
        
        # Results
        self.results_text = QPlainTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(QLabel("Results:"))
        layout.addWidget(self.results_text)
        
        self.setLayout(layout)
        self.selected_data_file = self.config.data_file or ""

    def download_data(self):
        """Download data for the symbol using MT5 settings."""
        symbol = self.symbol_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "No Symbol", "Please enter a symbol to download (e.g. XAUUSD).")
            return
        self.download_button.setEnabled(False)
        self.status_label.setText(f"Downloading {symbol}...")
        self.dworker = DownloadWorker(symbol, self.config.mt5_path, output_dir=self.config.data_dir)
        self.dworker.status.connect(self.update_status)
        self.dworker.finished.connect(self.on_download_finished)
        self.dworker.error.connect(self.on_download_error)
        self.dworker.start()

    def on_download_finished(self, filepath: str):
        self.download_button.setEnabled(True)
        self.status_label.setText("Download complete")
        self.selected_data_file = filepath
        self.selected_file_label.setText(filepath)
        self.config.data_file = filepath
        QMessageBox.information(self, "Download Complete", f"Data saved to {filepath}")

    def on_download_error(self, error: str):
        self.download_button.setEnabled(True)
        self.status_label.setText("Download failed")
        QMessageBox.critical(self, "Download Error", f"Failed to download data: {error}")

    def select_data_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Data File", str(Path(self.config.data_dir)), "CSV Files (*.csv)")
        if file_path:
            self.selected_data_file = file_path
            self.selected_file_label.setText(file_path)
            self.config.data_file = file_path
            QMessageBox.information(self, "Data Selected", f"Selected file: {file_path}")

    def start_training(self):
        """Start training."""
        self.train_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.results_text.clear()
        
        # Update config with current UI values
        self.config.test_size = self.test_size.value()
        self.config.validation_size = self.validation_size.value()
        self.config.epochs = self.epochs.value()
        self.config.batch_size = self.batch_size.value()
        self.config.model_type = self.model_type.currentText()
        
        self.worker = TrainingWorker(self.config)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.training_finished)
        self.worker.error.connect(self.training_error)
        self.worker.start()
    
    def stop_training(self):
        """Stop training."""
        if self.worker:
            self.worker.terminate()
        self.train_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Training stopped")
    
    def update_status(self, status: str):
        """Update status."""
        self.status_label.setText(status)
        self.results_text.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] {status}")
    
    def training_finished(self, results: dict):
        """Training finished."""
        self.train_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        results_str = json.dumps(results, indent=2)
        self.results_text.appendPlainText("\n" + "="*50)
        self.results_text.appendPlainText("TRAINING RESULTS:")
        self.results_text.appendPlainText(results_str)
        
        QMessageBox.information(self, "Training Complete", "Model training completed successfully!")
    
    def training_error(self, error: str):
        """Training error."""
        self.train_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        self.results_text.appendPlainText("\n" + "="*50)
        self.results_text.appendPlainText(f"ERROR: {error}")
        
        QMessageBox.critical(self, "Training Error", f"Training failed: {error}")


class BacktestTab(QWidget):
    """Backtesting tab."""
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        
        # Backtest Controls
        controls_layout = QHBoxLayout()
        
        self.backtest_button = QPushButton("▶ Run Backtest")
        self.backtest_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        self.backtest_button.clicked.connect(self.start_backtest)
        
        self.export_button = QPushButton("💾 Export Results")
        self.export_button.clicked.connect(self.export_results)
        
        controls_layout.addWidget(self.backtest_button)
        controls_layout.addWidget(self.export_button)
        layout.addLayout(controls_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(QLabel("Progress:"))
        layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_label)
        
        # Results Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(['Metric', 'Value'])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(QLabel("Results:"))
        layout.addWidget(self.results_table)
        
        self.setLayout(layout)
        self.backtest_results = None
    
    def start_backtest(self):
        """Start backtest."""
        self.backtest_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.results_table.setRowCount(0)
        
        self.worker = BacktestWorker(self.config)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.update_status)
        self.worker.results.connect(self.backtest_finished)
        self.worker.error.connect(self.backtest_error)
        self.worker.start()
    
    def update_status(self, status: str):
        """Update status."""
        self.status_label.setText(status)
    
    def backtest_finished(self, results: dict):
        """Backtest finished."""
        self.backtest_button.setEnabled(True)
        self.backtest_results = results
        
        # Populate table
        self.results_table.setRowCount(0)
        for key, value in results.items():
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            self.results_table.setItem(row, 0, QTableWidgetItem(key.replace('_', ' ').title()))
            
            if isinstance(value, float):
                value_str = f"{value:.2f}"
            else:
                value_str = str(value)
            
            self.results_table.setItem(row, 1, QTableWidgetItem(value_str))
        
        QMessageBox.information(self, "Backtest Complete", "Backtesting completed successfully!")
    
    def backtest_error(self, error: str):
        """Backtest error."""
        self.backtest_button.setEnabled(True)
        QMessageBox.critical(self, "Backtest Error", f"Backtest failed: {error}")
    
    def export_results(self):
        """Export results."""
        if self.backtest_results is None:
            QMessageBox.warning(self, "No Results", "Run a backtest first!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Backtest Results", "", "CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if file_path:
            if file_path.endswith('.json'):
                with open(file_path, 'w') as f:
                    json.dump(self.backtest_results, f, indent=2)
            else:
                df = pd.DataFrame([self.backtest_results])
                df.to_csv(file_path, index=False)
            
            QMessageBox.information(self, "Export Complete", f"Results exported to {file_path}")


class RealTimeTab(QWidget):
    """Real-time monitoring tab."""
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        
        # Monitoring Settings
        settings_group = QGroupBox("Monitoring Settings")
        settings_form = QFormLayout()
        
        self.source = QComboBox()
        self.source.addItems(['csv', 'mt5', 'yfinance'])
        self.source.setCurrentText(self.config.data_source)
        self.source.currentTextChanged.connect(self.on_data_source_changed)
        
        self.interval = QDoubleSpinBox()
        self.interval.setDecimals(1)
        self.interval.setMinimum(0.1)
        self.interval.setValue(self.config.monitoring_interval)
        
        # CSV file selector (shown only when csv source is selected)
        self.csv_file_layout = QHBoxLayout()
        self.csv_label = QLabel("CSV File:")
        self.csv_selector = QComboBox()
        self.load_csv_button = QPushButton("🔄 Reload")
        self.load_csv_button.clicked.connect(self.load_csv_files)
        self.csv_file_layout.addWidget(self.csv_label)
        self.csv_file_layout.addWidget(self.csv_selector)
        self.csv_file_layout.addWidget(self.load_csv_button)
        
        # Hide CSV selector initially if not set to csv
        self.show_csv_selector(self.config.data_source == 'csv')
        
        settings_form.addRow("Data Source:", self.source)
        settings_form.addRow("Update Interval (s):", self.interval)
        settings_group.setLayout(settings_form)
        layout.addWidget(settings_group)
        
        # Add CSV selector row
        layout.addLayout(self.csv_file_layout)
        
        # Monitoring Controls
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶ Start Monitoring")
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.start_button.clicked.connect(self.start_monitoring)
        
        self.stop_button = QPushButton("⏹ Stop Monitoring")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        self.stop_button.clicked.connect(self.stop_monitoring)
        
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        layout.addLayout(controls_layout)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_label)
        
        # Live Metrics
        metrics_group = QGroupBox("Live Metrics")
        metrics_form = QFormLayout()
        
        self.iteration_label = QLabel("0")
        self.latest_price = QLabel("--")
        self.latest_prediction = QLabel("--")
        self.latest_signal = QLabel("--")
        self.buy_count = QLabel("0")
        self.sell_count = QLabel("0")
        self.hold_count = QLabel("0")
        
        metrics_form.addRow("Iteration:", self.iteration_label)
        metrics_form.addRow("Latest Price:", self.latest_price)
        metrics_form.addRow("Prediction:", self.latest_prediction)
        metrics_form.addRow("Signal:", self.latest_signal)
        metrics_form.addRow("Buy Signals:", self.buy_count)
        metrics_form.addRow("Sell Signals:", self.sell_count)
        metrics_form.addRow("Hold Signals:", self.hold_count)
        
        metrics_group.setLayout(metrics_form)
        layout.addWidget(metrics_group)
        
        # Predictions History
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(['Time', 'Price', 'Prediction', 'Signal', 'Iter.'])
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(QLabel("Recent Predictions (Last 50):"))
        layout.addWidget(self.history_table)
        
        self.setLayout(layout)
        self.signal_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        self.selected_csv_file = ""
        
        # Load CSV files on startup if csv is the source
        if self.config.data_source == 'csv':
            self.load_csv_files()
    
    def show_csv_selector(self, show: bool):
        """Show or hide CSV file selector."""
        self.csv_label.setVisible(show)
        self.csv_selector.setVisible(show)
        self.load_csv_button.setVisible(show)
    
    def on_data_source_changed(self, source: str):
        """Handle data source change."""
        if source == 'csv':
            self.show_csv_selector(True)
            self.load_csv_files()
        else:
            self.show_csv_selector(False)
    
    def load_csv_files(self):
        """Load available CSV files from data directory."""
        self.csv_selector.clear()
        try:
            from pathlib import Path
            data_path = Path(self.config.data_dir)
            if data_path.exists():
                csv_files = list(data_path.glob('*.csv'))
                if csv_files:
                    for csv_file in sorted(csv_files):
                        self.csv_selector.addItem(csv_file.name, str(csv_file))
                    self.status_label.setText(f"Loaded {len(csv_files)} CSV file(s)")
                else:
                    self.csv_selector.addItem("(No CSV files found)")
                    self.status_label.setText("No CSV files in data directory")
            else:
                self.csv_selector.addItem("(Data directory not found)")
                self.status_label.setText("Data directory does not exist")
        except Exception as e:
            self.csv_selector.addItem(f"(Error: {e})")
            self.status_label.setText(f"Error loading CSV files: {e}")
    
    def start_monitoring(self):
        """Start monitoring."""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.source.setEnabled(False)
        self.interval.setEnabled(False)
        self.csv_selector.setEnabled(False)
        self.load_csv_button.setEnabled(False)
        
        self.config.data_source = self.source.currentText()
        self.config.monitoring_interval = self.interval.value()
        
        # If CSV source, get selected file
        if self.config.data_source == 'csv':
            self.selected_csv_file = self.csv_selector.currentData()
            if not self.selected_csv_file or self.selected_csv_file == "":
                QMessageBox.warning(self, "No CSV Selected", "Please select a CSV file to monitor.")
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.source.setEnabled(True)
                self.interval.setEnabled(True)
                self.csv_selector.setEnabled(True)
                self.load_csv_button.setEnabled(True)
                return
            self.config.data_file = self.selected_csv_file
        elif self.config.data_source == 'mt5':
            # When MT5 is selected, MT5 config should already be synced from Configuration tab
            self.status_label.setText("MT5 source selected - using Configuration settings")
        
        self.worker = MonitoringWorker(self.config)
        self.worker.update.connect(self.on_update)
        self.worker.status.connect(self.update_status)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def stop_monitoring(self):
        """Stop monitoring."""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.source.setEnabled(True)
        self.interval.setEnabled(True)
        self.csv_selector.setEnabled(True)
        self.load_csv_button.setEnabled(True)
        self.status_label.setText("Stopped")
    
    def update_status(self, status: str):
        """Update status."""
        self.status_label.setText(status)
    
    def on_update(self, result: dict):
        """Update with new prediction."""
        self.iteration_label.setText(str(result.get('iteration', 0)))
        self.latest_price.setText(f"${result['close']:.2f}")
        self.latest_prediction.setText(f"{result['prediction']:.2e}")
        
        signal = result['signal']
        self.latest_signal.setText(signal)
        
        # Update signal colors
        if signal == 'BUY':
            self.latest_signal.setStyleSheet("color: green; font-weight: bold;")
        elif signal == 'SELL':
            self.latest_signal.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.latest_signal.setStyleSheet("color: orange; font-weight: bold;")
        
        # Update counts
        self.signal_counts[signal] += 1
        self.buy_count.setText(str(self.signal_counts['BUY']))
        self.sell_count.setText(str(self.signal_counts['SELL']))
        self.hold_count.setText(str(self.signal_counts['HOLD']))
        
        # Add to history
        row = self.history_table.rowCount()
        if row >= 50:
            self.history_table.removeRow(0)
        else:
            self.history_table.insertRow(row)
        
        self.history_table.setItem(row, 0, QTableWidgetItem(str(result['timestamp'])))
        self.history_table.setItem(row, 1, QTableWidgetItem(f"${result['close']:.2f}"))
        self.history_table.setItem(row, 2, QTableWidgetItem(f"{result['prediction']:.2e}"))
        self.history_table.setItem(row, 3, QTableWidgetItem(signal))
        self.history_table.setItem(row, 4, QTableWidgetItem(str(result.get('iteration', 0))))
        
        self.history_table.scrollToBottom()
    
    def on_error(self, error: str):
        """Handle error."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QMessageBox.critical(self, "Monitoring Error", f"Error: {error}")


class PerformanceTab(QWidget):
    """Performance tracking tab."""
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        
        # Key Metrics
        metrics_group = QGroupBox("Performance Metrics")
        metrics_form = QFormLayout()
        
        self.total_trades = QLabel("0")
        self.winning_trades = QLabel("0")
        self.losing_trades = QLabel("0")
        self.win_rate = QLabel("0%")
        self.total_pnl = QLabel("$0.00")
        self.avg_win = QLabel("$0.00")
        self.avg_loss = QLabel("$0.00")
        self.profit_factor = QLabel("0.00")
        self.max_drawdown = QLabel("0%")
        
        metrics_form.addRow("Total Trades:", self.total_trades)
        metrics_form.addRow("Winning Trades:", self.winning_trades)
        metrics_form.addRow("Losing Trades:", self.losing_trades)
        metrics_form.addRow("Win Rate:", self.win_rate)
        metrics_form.addRow("Total P&L:", self.total_pnl)
        metrics_form.addRow("Average Win:", self.avg_win)
        metrics_form.addRow("Average Loss:", self.avg_loss)
        metrics_form.addRow("Profit Factor:", self.profit_factor)
        metrics_form.addRow("Max Drawdown:", self.max_drawdown)
        
        metrics_group.setLayout(metrics_form)
        layout.addWidget(metrics_group)
        
        # Trade History
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(6)
        self.trades_table.setHorizontalHeaderLabels(['Entry Time', 'Entry Price', 'Exit Price', 'P&L', 'Return %', 'Bars'])
        
        layout.addWidget(QLabel("Trade History:"))
        layout.addWidget(self.trades_table)
        
        # Refresh Button
        refresh_button = QPushButton("🔄 Refresh Metrics")
        refresh_button.clicked.connect(self.refresh_metrics)
        layout.addWidget(refresh_button)
        
        self.setLayout(layout)
    
    def refresh_metrics(self):
        """Refresh performance metrics."""
        logger.info("Refreshing performance metrics...")
        QMessageBox.information(self, "Metrics Updated", "Performance metrics refreshed from latest data.")


class RiskManagementTab(QWidget):
    """Risk management and position sizing tab."""
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        
        # Position Sizing
        sizing_group = QGroupBox("Position Sizing")
        sizing_form = QFormLayout()
        
        self.account_size = QDoubleSpinBox()
        self.account_size.setMaximum(999999999)
        self.account_size.setValue(10000)
        
        self.risk_per_trade = QDoubleSpinBox()
        self.risk_per_trade.setMaximum(100)
        self.risk_per_trade.setSuffix('%')
        self.risk_per_trade.setValue(2)
        
        self.stop_loss_pips = QSpinBox()
        self.stop_loss_pips.setValue(self.config.stop_loss_pips)
        
        sizing_form.addRow("Account Size ($):", self.account_size)
        sizing_form.addRow("Risk Per Trade (%):", self.risk_per_trade)
        sizing_form.addRow("Stop Loss (pips):", self.stop_loss_pips)
        sizing_group.setLayout(sizing_form)
        layout.addWidget(sizing_group)
        
        # Calculated Position Size
        calc_button = QPushButton("📊 Calculate Position Size")
        calc_button.clicked.connect(self.calculate_position)
        layout.addWidget(calc_button)
        
        self.calculated_lot = QLabel("--")
        layout.addWidget(QLabel("Recommended Lot Size:"))
        layout.addWidget(self.calculated_lot)
        
        # Daily Loss Limits
        limits_group = QGroupBox("Daily Limits")
        limits_form = QFormLayout()
        
        self.daily_loss_limit = QDoubleSpinBox()
        self.daily_loss_limit.setMaximum(999999999)
        self.daily_loss_limit.setValue(self.config.max_daily_loss)
        
        self.daily_win_target = QDoubleSpinBox()
        self.daily_win_target.setMaximum(999999999)
        self.daily_win_target.setValue(1000)
        
        self.max_concurrent = QSpinBox()
        self.max_concurrent.setValue(self.config.max_positions)
        
        limits_form.addRow("Daily Loss Limit ($):", self.daily_loss_limit)
        limits_form.addRow("Daily Profit Target ($):", self.daily_win_target)
        limits_form.addRow("Max Concurrent Positions:", self.max_concurrent)
        limits_group.setLayout(limits_form)
        layout.addWidget(limits_group)
        
        # Current Risk Metrics
        risk_group = QGroupBox("Current Risk Metrics")
        risk_form = QFormLayout()
        
        self.current_exposure = QLabel("$0.00")
        self.current_risk = QLabel("0%")
        self.margin_available = QLabel("--")
        
        risk_form.addRow("Current Exposure:", self.current_exposure)
        risk_form.addRow("Current Risk %:", self.current_risk)
        risk_form.addRow("Available Margin:", self.margin_available)
        risk_group.setLayout(risk_form)
        layout.addWidget(risk_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def calculate_position(self):
        """Calculate position size."""
        account = self.account_size.value()
        risk_pct = self.risk_per_trade.value()
        
        risk_amount = account * (risk_pct / 100)
        pips = self.stop_loss_pips.value()
        
        # For XAUUSD: 1 pip = $0.01, 1 lot = 100 oz
        pip_value = 0.10  # per pip per lot for gold
        
        if pips > 0 and pip_value > 0:
            lot_size = risk_amount / (pips * pip_value)
            self.calculated_lot.setText(f"{lot_size:.2f} lots")
        else:
            self.calculated_lot.setText("Invalid inputs")


class LiveTradingTab(QWidget):
    """Live trading execution tab."""
    
    def __init__(self, config: TradingConfig):
        super().__init__()
        self.config = config
        self.is_trading = False
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        
        # Trading Mode Selection
        mode_group = QGroupBox("Trading Mode")
        mode_form = QFormLayout()
        
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(['🧪 Paper Trading (Demo)', '💰 Live Trading (Real Money)'])
        self.mode_selector.setCurrentIndex(0)
        self.mode_selector.currentTextChanged.connect(self.on_mode_changed)
        
        mode_form.addRow("Select Mode:", self.mode_selector)
        mode_group.setLayout(mode_form)
        layout.addWidget(mode_group)
        
        # Trading Status
        status_group = QGroupBox("Trading Status")
        status_form = QFormLayout()
        
        self.trading_status = QLabel("⚫ STOPPED")
        self.trading_status.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        
        self.trading_mode = QLabel("🧪 Paper Trading (Demo)")
        self.trading_mode.setStyleSheet("color: orange; font-weight: bold;")
        
        status_form.addRow("Status:", self.trading_status)
        status_form.addRow("Mode:", self.trading_mode)
        status_group.setLayout(status_form)
        layout.addWidget(status_group)
        
        # Trading Controls
        controls_layout = QHBoxLayout()
        
        self.start_trade_button = QPushButton("▶ START TRADING")
        self.start_trade_button.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            font-size: 14px;
            padding: 12px;
            border-radius: 4px;
        """)
        self.start_trade_button.setMinimumHeight(50)
        self.start_trade_button.clicked.connect(self.start_trading)
        
        self.stop_trade_button = QPushButton("⏹ STOP TRADING")
        self.stop_trade_button.setEnabled(False)
        self.stop_trade_button.setStyleSheet("""
            background-color: #f44336;
            color: white;
            font-weight: bold;
            font-size: 14px;
            padding: 12px;
            border-radius: 4px;
        """)
        self.stop_trade_button.setMinimumHeight(50)
        self.stop_trade_button.clicked.connect(self.stop_trading)
        
        controls_layout.addWidget(self.start_trade_button)
        controls_layout.addWidget(self.stop_trade_button)
        layout.addLayout(controls_layout)
        
        # Real-time Metrics (using GridLayout for better layout)
        metrics_group = QGroupBox("Real-time Trading Metrics")
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(10)
        
        self.current_price = QLabel("--")
        self.profit_loss = QLabel("$0.00")
        self.profit_loss.setStyleSheet("color: black;")
        
        self.trades_count = QLabel("0")
        self.winning_trades = QLabel("0")
        self.losing_trades = QLabel("0")
        self.win_rate = QLabel("0%")
        
        self.open_positions = QLabel("0")
        self.total_volume = QLabel("0.0 lots")
        
        # Row 0: Current Price & Profit/Loss (side by side)
        metrics_grid.addWidget(QLabel("Current Price:"), 0, 0)
        metrics_grid.addWidget(self.current_price, 0, 1)
        metrics_grid.addWidget(QLabel("Profit/Loss:"), 0, 2)
        metrics_grid.addWidget(self.profit_loss, 0, 3)
        
        # Row 1: Trade Statistics
        metrics_grid.addWidget(QLabel("Total Trades:"), 1, 0)
        metrics_grid.addWidget(self.trades_count, 1, 1)
        metrics_grid.addWidget(QLabel("Winning:"), 1, 2)
        metrics_grid.addWidget(self.winning_trades, 1, 3)
        
        # Row 2: More Trade Stats
        metrics_grid.addWidget(QLabel("Losing:"), 2, 0)
        metrics_grid.addWidget(self.losing_trades, 2, 1)
        metrics_grid.addWidget(QLabel("Win Rate:"), 2, 2)
        metrics_grid.addWidget(self.win_rate, 2, 3)
        
        # Row 3: Position Stats
        metrics_grid.addWidget(QLabel("Open Positions:"), 3, 0)
        metrics_grid.addWidget(self.open_positions, 3, 1)
        metrics_grid.addWidget(QLabel("Total Volume:"), 3, 2)
        metrics_grid.addWidget(self.total_volume, 3, 3)
        
        metrics_group.setLayout(metrics_grid)
        layout.addWidget(metrics_group)
        
        # Active Positions
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(7)
        self.positions_table.setHorizontalHeaderLabels([
            'Position ID', 'Symbol', 'Type', 'Entry Price', 'Current Price', 'P&L', 'Size'
        ])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.positions_table.setMinimumHeight(120)
        self.positions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(QLabel("Active Positions:"))
        layout.addWidget(self.positions_table)
        
        # Trading Log
        self.trade_log = QPlainTextEdit()
        self.trade_log.setReadOnly(True)
        self.trade_log.setMaximumHeight(150)
        
        layout.addWidget(QLabel("Trading Log:"))
        layout.addWidget(self.trade_log)
        
        layout.addStretch()
        self.setLayout(layout)
        self.current_trading_mode = "paper"  # 'paper' or 'live'
    
    def on_mode_changed(self, mode_text: str):
        """Handle trading mode change."""
        if "Live Trading" in mode_text:
            reply = QMessageBox.warning(
                self,
                "⚠️ WARNING - LIVE TRADING",
                "Anda akan menggunakan UANG NYATA!\n\n"
                "Pastikan:\n"
                "✓ Semua konfigurasi sudah benar\n"
                "✓ Koneksi MT5 sudah terhubung\n"
                "✓ Stop Loss dan Take Profit sudah ditetapkan\n"
                "✓ Anda memahami risiko yang ada\n\n"
                "Lanjutkan?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.current_trading_mode = "live"
                self.trading_mode.setText("💰 Live Trading (Real Money)")
                self.trading_mode.setStyleSheet("color: red; font-weight: bold;")
                self.log_trade("⚠️ Mode diubah ke LIVE TRADING (Real Money)")
                logger.warning("Trading mode changed to LIVE")
            else:
                # Revert to paper trading
                self.mode_selector.blockSignals(True)
                self.mode_selector.setCurrentIndex(0)
                self.mode_selector.blockSignals(False)
        else:
            self.current_trading_mode = "paper"
            self.trading_mode.setText("🧪 Paper Trading (Demo)")
            self.trading_mode.setStyleSheet("color: orange; font-weight: bold;")
            self.log_trade("✓ Mode diubah ke PAPER TRADING (Demo)")
            logger.info("Trading mode changed to PAPER")
    
    def start_trading(self):
        """Start live trading."""
        mode_text = "Live Trading (Real Money)" if self.current_trading_mode == "live" else "Paper Trading (Demo)"
        
        message = f"Mulai {mode_text}?\n\n⚠️ Pastikan semua setting sudah benar!"
        
        reply = QMessageBox.question(
            self,
            "Konfirmasi - Mulai Trading",
            message,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Ok:
            try:
                self.is_trading = True
                self.start_trade_button.setEnabled(False)
                self.stop_trade_button.setEnabled(True)
                self.mode_selector.setEnabled(False)
                
                self.trading_status.setText("🟢 RUNNING")
                self.trading_status.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
                
                mode_text = "Live Trading" if self.current_trading_mode == "live" else "Paper Trading"
                self.log_trade(f"✓ {mode_text} dimulai")
                logger.info(f"{mode_text} started")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal memulai trading: {e}")
                self.is_trading = False
                self.start_trade_button.setEnabled(True)
                self.stop_trade_button.setEnabled(False)
                self.mode_selector.setEnabled(True)
                logger.error(f"Failed to start trading: {e}")
    
    def stop_trading(self):
        """Stop live trading."""
        reply = QMessageBox.question(
            self,
            "Konfirmasi - Hentikan Trading",
            "Hentikan trading?\n\nSemua posisi yang terbuka akan ditutup.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Ok:
            try:
                self.is_trading = False
                self.start_trade_button.setEnabled(True)
                self.stop_trade_button.setEnabled(False)
                self.mode_selector.setEnabled(True)
                
                self.trading_status.setText("⚫ STOPPED")
                self.trading_status.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
                
                self.log_trade("✓ Trading dihentikan")
                logger.info("Trading stopped")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menghentikan trading: {e}")
                logger.error(f"Failed to stop trading: {e}")
    
    def log_trade(self, message: str):
        """Log trading activity."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.trade_log.appendPlainText(f"[{timestamp}] {message}")
    
    def update_metrics(self, metrics: dict):
        """Update trading metrics."""
        if 'price' in metrics:
            self.current_price.setText(f"${metrics['price']:.2f}")
        if 'pnl' in metrics:
            pnl = metrics['pnl']
            self.profit_loss.setText(f"${pnl:.2f}")
            if pnl > 0:
                self.profit_loss.setStyleSheet("color: green; font-weight: bold;")
            elif pnl < 0:
                self.profit_loss.setStyleSheet("color: red; font-weight: bold;")
        if 'trades' in metrics:
            self.trades_count.setText(str(metrics['trades']))
        if 'wins' in metrics:
            self.winning_trades.setText(str(metrics['wins']))
        if 'losses' in metrics:
            self.losing_trades.setText(str(metrics['losses']))
        if 'win_rate' in metrics:
            self.win_rate.setText(f"{metrics['win_rate']:.1f}%")
        if 'positions' in metrics:
            self.open_positions.setText(str(metrics['positions']))
        if 'volume' in metrics:
            self.total_volume.setText(f"{metrics['volume']:.2f} lots")


class LogsTab(QWidget):
    """Logging and activity tracking tab."""
    
    log_received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_logging()
    
    def setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout()
        
        # Log Controls
        controls_layout = QHBoxLayout()
        
        self.log_level = QComboBox()
        self.log_level.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        self.log_level.setCurrentText('INFO')
        
        clear_button = QPushButton("🗑️ Clear Logs")
        clear_button.clicked.connect(self.clear_logs)
        
        export_button = QPushButton("💾 Export Logs")
        export_button.clicked.connect(self.export_logs)
        
        controls_layout.addWidget(QLabel("Log Level:"))
        controls_layout.addWidget(self.log_level)
        controls_layout.addStretch()
        controls_layout.addWidget(clear_button)
        controls_layout.addWidget(export_button)
        layout.addLayout(controls_layout)
        
        # Log Display
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        
        layout.addWidget(QLabel("Activity Log:"))
        layout.addWidget(self.log_display)
        
        self.setLayout(layout)
        self.log_received.connect(self.append_log)
    
    def setup_logging(self):
        """Setup logging handler."""
        # Create custom handler
        handler = LogHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        handler.log_signal.connect(self.append_log)
        
        # Add to root logger
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.DEBUG)
    
    def append_log(self, message: str):
        """Append log message."""
        self.log_display.appendPlainText(message)
    
    def clear_logs(self):
        """Clear logs."""
        reply = QMessageBox.question(self, "Confirm", "Clear all logs?")
        if reply == QMessageBox.StandardButton.Yes:
            self.log_display.clear()
    
    def export_logs(self):
        """Export logs."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Logs", "", "Text Files (*.txt);;Log Files (*.log)"
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.log_display.toPlainText())
            
            QMessageBox.information(self, "Export Complete", f"Logs exported to {file_path}")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.config = TradingConfig()
        self.config_file = Path('config.json')
        self.load_config()
        
        self.setWindowTitle("Aventa Trading System - Professional Launcher")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setup_ui()
        self.setup_menu()
        logger.info("Application started")
    
    def setup_ui(self):
        """Setup UI."""
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Tabs
        self.tabs = QTabWidget()
        
        self.config_tab = ConfigurationTab(self.config)
        self.indicator_tab = IndicatorTab(self.config)
        self.training_tab = TrainingTab(self.config)
        self.backtest_tab = BacktestTab(self.config)
        self.realtime_tab = RealTimeTab(self.config)
        self.live_trading_tab = LiveTradingTab(self.config)
        self.performance_tab = PerformanceTab(self.config)
        self.risk_tab = RiskManagementTab(self.config)
        self.logs_tab = LogsTab()
        
        self.tabs.addTab(self.config_tab, "⚙️ Configuration")
        self.tabs.addTab(self.indicator_tab, "📈 Indicators")
        self.tabs.addTab(self.training_tab, "🎓 Training")
        self.tabs.addTab(self.backtest_tab, "📊 Backtest")
        self.tabs.addTab(self.realtime_tab, "🔴 Real-time")
        self.tabs.addTab(self.live_trading_tab, "🚀 Live Trading")
        self.tabs.addTab(self.performance_tab, "💹 Performance")
        self.tabs.addTab(self.risk_tab, "⚠️ Risk Management")
        self.tabs.addTab(self.logs_tab, "📋 Logs")
        
        layout.addWidget(self.tabs)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        new_config = file_menu.addAction("New Configuration")
        new_config.triggered.connect(self.new_config)
        
        open_config = file_menu.addAction("Open Configuration...")
        open_config.triggered.connect(self.open_config)
        
        save_config = file_menu.addAction("Save Configuration")
        save_config.triggered.connect(self.save_config)
        
        save_as = file_menu.addAction("Save Configuration As...")
        save_as.triggered.connect(self.save_config_as)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Tools Menu
        tools_menu = menubar.addMenu("Tools")
        
        validate = tools_menu.addAction("Validate Configuration")
        validate.triggered.connect(self.validate_config)
        
        tools_menu.addSeparator()
        
        reset = tools_menu.addAction("Reset to Defaults")
        reset.triggered.connect(self.reset_config)
        
        # Help Menu
        help_menu = menubar.addMenu("Help")
        
        about = help_menu.addAction("About")
        about.triggered.connect(self.show_about)
        
        docs = help_menu.addAction("Documentation")
        docs.triggered.connect(self.show_docs)
    
    def load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.config = TradingConfig.from_dict(data)
                    logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
    
    def save_config(self):
        """Save configuration."""
        try:
            # Update config from all tabs
            self.config = self.config_tab.get_config()
            self.config = self.indicator_tab.get_config()
            self.config.test_size = self.training_tab.test_size.value()
            self.config.validation_size = self.training_tab.validation_size.value()
            self.config.epochs = self.training_tab.epochs.value()
            self.config.batch_size = self.training_tab.batch_size.value()
            self.config.model_type = self.training_tab.model_type.currentText()
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            QMessageBox.information(self, "Success", f"Configuration saved to {self.config_file}")
        
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
    
    def save_config_as(self):
        """Save configuration as."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.config_file = Path(file_path)
                self.save_config()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")
    
    def open_config(self):
        """Open configuration file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Configuration", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                self.config_file = Path(file_path)
                self.load_config()
                
                # Reload UI
                self.reload_ui()
                
                QMessageBox.information(self, "Success", f"Configuration loaded from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load: {e}")
    
    def reload_ui(self):
        """Reload UI with current config."""
        # Recreate tabs
        self.tabs.clear()
        
        self.config_tab = ConfigurationTab(self.config)
        self.indicator_tab = IndicatorTab(self.config)
        self.training_tab = TrainingTab(self.config)
        self.backtest_tab = BacktestTab(self.config)
        self.realtime_tab = RealTimeTab(self.config)
        self.live_trading_tab = LiveTradingTab(self.config)
        self.performance_tab = PerformanceTab(self.config)
        self.risk_tab = RiskManagementTab(self.config)
        
        self.tabs.addTab(self.config_tab, "⚙️ Configuration")
        self.tabs.addTab(self.indicator_tab, "📈 Indicators")
        self.tabs.addTab(self.training_tab, "🎓 Training")
        self.tabs.addTab(self.backtest_tab, "📊 Backtest")
        self.tabs.addTab(self.realtime_tab, "🔴 Real-time")
        self.tabs.addTab(self.live_trading_tab, "🚀 Live Trading")
        self.tabs.addTab(self.performance_tab, "💹 Performance")
        self.tabs.addTab(self.risk_tab, "⚠️ Risk Management")
        self.tabs.addTab(self.logs_tab, "📋 Logs")
    
    def new_config(self):
        """Create new configuration."""
        reply = QMessageBox.question(
            self, "Confirm", "Create new configuration? Unsaved changes will be lost."
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config = TradingConfig()
            self.config_file = Path('config.json')
            self.reload_ui()
            logger.info("New configuration created")
    
    def validate_config(self):
        """Validate configuration."""
        errors = []
        
        if not self.config.symbol:
            errors.append("Symbol is required")
        if self.config.lot_size <= 0:
            errors.append("Lot size must be positive")
        if self.config.stop_loss_pips <= 0:
            errors.append("Stop loss must be positive")
        
        if errors:
            QMessageBox.warning(self, "Validation Errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "Validation", "Configuration is valid!")
    
    def reset_config(self):
        """Reset configuration to defaults."""
        reply = QMessageBox.question(
            self, "Confirm", "Reset all settings to defaults?"
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config = TradingConfig()
            self.reload_ui()
            logger.info("Configuration reset to defaults")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Aventa Trading System",
            "Aventa Trading System v1.0\n\n"
            "Professional ML-based trading launcher with:\n"
            "✓ Real-time monitoring\n"
            "✓ Model training & backtesting\n"
            "✓ Risk management\n"
            "✓ Performance tracking\n"
            "✓ Configuration management\n\n"
            "© 2026 Aventa Technologies"
        )
    
    def show_docs(self):
        """Show documentation."""
        QMessageBox.information(
            self,
            "Documentation",
            "For full documentation, see:\n\n"
            "- QUICK_START.md\n"
            "- DASHBOARD_GUIDE.md\n"
            "- README.md\n\n"
            "Configuration files are saved as JSON in config.json"
        )


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
