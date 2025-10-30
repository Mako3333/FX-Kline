"""
Streamlit web UI for FX-Kline
Interactive interface for fetching FX OHLC data
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
# Add parent directory to path for imports
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent.parent  # Go up to project root
sys.path.insert(0, str(project_root / "src"))

from fx_kline.core import (
    OHLCRequest,
    fetch_batch_ohlc_sync,
    get_preset_pairs,
    get_preset_timeframes,
    get_supported_pairs,
    get_default_business_days_for_timeframe,
    export_to_csv,
    export_to_json,
    export_to_csv_string,
    get_jst_now,
)

TIMEFRAME_LABELS = {
    "1m": "1 Min",
    "5m": "5 Min",
    "15m": "15 Min",
    "30m": "30 Min",
    "1h": "1 Hour",
    "4h": "4 Hours",
    "1d": "1 Day",
    "1wk": "1 Week",
    "1mo": "1 Month",
}


# Page configuration
st.set_page_config(
    page_title="FX-Kline",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for styling
st.markdown("""
    <style>
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin-bottom: 15px;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
        margin-bottom: 15px;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Page title
st.title("📈 FX-Kline OHLC Data Fetcher")

st.markdown("""
Fetch FX OHLC data for multiple currency pairs and timeframes in parallel.
Export to CSV, JSON, or copy to clipboard.
""")

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

# Get preset and supported options
preset_pairs = get_preset_pairs()
preset_timeframes = get_preset_timeframes()
supported_pairs = get_supported_pairs()

# Currency pair selection
st.sidebar.subheader("Currency Pairs")
selected_pairs = st.sidebar.multiselect(
    "Select currency pairs:",
    options=preset_pairs,
    default=["USDJPY"],
    format_func=lambda x: f"{supported_pairs[x]} ({x})" if x in supported_pairs else x
)

# Timeframe selection
st.sidebar.subheader("Timeframes")
selected_timeframes = st.sidebar.multiselect(
    "Select timeframes:",
    options=preset_timeframes,
    default=["1h"],
    format_func=lambda x: TIMEFRAME_LABELS.get(x, x)
)

# Period specification
st.sidebar.subheader("Data Period (Business Days)")
st.sidebar.info("Configure business-day lookbacks per pair and timeframe. Today is included when data is available.")

period_config = []

if selected_pairs and selected_timeframes:
    for pair in selected_pairs:
        pair_label = supported_pairs.get(pair, pair)
        display_name = pair_label.split("(")[0].strip()
        with st.sidebar.expander(f"{display_name} ({pair})", expanded=len(selected_pairs) == 1):
            for timeframe in selected_timeframes:
                timeframe_label = TIMEFRAME_LABELS.get(timeframe, timeframe)
                default_days = get_default_business_days_for_timeframe(timeframe)
                period_days = st.sidebar.number_input(
                    f"{timeframe_label} – business days",
                    min_value=1,
                    max_value=365,
                    value=default_days,
                    key=f"period_{pair}_{timeframe}"
                )
                period_config.append((pair, timeframe, int(period_days)))
else:
    st.sidebar.info("Add at least one pair and timeframe to configure lookbacks.")

# Fetch button
st.sidebar.markdown("---")

if st.sidebar.button("🚀 Fetch Data", key="fetch_button", use_container_width=True):

    if not selected_pairs:
        st.error("❌ Please select at least one currency pair")
    elif not selected_timeframes:
        st.error("❌ Please select at least one timeframe")
    elif not period_config:
        st.error("❌ Configure at least one period for the selected pair and timeframe")
    else:
        # Build requests
        requests = []

        for pair, timeframe, period_days in period_config:
            period_str = f"{int(period_days)}d"
            requests.append(OHLCRequest(
                pair=pair,
                interval=timeframe,
                period=period_str
            ))

        st.session_state.requests = requests
        st.session_state.fetch_clicked = True

# Display results
if "fetch_clicked" in st.session_state and st.session_state.fetch_clicked:

    st.markdown("---")
    st.header("📊 Fetching Data...")

    # Show progress
    progress_placeholder = st.empty()
    status_placeholder = st.empty()

    progress_placeholder.info(f"⏳ Fetching {len(st.session_state.requests)} requests in parallel...")

    # Fetch data
    response = fetch_batch_ohlc_sync(st.session_state.requests)

    # Clear progress
    progress_placeholder.empty()

    # Store response in session
    st.session_state.response = response

    # Display summary
    st.markdown("---")
    st.header("📈 Results Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Requested", response.total_requested)

    with col2:
        st.metric("Successful", response.total_succeeded, delta="✓")

    with col3:
        st.metric("Failed", response.total_failed, delta="✗" if response.total_failed > 0 else None)

    with col4:
        success_rate = (response.total_succeeded / response.total_requested * 100) if response.total_requested > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")

    # Display successful data
    if response.successful:
        st.markdown("---")
        st.header("✅ Successful Fetches")

        for ohlc_data in response.successful:
            with st.expander(f"📊 {ohlc_data.pair} | {ohlc_data.interval} | {ohlc_data.period}"):
                # Data info
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.info(f"**Data Points:** {ohlc_data.data_count}")

                with col2:
                    if ohlc_data.rows:
                        first_date = ohlc_data.rows[0]['Datetime']
                        last_date = ohlc_data.rows[-1]['Datetime']
                        st.info(f"**Period:** {first_date} to {last_date}")

                with col3:
                    st.info(f"**Fetched:** {ohlc_data.timestamp_jst.strftime('%Y-%m-%d %H:%M:%S JST') if ohlc_data.timestamp_jst else 'N/A'}")

                # Display data table
                st.subheader("Data Preview")
                df_display = pd.DataFrame(ohlc_data.rows)
                st.dataframe(df_display, use_container_width=True)

                # Export options
                st.subheader("Export Options")

                col1, col2, col3 = st.columns(3)

                with col1:
                    csv_data = export_to_csv(ohlc_data)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv_data,
                        file_name=f"{ohlc_data.pair}_{ohlc_data.interval}_{ohlc_data.period}.csv",
                        mime="text/csv",
                        key=f"csv_{id(ohlc_data)}"
                    )

                with col2:
                    json_data = export_to_json(ohlc_data)
                    st.download_button(
                        label="📥 Download as JSON",
                        data=json_data,
                        file_name=f"{ohlc_data.pair}_{ohlc_data.interval}_{ohlc_data.period}.json",
                        mime="application/json",
                        key=f"json_{id(ohlc_data)}"
                    )

                with col3:
                    csv_string = export_to_csv_string(ohlc_data, include_header=True)
                    st.code(csv_string, language="csv")
                    st.text(f"👆 Copy the data above (comma-separated format)")

    # Display failed requests
    if response.failed:
        st.markdown("---")
        st.header("❌ Failed Fetches")

        error_df = pd.DataFrame([
            {
                "Pair": err.pair,
                "Interval": err.interval,
                "Period": err.period,
                "Error Type": err.error_type,
                "Error Message": err.error_message
            }
            for err in response.failed
        ])

        st.dataframe(error_df, use_container_width=True)

        # Error details
        st.subheader("Error Details")
        for err in response.failed:
            st.error(f"""
**{err.pair} ({err.interval} / {err.period})**
- Error Type: {err.error_type}
- Message: {err.error_message}
- Time: {err.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
            """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #888;">
    <small>FX-Kline | Powered by yfinance | Data as of """ + get_jst_now().strftime('%Y-%m-%d %H:%M:%S JST') + """</small>
</div>
""", unsafe_allow_html=True)
