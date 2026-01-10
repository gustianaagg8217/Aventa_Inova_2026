from setuptools import setup, find_packages

setup(
    name="trading_system",
    version="0.1.0",
    description="HFT Trading System for GOLD/XAUUSD with MT5",
    author="Agus Gustiana",
    packages=find_packages(),
    install_requires=[
        'MetaTrader5>=5.0.45',
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'torch>=2.0.0',
        'scikit-learn>=1.3.0',
        'fastapi>=0.100.0',
        'uvicorn>=0.23.0',
        'pyyaml>=6.0',
        'redis>=4.5.0',
        'structlog>=23.1.0',
        'numba>=0.57.0',
        'websockets>=11.0',
        'aiohttp>=3.8.0',
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'trading-system=main:main',
        ],
    },
)