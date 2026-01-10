#!/usr/bin/env python3
"""
Model training pipeline for Aventa_Inova_2026.

Features:
- Load historical CSV tick/candle data (expects files like data/XAUUSD_M1_*.csv)
- Compute simple technical indicators (SMA, RSI, ATR) and returns
- Train either a scikit-learn baseline (RandomForestRegressor) or a simple PyTorch LSTM
- Save trained model and scaler to disk
- Basic evaluation on validation/test sets

Usage:
    python train_models.py --model sklearn --data-dir data --output-dir models
    python train_models.py --model lstm --epochs 30 --seq-len 32
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Optional import for LSTM
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

# Try to use project's logger if available
try:
    from trading_system.utils.logger import setup_logger
    _logger = setup_logger('training', Path('logs/training.log'), 'INFO')
    logger = logging.getLogger('training')
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('train_models')


# -------------------------
# Data / Feature utilities
# -------------------------
def find_latest_data_file(data_dir: Path, pattern: str = "BTCUSD_M1_*.csv") -> Optional[Path]:
    files = list(data_dir.glob(pattern))
    if not files:
        return None
    # choose largest file (heuristic for most complete)
    return max(files, key=lambda p: p.stat().st_size)


def load_data(file_path: Path) -> pd.DataFrame:
    """Load CSV and ensure datetime column."""
    df = pd.read_csv(file_path)
    # Common column name used in repo is 'time' and 'close','high','low','open'
    if 'time' not in df.columns:
        # try common alternatives
        for col in ('timestamp', 'date', 'datetime'):
            if col in df.columns:
                df = df.rename(columns={col: 'time'})
                break
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time').reset_index(drop=True)
    return df


def add_technical_features(df: pd.DataFrame, sma_fast: int = 10, sma_slow: int = 30, rsi_period: int = 14, atr_period: int = 14) -> pd.DataFrame:
    """Add simple technical indicators to DataFrame."""
    out = df.copy()
    out['close'] = out['close'].astype(float)
    out['high'] = out['high'].astype(float)
    out['low'] = out['low'].astype(float)

    out['sma_fast'] = out['close'].rolling(window=sma_fast, min_periods=1).mean()
    out['sma_slow'] = out['close'].rolling(window=sma_slow, min_periods=1).mean()

    # RSI
    delta = out['close'].diff()
    gain = delta.clip(lower=0).rolling(window=rsi_period, min_periods=1).mean()
    loss = -delta.clip(upper=0).rolling(window=rsi_period, min_periods=1).mean()
    rs = gain / (loss + 1e-9)
    out['rsi'] = 100 - (100 / (1 + rs))

    # ATR
    prev_close = out['close'].shift(1)
    tr1 = out['high'] - out['low']
    tr2 = (out['high'] - prev_close).abs()
    tr3 = (out['low'] - prev_close).abs()
    out['tr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    out['atr'] = out['tr'].rolling(window=atr_period, min_periods=1).mean()

    # log returns as target-friendly value
    out['logret_1'] = np.log(out['close']).diff().fillna(0)

    # Additional simple features
    out['sma_spread'] = out['sma_fast'] - out['sma_slow']
    out['range'] = out['high'] - out['low']
    out = out.dropna().reset_index(drop=True)
    return out


def build_features_and_target(df: pd.DataFrame, target_horizon: int = 1) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Build features X and target y.
    Target is the log-return after target_horizon bars.
    """
    df2 = df.copy().reset_index(drop=True)
    # use a subset of columns
    feature_cols = ['close', 'sma_fast', 'sma_slow', 'sma_spread', 'rsi', 'atr', 'range', 'logret_1']
    X = df2[feature_cols].copy()
    # target: future log return after target_horizon
    y = (np.log(df2['close'].shift(-target_horizon)) - np.log(df2['close'])).shift(0)
    # Drop last rows with NaN target
    valid = ~y.isna()
    X = X.loc[valid].reset_index(drop=True)
    y = y.loc[valid].reset_index(drop=True)
    return X, y


# -------------------------
# Sklearn training
# -------------------------
def train_sklearn_model(X_train, y_train, X_val, y_val, n_estimators: int = 200) -> Tuple[RandomForestRegressor, Dict]:
    logger.info("Training RandomForestRegressor (baseline)...")
    model = RandomForestRegressor(n_estimators=n_estimators, n_jobs=-1, random_state=42)
    logger.info(f"Fitting model on {len(X_train)} samples...")
    model.fit(X_train, y_train.ravel())
    logger.info("Model fitting complete. Predicting validation set...")
    preds_val = model.predict(X_val)
    metrics = evaluate_regression(y_val, preds_val)
    logger.info(f"Validation metrics: {metrics}")
    return model, metrics


def evaluate_regression(y_true, y_pred) -> Dict[str, float]:
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    return {'mse': float(mse), 'mae': float(mae), 'r2': float(r2)}


