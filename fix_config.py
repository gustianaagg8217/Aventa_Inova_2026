#!/usr/bin/env python3
# Temporary script to fix config YAML

import os
import sys

# Fix config/config.yaml
config_file = 'config/config.yaml'
with open(config_file, 'r') as f:
    content = f.read()

# Check if magic_number already exists
if 'magic_number' not in content:
    # Add magic_number after symbol line
    content = content.replace(
        'trading:\n  symbol: "XAUUSD"',
        'trading:\n  symbol: "XAUUSD"\n  magic_number: 12345  # Unique identifier for orders'
    )
    with open(config_file, 'w') as f:
        f.write(content)
    print(f"✓ Added magic_number to {config_file}")
else:
    print(f"✓ {config_file} already has magic_number")

# Fix config/trading_config.yaml
trading_config = 'config/trading_config.yaml'
if os.path.exists(trading_config):
    with open(trading_config, 'r') as f:
        content = f.read()
    
    if 'magic_number' not in content:
        content = content.replace(
            'trading:\n  symbol: "XAUUSD"',
            'trading:\n  symbol: "XAUUSD"\n  magic_number: 12345  # Unique identifier for orders'
        )
        with open(trading_config, 'w') as f:
            f.write(content)
        print(f"✓ Added magic_number to {trading_config}")
    else:
        print(f"✓ {trading_config} already has magic_number")

# Update main.py to add fallback
main_file = 'main.py'
with open(main_file, 'r') as f:
    content = f.read()

# Check if fallback already exists
if 'magic_number = self.config.get' in content:
    print(f"✓ {main_file} already has fallback")
else:
    # Add fallback
    content = content.replace(
        '        self.order_executor = get_order_executor(\n            self.config[\'trading\'][\'magic_number\']\n        )',
        '        # Get magic number with fallback\n        magic_number = self.config.get(\'trading\', {}).get(\'magic_number\', 12345)\n        self.order_executor = get_order_executor(magic_number)'
    )
    with open(main_file, 'w') as f:
        f.write(content)
    print(f"✓ Added fallback to {main_file}")

print("\nAll fixes applied!")
