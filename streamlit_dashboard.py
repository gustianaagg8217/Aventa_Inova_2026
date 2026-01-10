#!/usr/bin/env python3
"""
Web-based monitoring dashboard for real-time trading signals (Streamlit).

Displays predictions, signals, metrics, and market data using Streamlit.

Usage:
    streamlit run streamlit_dashboard.py
    
    # Or with custom port:
    streamlit run streamlit_dashboard.py --server.port 8501
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

try:
    import streamlit as st
except ImportError:
    raise ImportError("Streamlit required: pip install streamlit plotly pandas")

from inference import ModelPredictor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dashboard')

# Streamlit page config
st.set_page_config(
    page_title="Aventa Trading Monitor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .signal-buy {
        color: #00d084;
        font-weight: bold;
    }
    .signal-sell {
        color: #ff2b2b;
        font-weight: bold;
    }
    .signal-hold {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_predictor(model_dir: str = "models") -> ModelPredictor:
    """Load ML model (cached)."""
    return ModelPredictor(model_dir=model_dir)


@st.cache_data(ttl=30)
def load_predictions(log_file: str = "logs/realtime_predictions.jsonl") -> pd.DataFrame:
    """Load predictions from JSONL log (cached for 30s)."""
    log_path = Path(log_file)
    
    if not log_path.exists():
        return pd.DataFrame()
    
    predictions = []
    try:
        with open(log_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        data['timestamp'] = pd.to_datetime(data['timestamp'])
                        predictions.append(data)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.error(f"Error loading predictions: {e}")
    
    if predictions:
        return pd.DataFrame(predictions)
    return pd.DataFrame()


def get_signal_emoji(signal: str) -> str:
    """Get emoji for signal type."""
    if signal == 'BUY':
        return '🟢'
    elif signal == 'SELL':
        return '🔴'
    else:
        return '🟡'


def render_metrics(df: pd.DataFrame, model_info: Dict):
    """Render summary metrics."""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Predictions",
            len(df)
        )
    
    with col2:
        buy_count = len(df[df['signal'] == 'BUY'])
        pct = f"{100*buy_count/len(df):.1f}%" if len(df) > 0 else "0%"
        st.metric("Buy Signals", buy_count, pct)
    
    with col3:
        sell_count = len(df[df['signal'] == 'SELL'])
        pct = f"{100*sell_count/len(df):.1f}%" if len(df) > 0 else "0%"
        st.metric("Sell Signals", sell_count, pct)
    
    with col4:
        hold_count = len(df[df['signal'] == 'HOLD'])
        pct = f"{100*hold_count/len(df):.1f}%" if len(df) > 0 else "0%"
        st.metric("Hold Signals", hold_count, pct)
    
    with col5:
        if not df.empty:
            latest_close = df['close'].iloc[-1]
            st.metric("Latest Close", f"${latest_close:.2f}")


def render_prediction_chart(df: pd.DataFrame):
    """Render prediction chart."""
    if df.empty:
        st.warning("No prediction data available")
        return
    
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['close'],
        name='Close Price',
        yaxis='y1',
        line=dict(color='rgba(0, 0, 255, 0.7)', width=2),
        mode='lines',
        hovertemplate='<b>Price</b><br>Time: %{x}<br>Close: $%{y:.2f}<extra></extra>'
    ))
    
    # Add prediction scatter with color gradient
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['prediction'],
        name='Prediction',
        yaxis='y2',
        mode='markers',
        marker=dict(
            size=10,
            color=df['prediction'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Pred", x=1.08),
            line=dict(width=1, color='white')
        ),
        hovertemplate='<b>Prediction</b><br>Time: %{x}<br>Value: %{y:.2e}<extra></extra>'
    ))
    
    # Add signal markers
    buy_df = df[df['signal'] == 'BUY']
    sell_df = df[df['signal'] == 'SELL']
    
    if len(buy_df) > 0:
        fig.add_trace(go.Scatter(
            x=buy_df['timestamp'],
            y=buy_df['close'],
            name='Buy Signal',
            yaxis='y1',
            mode='markers',
            marker=dict(size=15, color='#00d084', symbol='triangle-up', 
                       line=dict(color='darkgreen', width=2)),
            hovertemplate='<b>BUY</b><br>Time: %{x}<br>Price: $%{y:.2f}<extra></extra>'
        ))
    
    if len(sell_df) > 0:
        fig.add_trace(go.Scatter(
            x=sell_df['timestamp'],
            y=sell_df['close'],
            name='Sell Signal',
            yaxis='y1',
            mode='markers',
            marker=dict(size=15, color='#ff2b2b', symbol='triangle-down',
                       line=dict(color='darkred', width=2)),
            hovertemplate='<b>SELL</b><br>Time: %{x}<br>Price: $%{y:.2f}<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title="Real-Time Predictions & Trading Signals",
        hovermode='x unified',
        height=600,
        yaxis=dict(title='Close Price ($)', position=0),
        yaxis2=dict(
            title='Prediction',
            overlaying='y',
            side='right'
        ),
        xaxis=dict(title='Time'),
        legend=dict(x=0.01, y=0.99)
    )
    
    st.plotly_chart(fig, use_container_width=True, key="pred_chart")


def render_signal_history(df: pd.DataFrame):
    """Render recent trading signals."""
    st.subheader("📋 Recent Trading Signals")
    
    if df.empty:
        st.info("No signals yet")
        return
    
    # Get last N signals based on user selection
    n = st.slider("Number of signals to display", 5, 50, 20)
    recent = df.sort_values('timestamp', ascending=False).head(n)
    
    # Create display dataframe
    display_df = recent[[
        'timestamp', 'close', 'prediction', 'signal'
    ]].copy()
    
    display_df.columns = ['Time', 'Close ($)', 'Prediction', 'Signal']
    display_df['Time'] = display_df['Time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['Close ($)'] = display_df['Close ($)'].apply(lambda x: f"${x:.2f}")
    display_df['Prediction'] = display_df['Prediction'].apply(lambda x: f"{x:.2e}")
    display_df['Signal'] = display_df['Signal'].apply(
        lambda x: f"{get_signal_emoji(x)} {x}"
    )
    
    # Display as table
    st.dataframe(
        display_df.reset_index(drop=True),
        use_container_width=True,
        height=400
    )


def render_prediction_stats(df: pd.DataFrame):
    """Render prediction statistics."""
    st.subheader("📈 Prediction Statistics")
    
    if df.empty:
        st.warning("No data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Prediction distribution
        fig = go.Figure(data=[
            go.Histogram(
                x=df['prediction'],
                nbinsx=50,
                name='Predictions',
                marker_color='rgba(100, 149, 237, 0.7)'
            )
        ])
        fig.update_layout(
            title="Prediction Distribution",
            xaxis_title="Prediction Value",
            yaxis_title="Frequency",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, key="hist_dist")
    
    with col2:
        # Signal pie chart
        signal_counts = df['signal'].value_counts()
        colors_map = {'BUY': '#00d084', 'SELL': '#ff2b2b', 'HOLD': '#ffc107'}
        colors = [colors_map.get(sig, '#999999') for sig in signal_counts.index]
        
        fig = go.Figure(data=[go.Pie(
            labels=signal_counts.index,
            values=signal_counts.values,
            marker=dict(colors=colors),
            textinfo='label+percent'
        )])
        fig.update_layout(
            title="Signal Distribution",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True, key="signal_pie")
    
    # Statistics table
    st.subheader("Summary Statistics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Mean", f"{df['prediction'].mean():.2e}")
    with col2:
        st.metric("Std Dev", f"{df['prediction'].std():.2e}")
    with col3:
        st.metric("Min", f"{df['prediction'].min():.2e}")
    with col4:
        st.metric("Max", f"{df['prediction'].max():.2e}")
    with col5:
        st.metric("Median", f"{df['prediction'].median():.2e}")


def render_model_info(model_info: Dict):
    """Render model information."""
    st.subheader("🤖 Model Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        **Model Name:** `{model_info.get('model_name', 'N/A')}`  
        **Model Type:** `{model_info.get('model_type', 'N/A')}`  
        **Estimators:** `{model_info.get('n_estimators', 'N/A')}`
        """)
    
    with col2:
        if 'test_metrics' in model_info and model_info['test_metrics']:
            metrics = model_info['test_metrics']
            st.markdown(f"""
            **Test Metrics:**
            - R²: `{metrics['r2']:.4f}`
            - MAE: `{metrics['mae']:.6f}`
            - MSE: `{metrics['mse']:.2e}`
            """)
    
    with col3:
        if 'metadata' in model_info and model_info['metadata']:
            metadata = model_info['metadata']
            st.markdown(f"""
            **Training Data:**
            - Start: `{metadata.get('data_start', 'N/A')}`
            - End: `{metadata.get('data_end', 'N/A')}`
            - Horizon: `{metadata.get('target_horizon', 1)} bar(s)`
            """)
    
    # Feature importances
    st.markdown("**Feature Importance:**")
    if 'feature_importances' in model_info and model_info['feature_importances']:
        importances = model_info['feature_importances']
        top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                y=[f[0] for f in top_features],
                x=[f[1] for f in top_features],
                orientation='h',
                marker_color='rgba(100, 149, 237, 0.7)',
                text=[f"{f[1]:.4f}" for f in top_features],
                textposition='auto'
            )
        ])
        fig.update_layout(
            title="Feature Importances",
            xaxis_title="Importance",
            yaxis_title="Feature",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, key="feat_imp")


