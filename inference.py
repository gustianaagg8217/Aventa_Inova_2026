#!/usr/bin/env python3
"""
Inference pipeline for trained RandomForest model.

Loads the trained model and makes predictions on new market data.
Handles feature engineering and normalization.

Usage:
    from inference import ModelPredictor
    predictor = ModelPredictor(model_dir='models')
    predictions = predictor.predict(market_data_df)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('inference')


class ModelPredictor:
    """Load and use trained RandomForest model for inference."""
    
    def __init__(self, model_dir: Path = Path('models'), model_name: str = 'rf_baseline'):
        """
        Initialize predictor by loading model and scaler.
        
        Args:
            model_dir: Directory containing model artifacts
            model_name: Base name of model files (without extension)
        """
        self.model_dir = Path(model_dir)
        self.model_name = model_name
        self.model = None
        self.scaler = None
        self.metadata = None
        
        self._load_artifacts()
    
    def _load_artifacts(self):
        """Load model, scaler, and metadata from disk."""
        # Load model
        model_path = self.model_dir / f"{self.model_name}.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
        self.model = joblib.load(model_path)
        logger.info(f"Loaded model from {model_path}")
        
        # Load scaler
        scaler_path = self.model_dir / f"{self.model_name}_scaler.pkl"
        if not scaler_path.exists():
            raise FileNotFoundError(f"Scaler not found at {scaler_path}")
        self.scaler = joblib.load(scaler_path)
        logger.info(f"Loaded scaler from {scaler_path}")
        
        # Load metadata (optional)
        metadata_path = self.model_dir / f"{self.model_name}_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            logger.info(f"Loaded metadata from {metadata_path}")
    
    def add_technical_features(self, df: pd.DataFrame, 
                              sma_fast: int = 10, 
                              sma_slow: int = 30, 
                              rsi_period: int = 14, 
                              atr_period: int = 14) -> pd.DataFrame:
        """
        Add technical indicators to DataFrame (same as training).
        
        Args:
            df: DataFrame with OHLC data (close, high, low required)
            sma_fast: Period for fast SMA
            sma_slow: Period for slow SMA
            rsi_period: Period for RSI
            atr_period: Period for ATR
            
        Returns:
            DataFrame with technical features added
        """
        out = df.copy()
        out['close'] = out['close'].astype(float)
        out['high'] = out['high'].astype(float)
        out['low'] = out['low'].astype(float)
        
        # SMA
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
        
        # Log returns
        out['logret_1'] = np.log(out['close']).diff().fillna(0)
        
        # Additional features
        out['sma_spread'] = out['sma_fast'] - out['sma_slow']
        out['range'] = out['high'] - out['low']
        
        return out
    
    def extract_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Extract and scale features from market data.
        
        Args:
            df: DataFrame with OHLC data and technical indicators added
            
        Returns:
            Tuple of (feature DataFrame, scaled numpy array)
        """
        feature_cols = ['close', 'sma_fast', 'sma_slow', 'sma_spread', 'rsi', 'atr', 'range', 'logret_1']
        
        # Validate columns
        missing = [col for col in feature_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        
        X = df[feature_cols].copy()
        
        # Handle NaN
        if X.isna().any().any():
            logger.warning(f"Found {X.isna().sum().sum()} NaN values in features, filling forward...")
            X = X.fillna(method='ffill').fillna(0)
        
        # Scale
        X_scaled = self.scaler.transform(X)
        
        return X, X_scaled
    
    def predict(self, df: pd.DataFrame, return_proba: bool = False) -> Dict[str, np.ndarray]:
        """
        Make predictions on new market data.
        
        Args:
            df: DataFrame with OHLC data (time, close, high, low columns required)
            return_proba: If True, return prediction probabilities (for classification models)
            
        Returns:
            Dictionary with predictions and metadata
        """
        logger.info(f"Making predictions on {len(df)} samples")
        
        # Add technical features
        df_features = self.add_technical_features(df)
        
        # Extract and scale
        X_df, X_scaled = self.extract_features(df_features)
        
        # Predict
        preds = self.model.predict(X_scaled)
        
        result = {
            'predictions': preds,
            'features': X_df.values,
            'timestamps': df.get('time', pd.Series(range(len(df)))).values,
            'close': df['close'].values,
        }
        
        # Add feature importances
        if hasattr(self.model, 'feature_importances_'):
            feature_cols = ['close', 'sma_fast', 'sma_slow', 'sma_spread', 'rsi', 'atr', 'range', 'logret_1']
            importances = self.model.feature_importances_
            result['feature_importances'] = dict(zip(feature_cols, importances))
            logger.info(f"Top 3 features: {sorted(result['feature_importances'].items(), key=lambda x: x[1], reverse=True)[:3]}")
        
        return result
    
    def predict_single(self, close: float, high: float, low: float, 
                      lookback_df: Optional[pd.DataFrame] = None) -> float:
        """
        Make a single prediction for latest bar.
        
        Args:
            close: Latest close price
            high: Latest high price
            low: Latest low price
            lookback_df: Historical data for computing indicators (if None, uses last known state)
            
        Returns:
            Single prediction value
        """
        if lookback_df is None or len(lookback_df) == 0:
            logger.warning("No lookback data provided - using default values")
            # Create minimal dataframe for single prediction
            df = pd.DataFrame({
                'close': [close],
                'high': [high],
                'low': [low],
            })
        else:
            # Append new bar to lookback
            new_bar = pd.DataFrame({
                'close': [close],
                'high': [high],
                'low': [low],
            })
            df = pd.concat([lookback_df, new_bar], ignore_index=True)
        
        result = self.predict(df)
        pred = result['predictions'][-1]  # Get last prediction
        
        return float(pred)
    
    def get_model_info(self) -> Dict:
        """Get information about loaded model."""
        info = {
            'model_name': self.model_name,
            'model_type': type(self.model).__name__,
            'metadata': self.metadata,
        }
        
        if hasattr(self.model, 'n_estimators'):
            info['n_estimators'] = self.model.n_estimators
        
        if hasattr(self.model, 'max_depth'):
            info['max_depth'] = self.model.max_depth
        
        if self.metadata:
            info['test_metrics'] = self.metadata.get('test_metrics')
            info['validation_metrics'] = self.metadata.get('validation_metrics')
        
        return info


def main():
    """Demo usage of ModelPredictor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run inference pipeline")
    parser.add_argument("--data-file", type=str, help="Path to CSV file with OHLC data")
    parser.add_argument("--model-dir", type=str, default="models", help="Directory with trained models")
    parser.add_argument("--output", type=str, help="Save predictions to CSV")
    parser.add_argument("--show-info", action='store_true', help="Show model information")
    
    args = parser.parse_args()
    
    # Initialize predictor
    predictor = ModelPredictor(model_dir=args.model_dir)
    
    if args.show_info:
        info = predictor.get_model_info()
        print("\n=== Model Information ===")
        print(json.dumps(info, indent=2, default=str))
        return
    
    if not args.data_file:
        print("Demo: Loading sample data...")
        # Create synthetic OHLC data for demo
        np.random.seed(42)
        n = 100
        close = 2000 + np.cumsum(np.random.randn(n) * 0.5)
        df = pd.DataFrame({
            'time': pd.date_range('2026-01-01', periods=n, freq='1min'),
            'close': close,
            'high': close + np.abs(np.random.randn(n) * 0.3),
            'low': close - np.abs(np.random.randn(n) * 0.3),
        })
    else:
        print(f"Loading data from {args.data_file}")
        df = pd.read_csv(args.data_file)
        df['time'] = pd.to_datetime(df.get('time', pd.Series(range(len(df)))))
    
    # Make predictions
    print(f"\nMaking predictions on {len(df)} bars...")
    result = predictor.predict(df)
    
    print(f"\nPredictions shape: {result['predictions'].shape}")
    print(f"Last 5 predictions: {result['predictions'][-5:]}")
    
    if 'feature_importances' in result:
        print("\nFeature importances:")
        for feat, imp in sorted(result['feature_importances'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {feat}: {imp:.4f}")
    
    # Save if requested
    if args.output:
        output_df = pd.DataFrame({
            'time': result['timestamps'],
            'close': result['close'],
            'prediction': result['predictions'],
        })
        output_df.to_csv(args.output, index=False)
        print(f"\nSaved predictions to {args.output}")


if __name__ == "__main__":
    main()