# -------------------------
# Optional PyTorch LSTM
# -------------------------
if TORCH_AVAILABLE:
    class SequenceDataset(Dataset):
        def __init__(self, X: np.ndarray, y: np.ndarray, seq_len: int = 32):
            self.X = X.astype(np.float32)
            self.y = y.astype(np.float32)
            self.seq_len = seq_len

        def __len__(self):
            return max(0, len(self.X) - self.seq_len)

        def __getitem__(self, idx):
            x_seq = self.X[idx: idx + self.seq_len]
            y_val = self.y[idx + self.seq_len]
            return x_seq, y_val

    class LSTMModel(nn.Module):
        def __init__(self, n_features: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.1):
            super().__init__()
            self.lstm = nn.LSTM(input_size=n_features, hidden_size=hidden_size, num_layers=num_layers, batch_first=True, dropout=dropout)
            self.head = nn.Sequential(
                nn.Linear(hidden_size, hidden_size // 2),
                nn.ReLU(),
                nn.Linear(hidden_size // 2, 1)
            )

        def forward(self, x):
            # x: (batch, seq_len, features)
            out, _ = self.lstm(x)
            # take last hidden state
            last = out[:, -1, :]
            return self.head(last).squeeze(-1)

    def train_lstm(X_train, y_train, X_val, y_val, seq_len: int = 32, epochs: int = 20, batch_size: int = 128, lr: float = 1e-3, device: str = "cpu"):
        logger.info("Training LSTM model (PyTorch)...")
        device = torch.device(device)
        train_ds = SequenceDataset(X_train, y_train, seq_len=seq_len)
        val_ds = SequenceDataset(X_val, y_val, seq_len=seq_len)
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

        model = LSTMModel(n_features=X_train.shape[1]).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn = nn.MSELoss()

        best_val = float('inf')
        for epoch in range(1, epochs + 1):
            logger.info(f"Starting epoch {epoch}/{epochs}...")
            model.train()
            train_losses = []
            for batch_idx, (xb, yb) in enumerate(train_loader):
                xb = xb.to(device)
                yb = yb.to(device)
                pred = model(xb)
                loss = loss_fn(pred, yb)
                opt.zero_grad()
                loss.backward()
                opt.step()
                train_losses.append(loss.item())
                if (batch_idx + 1) % 10 == 0 or (batch_idx + 1) == len(train_loader):
                    logger.debug(f"Epoch {epoch} Batch {batch_idx+1}/{len(train_loader)} Loss: {loss.item():.6f}")
            avg_train = float(np.mean(train_losses)) if train_losses else 0.0

            # validation
            model.eval()
            val_preds = []
            val_targets = []
            with torch.no_grad():
                for xb, yb in val_loader:
                    xb = xb.to(device)
                    pred = model(xb).cpu().numpy()
                    val_preds.append(pred)
                    val_targets.append(yb.numpy())
            if val_preds:
                val_preds = np.concatenate(val_preds, axis=0)
                val_targets = np.concatenate(val_targets, axis=0)
                metrics = evaluate_regression(val_targets, val_preds)
            else:
                metrics = {'mse': None, 'mae': None, 'r2': None}

            logger.info(f"Epoch {epoch}/{epochs} train_mse={avg_train:.6f} val_mse={metrics['mse']:.6f}")
            # save best
            if metrics['mse'] is not None and metrics['mse'] < best_val:
                best_val = metrics['mse']
                best_state = model.state_dict()

        # restore best
        logger.info("Restoring best model state from training.")
        model.load_state_dict(best_state)
        return model, metrics
else:
    # placeholders if torch not available
    def train_lstm(*args, **kwargs):
        raise RuntimeError("PyTorch is not available in this environment. Install torch to use LSTM model.")


# -------------------------
# Orchestration
# -------------------------
def prepare_datasets(X: pd.DataFrame, y: pd.Series, test_size: float = 0.1, val_size: float = 0.1, random_state: int = 42):
    """Split and scale datasets. Returns scaled arrays and scalers."""
    X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)
    # split train/val
    val_relative = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=val_relative, shuffle=False)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # convert targets to numpy arrays
    y_train_arr = y_train.to_numpy().reshape(-1, 1)
    y_val_arr = y_val.to_numpy().reshape(-1, 1)
    y_test_arr = y_test.to_numpy().reshape(-1, 1)

    return {
        'X_train': X_train_scaled,
        'X_val': X_val_scaled,
        'X_test': X_test_scaled,
        'y_train': y_train_arr,
        'y_val': y_val_arr,
        'y_test': y_test_arr,
        'scaler': scaler
    }


def save_model_and_artifacts(model, scaler, output_dir: Path, model_name: str = "model"):
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"{model_name}.pkl"
    scaler_path = output_dir / f"{model_name}_scaler.pkl"
    try:
        # joblib for sklearn
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        logger.info(f"Saved model to {model_path} and scaler to {scaler_path}")
    except Exception:
        # fallback for torch: save state_dict and scaler
        if TORCH_AVAILABLE and isinstance(model, torch.nn.Module):
            torch.save(model.state_dict(), output_dir / f"{model_name}.pt")
            joblib.dump(scaler, scaler_path)
            logger.info(f"Saved torch model state_dict to {output_dir / f'{model_name}.pt'} and scaler to {scaler_path}")
        else:
            raise


