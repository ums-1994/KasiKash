#!/usr/bin/env python3
"""
KasiKash Application Startup Script
This script runs the KasiKash application and displays the correct URLs.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("🚀 KasiKash Application Launcher")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("backend").exists():
        print("❌ Error: Please run this script from the KasiKash project root directory")
        print("   Current directory:", os.getcwd())
        sys.exit(1)
    
    # Set environment variables if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Found .env file - environment variables will be loaded")
    else:
        print("⚠️  No .env file found - make sure your database configuration is set up")
    
    print("\n📋 Starting KasiKash application...")
    print("=" * 60)
    
    try:
        # Run the main application
        subprocess.run([sys.executable, "-m", "backend.main"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 