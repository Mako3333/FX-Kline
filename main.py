#!/usr/bin/env python3
"""
Main entry point for FX-Kline

Run this with: python main.py
Or use: streamlit run src/fx_kline/ui/streamlit_app.py
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run Streamlit app"""
    app_path = Path(__file__).parent / "src" / "fx_kline" / "ui" / "streamlit_app.py"

    if not app_path.exists():
        print(f"Error: Streamlit app not found at {app_path}")
        sys.exit(1)

    # Run streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


if __name__ == "__main__":
    main()
