#!/usr/bin/env python3
"""
Grid Trading Bot UI Launcher

Launch the web-based configuration interface for the Grid Trading Bot.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

def main():
    """Launch the Grid Trading Bot UI."""
    try:
        from web_ui.app import GridBotUI

        print("Starting Grid Trading Bot Configuration UI...")
        print("Features:")
        print("   * Visual grid configuration")
        print("   * Real-time price integration")
        print("   * Interactive parameter adjustment")
        print("   * Configuration validation")
        print("   * Export/import configurations")
        print("   * Backtest preview")
        print()

        ui = GridBotUI()
        ui.run(debug=True, port=8050)

    except ImportError as e:
        print("Missing dependencies for Web UI!")
        print("Please install the required packages:")
        print("   pip install flask dash dash-bootstrap-components")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
