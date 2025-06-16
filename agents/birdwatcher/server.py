#!/usr/bin/env python3
"""
Server script for running the Agno Slack bot
"""
import os
import sys
from aiohttp import web

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.slack import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Agno Slack bot server on port {port}")
    print(f"📡 Server ready to receive Slack events...")

    try:
        web.run_app(app, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("\nServer stopped")
