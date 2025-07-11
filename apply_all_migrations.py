import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MIGRATIONS_DIR = "migrations"

def is_migration_file(filename):
    """Check if a file is a migration file (.py or .sql)."""
    return (
        (filename.endswith(".py") or filename.endswith(".sql"))
        and not filename.startswith("__")
        and filename != "apply_all_migrations.py"
    )

def apply_sql_migration(filepath, db_name, db_user, db_password):
    """Apply an SQL migration script using psql."""
    print(f"Applying SQL migration: {os.path.basename(filepath)}")
    try:
        # Ensure the PGPASSWORD environment variable is set for the subprocess
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        command = [
            "psql",
            "-U", db_user,
            "-d", db_name,
            "-h", "localhost", # Or your db host
            "-f", filepath
        ]
        
        # Using shell=True for Windows compatibility with psql if it's not in PATH
        # but better to ensure psql is in PATH.
        # For cross-platform, better to rely on PATH.
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            env=env
        )
        print("✅ SQL Migration applied successfully.")
        return True
    except FileNotFoundError:
        print("❌ Error: 'psql' command not found.")
        print("Please ensure PostgreSQL client tools are installed and in your system's PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error applying SQL migration {os.path.basename(filepath)}.")
        print(f"   psql stdout: {e.stdout}")
        print(f"   psql stderr: {e.stderr}")
        return False

def apply_python_migration(filepath):
    """Apply a Python migration script."""
    print(f"Running Python migration: {os.path.basename(filepath)}")
    result = subprocess.run([sys.executable, filepath], text=True)
    if result.returncode != 0:
        print(f"❌ Python migration {os.path.basename(filepath)} failed.")
        return False
    else:
        print(f"✅ Python migration {os.path.basename(filepath)} completed successfully.")
        return True

def main():
    """Main function to find and apply all database migrations."""
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    if not all([db_name, db_user, db_password]):
        print("❌ Error: Database credentials (DB_NAME, DB_USER, DB_PASSWORD) not found in .env file.")
        sys.exit(1)

    try:
        migration_files = sorted(
            f for f in os.listdir(MIGRATIONS_DIR) if is_migration_file(f)
        )
    except FileNotFoundError:
        print(f"❌ Error: Migrations directory '{MIGRATIONS_DIR}' not found.")
        sys.exit(1)

    if not migration_files:
        print("No migration scripts found.")
        return

    print("Found migration files:")
    for script in migration_files:
        print(f" - {script}")

    for filename in migration_files:
        filepath = os.path.join(MIGRATIONS_DIR, filename)
        print(f"\n=== Processing {filename} ===")

        if filename.endswith(".sql"):
            success = apply_sql_migration(filepath, db_name, db_user, db_password)
        elif filename.endswith(".py"):
            success = apply_python_migration(filepath)
        else:
            print(f"❓ Skipping unsupported file type: {filename}")
            continue

        if not success:
            print(f"\nStopping further migrations due to failure in {filename}.")
            break

if __name__ == "__main__":
    main()