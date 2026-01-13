"""
Signal Service Tab for Aventa Trading System.
Manages telegram signal broadcasting to subscribers.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QPushButton, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QFormLayout,
    QPlainTextEdit, QGridLayout
)
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger('GUI')


class SignalServiceTab(QWidget):
    """Tab for managing trading signal broadcasting via Telegram."""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.broadcaster = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup tab UI with 4 sub-tabs."""
        layout = QVBoxLayout()
        
        # Sub-tab widget
        self.tabs = QTabWidget()
        
        # Sub-Tab 1: Configuration
        self.config_tab = self._create_config_tab()
        self.tabs.addTab(self.config_tab, "⚙️ Configuration")
        
        # Sub-Tab 2: Subscribers
        self.subscribers_tab = self._create_subscribers_tab()
        self.tabs.addTab(self.subscribers_tab, "👥 Subscribers")
        
        # Sub-Tab 3: Signal History
        self.history_tab = self._create_history_tab()
        self.tabs.addTab(self.history_tab, "📊 History")
        
        # Sub-Tab 4: Statistics
        self.stats_tab = self._create_stats_tab()
        self.tabs.addTab(self.stats_tab, "📈 Statistics")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    def _create_config_tab(self) -> QWidget:
        """Create Signal Configuration sub-tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Service Enable Toggle
        service_group = QGroupBox("Signal Service Control")
        service_form = QFormLayout()
        
        self.service_enabled = QCheckBox("Enable Signal Broadcasting")
        self.service_enabled.setChecked(self.config.signal_service_enabled)
        self.service_status = QLabel("🔴 OFFLINE")
        self.service_status.setStyleSheet("color: red; font-weight: bold;")
        
        service_form.addRow("Service Status:", self.service_status)
        service_form.addRow("Enable Service:", self.service_enabled)
        service_group.setLayout(service_form)
        layout.addWidget(service_group)
        
        # Bot Token Configuration
        token_group = QGroupBox("Telegram Bot Configuration")
        token_form = QFormLayout()
        
        self.bot_token = QLineEdit(self.config.signal_bot_token)
        self.bot_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.test_token_btn = QPushButton("🧪 Test Connection")
        self.test_token_btn.clicked.connect(self.test_token)
        
        token_form.addRow("Bot Token:", self.bot_token)
        token_layout = QHBoxLayout()
        token_layout.addStretch()
        token_layout.addWidget(self.test_token_btn)
        token_form.addRow("", token_layout)
        
        token_group.setLayout(token_form)
        layout.addWidget(token_group)
        
        # Signal Filters
        filter_group = QGroupBox("Signal Filters")
        filter_form = QFormLayout()
        
        self.symbols = QLineEdit(self.config.signal_symbols)
        self.symbols.setPlaceholderText("XAUUSD,EURUSD,GBPUSD")
        
        self.signal_type = QComboBox()
        self.signal_type.addItems(["ALL", "BUY", "SELL"])
        self.signal_type.setCurrentText(self.config.signal_filter_type)
        
        self.min_confidence = QDoubleSpinBox()
        self.min_confidence.setRange(0.0, 1.0)
        self.min_confidence.setDecimals(6)
        self.min_confidence.setValue(self.config.signal_min_confidence)
        
        self.max_signals_hour = QSpinBox()
        self.max_signals_hour.setRange(1, 100)
        self.max_signals_hour.setValue(self.config.max_signals_per_hour)
        
        filter_form.addRow("Symbols to Broadcast:", self.symbols)
        filter_form.addRow("Signal Filter:", self.signal_type)
        filter_form.addRow("Min ML Confidence:", self.min_confidence)
        filter_form.addRow("Max Signals/Hour:", self.max_signals_hour)
        
        filter_group.setLayout(filter_form)
        layout.addWidget(filter_group)
        
        # TP/SL Recommendations
        rr_group = QGroupBox("Risk/Reward Configuration")
        rr_form = QFormLayout()
        
        self.tp_percent = QDoubleSpinBox()
        self.tp_percent.setRange(0.1, 10.0)
        self.tp_percent.setDecimals(2)
        self.tp_percent.setSuffix(" %")
        self.tp_percent.setValue(self.config.signal_tp_percent)
        
        self.sl_percent = QDoubleSpinBox()
        self.sl_percent.setRange(0.1, 10.0)
        self.sl_percent.setDecimals(2)
        self.sl_percent.setSuffix(" %")
        self.sl_percent.setValue(self.config.signal_sl_percent)
        
        self.rr_ratio = QLabel("1.5:1")
        self.rr_ratio.setStyleSheet("font-weight: bold; color: green;")
        
        # Connect spinboxes to update RR ratio
        self.tp_percent.valueChanged.connect(self._update_rr_ratio)
        self.sl_percent.valueChanged.connect(self._update_rr_ratio)
        
        rr_form.addRow("Take Profit %:", self.tp_percent)
        rr_form.addRow("Stop Loss %:", self.sl_percent)
        rr_form.addRow("Risk/Reward Ratio:", self.rr_ratio)
        
        rr_group.setLayout(rr_form)
        layout.addWidget(rr_group)
        
        # Message Template
        template_group = QGroupBox("Signal Message Template")
        template_form = QFormLayout()
        
        self.template_type = QComboBox()
        self.template_type.addItems(["minimal", "detailed"])
        self.template_type.setCurrentText(self.config.signal_template)
        
        template_form.addRow("Template Format:", self.template_type)
        template_group.setLayout(template_form)
        layout.addWidget(template_group)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_btn = QPushButton("💾 Save Configuration")
        save_btn.clicked.connect(self.save_config)
        save_layout.addWidget(save_btn)
        layout.addLayout(save_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_subscribers_tab(self) -> QWidget:
        """Create Subscribers Management sub-tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Add subscriber section
        add_group = QGroupBox("Add Subscriber")
        add_layout = QHBoxLayout()
        
        self.chat_id_input = QLineEdit()
        self.chat_id_input.setPlaceholderText("Enter Telegram Chat ID")
        self.chat_id_input.setMaximumWidth(250)
        
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self.add_subscriber)
        
        add_layout.addWidget(QLabel("Chat ID:"))
        add_layout.addWidget(self.chat_id_input)
        add_layout.addWidget(add_btn)
        add_layout.addStretch()
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Subscribers table
        self.subscribers_table = QTableWidget()
        self.subscribers_table.setColumnCount(4)
        self.subscribers_table.setHorizontalHeaderLabels(["Chat ID", "Status", "Added Date", "Action"])
        self.subscribers_table.setMaximumHeight(300)
        
        layout.addWidget(QLabel("Active Subscribers:"))
        layout.addWidget(self.subscribers_table)
        
        # Test signal button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        test_btn = QPushButton("🧪 Send Test Signal")
        test_btn.clicked.connect(self.send_test_signal)
        test_layout.addWidget(test_btn)
        layout.addLayout(test_layout)
        
        # Load and display subscribers
        self._load_subscribers()
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_history_tab(self) -> QWidget:
        """Create Signal History viewer sub-tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_history)
        refresh_layout.addWidget(refresh_btn)
        layout.addLayout(refresh_layout)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(9)
        self.history_table.setHorizontalHeaderLabels([
            "Timestamp", "Symbol", "Type", "Price", "ML Score",
            "TP", "SL", "Status", "Sent To"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.history_table)
        
        # Export button
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        export_btn = QPushButton("📥 Export to CSV")
        export_btn.clicked.connect(self.export_history)
        export_layout.addWidget(export_btn)
        layout.addLayout(export_layout)
        
        # Load history
        self.refresh_history()
        
        widget.setLayout(layout)
        return widget
    
    def _create_stats_tab(self) -> QWidget:
        """Create Statistics dashboard sub-tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Stats grid
        stats_group = QGroupBox("Signal Statistics")
        stats_layout = QGridLayout()
        
        # Create stat cards
        self.total_signals_label = self._create_stat_card("Total Signals", "0", "blue")
        self.buy_signals_label = self._create_stat_card("BUY Signals", "0", "green")
        self.sell_signals_label = self._create_stat_card("SELL Signals", "0", "red")
        self.success_rate_label = self._create_stat_card("Success Rate", "0%", "orange")
        
        stats_layout.addWidget(self.total_signals_label, 0, 0)
        stats_layout.addWidget(self.buy_signals_label, 0, 1)
        stats_layout.addWidget(self.sell_signals_label, 0, 2)
        stats_layout.addWidget(self.success_rate_label, 1, 0)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Statistics table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.setMaximumHeight(250)
        
        layout.addWidget(QLabel("Detailed Statistics:"))
        layout.addWidget(self.stats_table)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        refresh_btn = QPushButton("🔄 Refresh Stats")
        refresh_btn.clicked.connect(self.refresh_stats)
        refresh_layout.addWidget(refresh_btn)
        layout.addLayout(refresh_layout)
        
        # Initial load
        self.refresh_stats()
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QGroupBox:
        """Create a stat card widget."""
        group = QGroupBox(title)
        layout = QVBoxLayout()
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        colors = {
            'blue': 'color: #0066cc;',
            'green': 'color: #00aa00;',
            'red': 'color: #cc0000;',
            'orange': 'color: #ff9900;'
        }
        value_label.setStyleSheet(colors.get(color, ''))
        
        layout.addWidget(value_label)
        layout.setContentsMargins(10, 10, 10, 10)
        group.setLayout(layout)
        
        return group
    
    def _update_rr_ratio(self):
        """Update Risk/Reward ratio display."""
        tp = self.tp_percent.value()
        sl = self.sl_percent.value()
        ratio = tp / sl if sl > 0 else 0
        self.rr_ratio.setText(f"{ratio:.2f}:1")
    
    def test_token(self):
        """Test telegram bot token connection."""
        token = self.bot_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Warning", "Please enter a bot token first")
            return
        
        try:
            import requests
            response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    QMessageBox.information(
                        self, "Success",
                        f"✓ Bot Connected!\n\nBot: {bot_info.get('first_name', 'Unknown')}\n"
                        f"Username: @{bot_info.get('username', 'unknown')}"
                    )
                    self.service_status.setText("🟢 ONLINE")
                    self.service_status.setStyleSheet("color: green; font-weight: bold;")
                else:
                    QMessageBox.critical(self, "Error", "Invalid token")
            else:
                QMessageBox.critical(self, "Error", f"Connection failed: {response.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to test token: {e}")
    
    def save_config(self):
        """Save signal service configuration."""
        self.config.signal_service_enabled = self.service_enabled.isChecked()
        self.config.signal_bot_token = self.bot_token.text()
        self.config.signal_symbols = self.symbols.text()
        self.config.signal_filter_type = self.signal_type.currentText()
        self.config.signal_min_confidence = self.min_confidence.value()
        self.config.signal_tp_percent = self.tp_percent.value()
        self.config.signal_sl_percent = self.sl_percent.value()
        self.config.signal_template = self.template_type.currentText()
        self.config.max_signals_per_hour = self.max_signals_hour.value()
        
        QMessageBox.information(self, "Success", "✓ Signal configuration saved!")
        logger.info("Signal service configuration updated")
    
    
    def add_subscriber(self):
        """Add new subscriber."""
        chat_id = self.chat_id_input.text().strip()
        if not chat_id:
            QMessageBox.warning(self, "Warning", "Please enter a chat ID")
            return
        
        try:
            # Add to config
            current_ids = [id.strip() for id in self.config.signal_chat_ids.split(',') if id.strip()]
            if chat_id not in current_ids:
                current_ids.append(chat_id)
                self.config.signal_chat_ids = ",".join(current_ids)
                self.chat_id_input.clear()
                self._load_subscribers()
                QMessageBox.information(self, "Success", "✓ Subscriber added!")
            else:
                QMessageBox.warning(self, "Warning", "This chat ID already exists")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add subscriber: {e}")
    
    def _load_subscribers(self):
        """Load and display subscribers."""
        self.subscribers_table.setRowCount(0)
        
        if not self.config.signal_chat_ids:
            return
        
        chat_ids = [id.strip() for id in self.config.signal_chat_ids.split(',') if id.strip()]
        
        for idx, chat_id in enumerate(chat_ids):
            self.subscribers_table.insertRow(idx)
            self.subscribers_table.setItem(idx, 0, QTableWidgetItem(chat_id))
            self.subscribers_table.setItem(idx, 1, QTableWidgetItem("🟢 Active"))
            self.subscribers_table.setItem(idx, 2, QTableWidgetItem(datetime.now().strftime("%Y-%m-%d")))
            
            # Remove button
            remove_btn = QPushButton("❌")
            remove_btn.clicked.connect(lambda checked, cid=chat_id: self.remove_subscriber(cid))
            self.subscribers_table.setCellWidget(idx, 3, remove_btn)
    
    def remove_subscriber(self, chat_id: str):
        """Remove subscriber."""
        try:
            current_ids = [id.strip() for id in self.config.signal_chat_ids.split(',') if id.strip()]
            current_ids = [id for id in current_ids if id != chat_id]
            self.config.signal_chat_ids = ",".join(current_ids)
            self._load_subscribers()
            QMessageBox.information(self, "Success", "✓ Subscriber removed!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove subscriber: {e}")
    
    def send_test_signal(self):
        """Send test signal to all subscribers."""
        if not self.config.signal_chat_ids:
            QMessageBox.warning(self, "Warning", "No subscribers configured")
            return
        
        try:
            from signal_service import SignalBroadcaster
            
            broadcaster = SignalBroadcaster(self.config.signal_bot_token)
            chat_ids = [id.strip() for id in self.config.signal_chat_ids.split(',') if id.strip()]
            
            result = broadcaster.send_signal(
                symbol="XAUUSD",
                signal_type="BUY",
                price=2024.50,
                ml_score=0.85,
                tp_price=2050.00,
                sl_price=2020.00,
                tp_percent=self.config.signal_tp_percent,
                sl_percent=self.config.signal_sl_percent,
                chat_ids=chat_ids,
                template=self.config.signal_template
            )
            
            QMessageBox.information(
                self, "Test Signal Sent",
                f"✓ Sent to {result['sent_count']}/{len(chat_ids)} subscribers\n"
                f"Failed: {result['failed_count']}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send test signal: {e}")
    
    def refresh_history(self):
        """Refresh signal history table."""
        try:
            from signal_service import SignalBroadcaster
            
            broadcaster = SignalBroadcaster(
                self.config.signal_bot_token,
                self.config.signal_history_file
            )
            history = broadcaster.get_signal_history(limit=50)
            
            self.history_table.setRowCount(len(history))
            for idx, record in enumerate(history):
                self.history_table.setItem(idx, 0, QTableWidgetItem(record.get('timestamp', '')[:19]))
                self.history_table.setItem(idx, 1, QTableWidgetItem(record.get('symbol', '')))
                self.history_table.setItem(idx, 2, QTableWidgetItem(record.get('signal_type', '')))
                self.history_table.setItem(idx, 3, QTableWidgetItem(record.get('price', '')))
                self.history_table.setItem(idx, 4, QTableWidgetItem(record.get('ml_score', '')[:8]))
                self.history_table.setItem(idx, 5, QTableWidgetItem(record.get('tp_price', '')))
                self.history_table.setItem(idx, 6, QTableWidgetItem(record.get('sl_price', '')))
                
                status = record.get('status', '')
                status_label = "✓" if status == "success" else "⚠️"
                self.history_table.setItem(idx, 7, QTableWidgetItem(f"{status_label} {status}"))
                
                self.history_table.setItem(idx, 8, QTableWidgetItem(record.get('chat_ids_sent', '')[:30]))
        
        except Exception as e:
            logger.error(f"Error loading history: {e}")
    
    def export_history(self):
        """Export signal history to CSV."""
        try:
            from shutil import copy
            history_file = Path(self.config.signal_history_file)
            if history_file.exists():
                copy(history_file, Path.home() / "Desktop" / f"signal_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                QMessageBox.information(self, "Success", "✓ History exported to Desktop!")
            else:
                QMessageBox.warning(self, "Warning", "No history file found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")
    
    def refresh_stats(self):
        """Refresh statistics dashboard."""
        try:
            from signal_service import SignalBroadcaster
            
            broadcaster = SignalBroadcaster(
                self.config.signal_bot_token,
                self.config.signal_history_file
            )
            stats = broadcaster.get_statistics()
            
            # Update stat cards
            self.total_signals_label.findChild(QLabel).setText(str(stats.get('total_signals', 0)))
            self.buy_signals_label.findChild(QLabel).setText(str(stats.get('buy_signals', 0)))
            self.sell_signals_label.findChild(QLabel).setText(str(stats.get('sell_signals', 0)))
            self.success_rate_label.findChild(QLabel).setText(f"{stats.get('success_rate', 0):.1f}%")
            
            # Update stats table
            self.stats_table.setRowCount(0)
            metrics = [
                ("Total Signals Sent", str(stats.get('total_sent', 0))),
                ("Failed Broadcasts", str(stats.get('total_failed', 0))),
                ("BUY/SELL Ratio", f"{stats.get('buy_signals', 0)}/{stats.get('sell_signals', 0)}"),
            ]
            
            for idx, (metric, value) in enumerate(metrics):
                self.stats_table.insertRow(idx)
                self.stats_table.setItem(idx, 0, QTableWidgetItem(metric))
                self.stats_table.setItem(idx, 1, QTableWidgetItem(value))
        
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
    
    def get_config(self):
        """Get updated configuration from UI elements."""
        self.config.signal_service_enabled = self.service_enabled.isChecked()
        self.config.signal_bot_token = self.bot_token.text()
        
        # Extract chat IDs from subscribers table
        chat_ids = []
        for row in range(self.subscribers_table.rowCount()):
            chat_id_item = self.subscribers_table.item(row, 0)
            if chat_id_item:
                chat_ids.append(chat_id_item.text().strip())
        self.config.signal_chat_ids = ','.join(chat_ids) if chat_ids else self.config.signal_chat_ids
        
        self.config.signal_symbols = self.symbols.text()
        self.config.signal_tp_percent = self.tp_percent.value()
        self.config.signal_sl_percent = self.sl_percent.value()
        self.config.signal_min_confidence = self.min_confidence.value()
        self.config.signal_filter_type = self.signal_type.currentText()
        self.config.signal_template = self.template_type.currentText()
        self.config.max_signals_per_hour = self.max_signals_hour.value()
        
        return self.config
