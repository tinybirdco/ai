#!/usr/bin/env python3
"""
Server script for running the Agno Slack bot
"""
import os
import sys
from http.server import HTTPServer

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.slack import handler

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 Starting Agno Slack bot server on port {port}")
    print(f"📡 Server ready to receive Slack events...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.server_close()