def main():
    """Main dashboard app."""
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 Aventa Trading Monitor")
    with col2:
        st.metric("Status", "🟢 Live", delta="Running")
    
    st.markdown("Real-time ML predictions and trading signals for XAUUSD market")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        model_dir = st.text_input("Model Directory", value="models", key="model_dir_input")
        log_file = st.text_input("Log File", value="logs/realtime_predictions.jsonl", key="log_file_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Now"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            if st.button("📂 Open Directory"):
                import webbrowser
                webbrowser.open(str(Path(log_file).parent))
        
        st.divider()
        
        st.subheader("ℹ️ Quick Start")
        with st.expander("Start Monitoring"):
            st.code("""
python real_time_monitor.py \\
    --source csv \\
    --iterations 100 \\
    --interval 1
            """, language="bash")
        
        with st.expander("Live MT5"):
            st.code("""
python real_time_monitor.py \\
    --source mt5 \\
    --login 123456 \\
    --password pass \\
    --server server
            """, language="bash")
        
        st.divider()
        
        st.subheader("📌 Project Links")
        st.markdown("""
        - [GitHub Repository](https://github.com/gustianaagg8217/Aventa_Inova_2026)
        - [Model Training](training)
        - [Inference Pipeline](inference)
        - [Real-time Monitor](real_time_monitor)
        """)
    
    # Load data
    try:
        predictor = load_predictor(model_dir)
        model_info = predictor.get_model_info()
        df = load_predictions(log_file)
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.info("Make sure to run: `python real_time_monitor.py` first")
        return
    
    # Check if data exists
    if df.empty:
        st.info("⏳ No prediction data yet. Start the real-time monitor:")
        st.code("""
python real_time_monitor.py --source csv --iterations 100
        """)
        return
    
    # Main content
    render_metrics(df, model_info)
    
    st.divider()
    
    # Charts and info tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Live Predictions",
        "📊 Statistics", 
        "🔧 Model Info",
        "📋 Raw Data"
    ])
    
    with tab1:
        render_prediction_chart(df)
        st.divider()
        render_signal_history(df)
    
    with tab2:
        render_prediction_stats(df)
    
    with tab3:
        render_model_info(model_info)
    
    with tab4:
        st.subheader("📋 Raw Prediction Data")
        st.dataframe(
            df.sort_values('timestamp', ascending=False),
            use_container_width=True,
            height=500
        )
        
        # Download option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="predictions.csv",
            mime="text/csv"
        )
    
    # Footer
    st.divider()
    
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    with footer_col1:
        if not df.empty:
            last_update = df['timestamp'].max()
            st.metric("Last Update", last_update.strftime('%H:%M:%S'))
    with footer_col2:
        st.metric("Total Records", len(df))
    with footer_col3:
        if not df.empty:
            latest_pred = df['prediction'].iloc[-1]
            st.metric("Latest Prediction", f"{latest_pred:.2e}")


if __name__ == "__main__":
    main()