def run_training_flow(
    data_dir: Path,
    output_dir: Path,
    model_type: str = "sklearn",
    target_horizon: int = 1,
    n_estimators: int = 200,
    seq_len: int = 32,
    epochs: int = 20,
    device: str = "cpu"
):
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    data_file = find_latest_data_file(data_dir)
    if data_file is None:
        logger.error(f"No data file found in {data_dir}. Please put CSV files like XAUUSD_M1_*.csv in that folder.")
        sys.exit(1)

    logger.info(f"Loading data from {data_file}")
    df = load_data(data_file)
    logger.info(f"Loaded {len(df)} rows from data file.")
    df = add_technical_features(df)
    logger.info(f"Technical features added. Data now has {df.shape[1]} columns.")
    X_df, y_ser = build_features_and_target(df, target_horizon=target_horizon)
    logger.info(f"Feature matrix shape: {X_df.shape}, Target shape: {y_ser.shape}")
    if len(X_df) < 200:
        logger.warning("Too few rows after feature generation; results may be poor.")

    ds = prepare_datasets(X_df, y_ser)
    logger.info("Datasets prepared and scaled.")
    X_train = ds['X_train']
    X_val = ds['X_val']
    X_test = ds['X_test']
    y_train = ds['y_train']
    y_val = ds['y_val']
    y_test = ds['y_test']
    scaler = ds['scaler']

    if model_type == 'sklearn':
        model, val_metrics = train_sklearn_model(X_train, y_train, X_val, y_val, n_estimators=n_estimators)
        # evaluate on test
        preds_test = model.predict(X_test)
        test_metrics = evaluate_regression(y_test, preds_test)
        logger.info(f"Test metrics: {test_metrics}")
        save_model_and_artifacts(model, scaler, output_dir, model_name="rf_baseline")
    elif model_type == 'lstm':
        if not TORCH_AVAILABLE:
            logger.error("Torch not available. Install PyTorch to train LSTM model.")
            raise RuntimeError("Torch not available")
        # For LSTM create sequences; note our dataset creation for LSTM uses shapes (n_samples, seq_len, features)
        model_torch, val_metrics = train_lstm(X_train, y_train, X_val, y_val, seq_len=seq_len, epochs=epochs, device=device)
        # For test evaluation we need to build a sequence-based dataset for test set as well
        # Build test sequences quickly:
        test_ds = []
        for i in range(0, X_test.shape[0] - seq_len):
            test_ds.append((X_test[i:i+seq_len], y_test[i+seq_len]))
        if test_ds:
            X_test_seq = np.stack([t[0] for t in test_ds])
            y_test_seq = np.stack([t[1] for t in test_ds]).ravel()
            model_torch.eval()
            with torch.no_grad():
                preds = model_torch(torch.tensor(X_test_seq, dtype=torch.float32).to(device)).cpu().numpy()
            test_metrics = evaluate_regression(y_test_seq, preds)
        else:
            test_metrics = {'mse': None, 'mae': None, 'r2': None}
        logger.info(f"Test metrics: {test_metrics}")
        save_model_and_artifacts(model_torch, scaler, output_dir, model_name="lstm_model")
    else:
        raise ValueError("Unknown model_type. Choose 'sklearn' or 'lstm'.")


# -------------------------
# CLI
# -------------------------
def parse_args():
    p = argparse.ArgumentParser(description="Train models for Aventa_Inova_2026")
    p.add_argument("--data-dir", type=str, default="data", help="Path to data directory with CSV files")
    p.add_argument("--output-dir", type=str, default="models", help="Where to save models/scalers")
    p.add_argument("--model", type=str, default="sklearn", choices=["sklearn", "lstm"], help="Model type to train")
    p.add_argument("--target-horizon", type=int, default=1, help="Prediction horizon in bars")
    p.add_argument("--n-estimators", type=int, default=200, help="n_estimators for RandomForest")
    p.add_argument("--seq-len", type=int, default=32, help="Sequence length for LSTM")
    p.add_argument("--epochs", type=int, default=20, help="Epochs for LSTM")
    p.add_argument("--device", type=str, default="cpu", help="Torch device (cpu or cuda)")
    return p.parse_args()


def main():
    args = parse_args()
    logger.info("Starting training pipeline with args: %s", json.dumps(vars(args)))
    try:
        run_training_flow(
            data_dir=Path(args.data_dir),
            output_dir=Path(args.output_dir),
            model_type=args.model,
            target_horizon=args.target_horizon,
            n_estimators=args.n_estimators,
            seq_len=args.seq_len,
            epochs=args.epochs,
            device=args.device
        )
        logger.info("Training pipeline finished.")
    except Exception as e:
        logger.exception("Training pipeline failed: %s", str(e))
        sys.exit(2)


if __name__ == "__main__":
    main()