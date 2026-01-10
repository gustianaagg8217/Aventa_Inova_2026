#!/usr/bin/env python3
"""
Model training pipeline for Aventa_Inova_2026 (updated).

Changes in this update:
- Save PyTorch models as state_dict (.pt) instead of pickled .pkl
- Always save scaler with joblib
- Write metadata JSON with train/val/test metrics and arguments
- Save per-epoch train/val losses to logs/ as JSON
- Compute and log baseline (mean predictor) metrics for context
- Add optional diagnostic plots (if matplotlib available)

Usage examples:
    python train_models.py --model sklearn --data-dir data --output-dir models
    python train_models.py --model lstm --epochs 30 --seq-len 32
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from datetime import datetime
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

# Optional plotting
try:
    import matplotlib.pyplot as plt
    PLOTTING_AVAILABLE = True
except Exception:
    PLOTTING_AVAILABLE = False

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
def find_latest_data_file(data_dir: Path, pattern: str = "XAUUSD_M1_*.csv") -> Optional[Path]:
    files = list(Path(data_dir).glob(pattern))
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
    model.fit(X_train, y_train.ravel())
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
            # Ensure targets are 1D arrays (n_samples,)
            self.y = y.ravel().astype(np.float32)
            self.seq_len = seq_len

        def __len__(self):
            return max(0, len(self.X) - self.seq_len)

        def __getitem__(self, idx):
            x_seq = self.X[idx: idx + self.seq_len]
            # return scalar target (already 1D)
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
        best_state = None
        history = {'train_mse': [], 'val_mse': []}
        for epoch in range(1, epochs + 1):
            model.train()
            train_losses = []
            for xb, yb in train_loader:
                xb = xb.to(device)
                # ensure target and prediction shapes match: (batch,)
                yb = yb.to(device).view(-1)
                pred = model(xb).view(-1)
                loss = loss_fn(pred, yb)
                opt.zero_grad()
                loss.backward()
                opt.step()
                train_losses.append(loss.item())
            avg_train = float(np.mean(train_losses)) if train_losses else 0.0

            # validation
            model.eval()
            val_preds = []
            val_targets = []
            with torch.no_grad():
                for xb, yb in val_loader:
                    xb = xb.to(device)
                    preds_batch = model(xb).cpu().numpy().ravel()
                    val_preds.append(preds_batch)
                    # robust conversion for yb:
                    if hasattr(yb, 'cpu'):
                        arr = yb.cpu().numpy()
                    else:
                        arr = np.asarray(yb)
                    val_targets.append(arr.ravel())

            history['train_mse'].append(avg_train)
            history['val_mse'].append(val_mse if val_mse is not None else float('nan'))

            logger.info(f"Epoch {epoch}/{epochs} train_mse={avg_train:.6f} val_mse={metrics['mse']:.6f}")
            # save best
            if metrics['mse'] is not None and metrics['mse'] < best_val:
                best_val = metrics['mse']
                best_state = model.state_dict()

        if best_state is not None:
            model.load_state_dict(best_state)
        return model, metrics, history
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
        'scaler': scaler,
        'X_train_df': X_train,
        'X_val_df': X_val,
        'X_test_df': X_test,
        'y_train_ser': y_train,
        'y_val_ser': y_val,
        'y_test_ser': y_test,
    }


def save_model_and_artifacts(model, scaler, output_dir: Path, model_name: str = "model", metadata: Dict = None, history: Dict = None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scaler_path = output_dir / f"{model_name}_scaler.pkl"
    joblib.dump(scaler, scaler_path)
    logger.info(f"Saved scaler to {scaler_path}")

    # Save model depending on type
    if TORCH_AVAILABLE and isinstance(model, torch.nn.Module):
        model_path = output_dir / f"{model_name}.pt"
        torch.save(model.state_dict(), model_path)
        logger.info(f"Saved torch model state_dict to {model_path}")
    else:
        # sklearn or other picklable model
        model_path = output_dir / f"{model_name}.pkl"
        joblib.dump(model, model_path)
        logger.info(f"Saved model to {model_path}")

    # Save metadata & history
    if metadata is None:
        metadata = {}
    metadata_path = output_dir / f"{model_name}_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info(f"Saved metadata to {metadata_path}")

    if history:
        history_path = output_dir / f"{model_name}_history.json"
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2, default=float)
        logger.info(f"Saved training history to {history_path}")


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
    df = add_technical_features(df)
    X_df, y_ser = build_features_and_target(df, target_horizon=target_horizon)
    if len(X_df) < 200:
        logger.warning("Too few rows after feature generation; results may be poor.")

    ds = prepare_datasets(X_df, y_ser)
    X_train = ds['X_train']
    X_val = ds['X_val']
    X_test = ds['X_test']
    y_train = ds['y_train']
    y_val = ds['y_val']
    y_test = ds['y_test']
    scaler = ds['scaler']

    # Baseline metrics (mean predictor)
    baseline_pred = np.full_like(y_test, np.mean(y_train))
    baseline_metrics = evaluate_regression(y_test, baseline_pred)
    logger.info(f"Baseline (mean predictor) test metrics: {baseline_metrics}")

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    logs_dir = Path('logs')
    logs_dir.mkdir(parents=True, exist_ok=True)

    model_name = None
    metadata = {
        'data_file': str(data_file),
        'data_start': str(df['time'].min()),
        'data_end': str(df['time'].max()),
        'target_horizon': target_horizon,
        'baseline_test_metrics': baseline_metrics,
        'run_timestamp': timestamp,
    }
    history = None

    if model_type == 'sklearn':
        model_name = 'rf_baseline'
        model, val_metrics = train_sklearn_model(X_train, y_train, X_val, y_val, n_estimators=n_estimators)
        preds_test = model.predict(X_test)
        test_metrics = evaluate_regression(y_test, preds_test)
        logger.info(f"Test metrics: {test_metrics}")
        metadata.update({'validation_metrics': val_metrics, 'test_metrics': test_metrics})
        save_model_and_artifacts(model, scaler, output_dir, model_name=model_name, metadata=metadata)

        # diagnostics: save small sample visualization if possible
        try:
            if PLOTTING_AVAILABLE:
                sample_n = min(1000, len(y_test))
                plt.figure(figsize=(10, 4))
                plt.plot(y_test[:sample_n], label='true')
                plt.plot(preds_test[:sample_n], label='pred')
                plt.legend()
                plt.title('Sklearn predictions vs true (sample)')
                plt.tight_layout()
                ppath = logs_dir / f"{model_name}_preds_{timestamp}.png"
                plt.savefig(ppath)
                plt.close()
                logger.info(f"Saved diagnostic plot to {ppath}")
        except Exception as e:
            logger.warning(f"Failed to create diagnostic plot: {e}")

    elif model_type == 'lstm':
        if not TORCH_AVAILABLE:
            logger.error("Torch not available. Install PyTorch to train LSTM model.")
            raise RuntimeError("Torch not available")
        model_name = 'lstm_model'
        model_torch, val_metrics, history = train_lstm(X_train, y_train, X_val, y_val, seq_len=seq_len, epochs=epochs, device=device)

        # Build test sequences quickly for evaluation
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
        metadata.update({'validation_metrics': val_metrics, 'test_metrics': test_metrics, 'history_len': {k: len(v) for k,v in (history or {}).items()}})
        save_model_and_artifacts(model_torch, scaler, output_dir, model_name=model_name, metadata=metadata, history=history)

        # diagnostics: save sample plot
        try:
            if PLOTTING_AVAILABLE and test_ds:
                sample_n = min(1000, len(y_test_seq))
                plt.figure(figsize=(10, 4))
                plt.plot(y_test_seq[:sample_n], label='true')
                plt.plot(preds[:sample_n], label='pred')
                plt.legend()
                plt.title('LSTM predictions vs true (sample)')
                plt.tight_layout()
                ppath = logs_dir / f"{model_name}_preds_{timestamp}.png"
                plt.savefig(ppath)
                plt.close()
                logger.info(f"Saved diagnostic plot to {ppath}")
        except Exception as e:
            logger.warning(f"Failed to create diagnostic plot: {e}")

    else:
        raise ValueError("Unknown model_type. Choose 'sklearn' or 'lstm'.")

    # Save a run-level JSON log summarizing arguments and metrics
    run_summary = {
        'model_type': model_type,
        'model_name': model_name,
        'metadata': metadata,
        'history': history,
    }
    run_path = logs_dir / f"training_run_{timestamp}.json"
    with open(run_path, 'w') as f:
        json.dump(run_summary, f, indent=2, default=str)
    logger.info(f"Saved run summary to {run_path}")


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

