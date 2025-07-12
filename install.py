#!/usr/bin/env python3
"""
KasiKash Installation Script
Automates the setup process for the KasiKash application
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_virtual_environment():
    """Create virtual environment"""
    if os.path.exists("venv"):
        print("📁 Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")

def activate_virtual_environment():
    """Activate virtual environment"""
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
    else:  # Unix/Linux/macOS
        activate_script = "venv/bin/activate"
    
    if os.path.exists(activate_script):
        print("✅ Virtual environment ready")
        return True
    else:
        print("❌ Virtual environment not found")
        return False

def install_dependencies():
    """Install Python dependencies"""
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_cmd = "venv/bin/pip"
    
    return run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies")

def create_directories():
    """Create required directories"""
    directories = [
        "static/profile_pics",
        "static/kyc_docs", 
        "flask_session_data"
    ]
    
    print("📁 Creating required directories...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {directory}")

def setup_environment_file():
    """Setup environment file"""
    if os.path.exists(".env"):
        print("📄 .env file already exists")
        return True
    
    if os.path.exists("env_template.txt"):
        shutil.copy("env_template.txt", ".env")
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your configuration")
        return True
    else:
        print("❌ env_template.txt not found")
        return False

def check_database_connection():
    """Check database connection"""
    print("🗄️  Checking database connection...")
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'kasikash_db'),
            user=os.getenv('DB_USER', 'kasikash_user'),
            password=os.getenv('DB_PASSWORD', 'kasikash_password'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("💡 You can use SQLite for development: python init_sqlite_db.py")
        return False

def main():
    """Main installation process"""
    print("🚀 KasiKash Installation Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Activate virtual environment
    if not activate_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("💡 Try activating virtual environment first:")
        if os.name == 'nt':
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup environment file
    setup_environment_file()
    
    # Check database connection
    check_database_connection()
    
    print("\n🎉 Installation completed!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your configuration")
    print("2. Set up Firebase project and download service account key")
    print("3. Initialize database: python init_db.py (PostgreSQL) or python init_sqlite_db.py (SQLite)")
    print("4. Run the application: python main.py")
    print("\n📖 For detailed setup instructions, see SETUP_GUIDE.md")

if __name__ == "__main__":
    main() 