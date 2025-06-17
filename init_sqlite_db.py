import sys
import os

# Add current directory to path so we can import support
sys.path.append('.')
from support import init_database

if __name__ == "__main__":
    print("Initializing SQLite Database...")
    print("=" * 40)
    
    if init_database():
        print("🎉 SQLite database initialized successfully!")
        print("Your app should now work without PostgreSQL connection issues.")
    else:
        print("❌ Failed to initialize database.") 