import sys
import os
import time
import threading
import webbrowser
import uvicorn

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))
from app.main import app

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

def main():
    print("=" * 65)
    print("  RETAILMIND-X — RETAIL SALES FORECASTING & INVENTORY INTELLIGENCE")
    print("  Vaidsys Technologies Data Science Internship Project 1")
    print("=" * 65)
    print("\nStarting RetailMind-X Command Center Server...")
    print("Listening at: http://127.0.0.1:8000")
    print("Launching web browser automatically...\n")
    print("Press Ctrl+C or close this window to exit.")
    print("=" * 65 + "\n")
    
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
