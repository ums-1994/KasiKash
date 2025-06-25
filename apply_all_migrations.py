import os
import subprocess
import sys

MIGRATIONS_DIR = "migrations"

def is_migration_script(filename):
    return (
        filename.endswith(".py")
        and filename != "__init__.py"
        and filename != "apply_all_migrations.py"
    )

def main():
    migration_scripts = sorted(
        f for f in os.listdir(MIGRATIONS_DIR) if is_migration_script(f)
    )
    print("Found migration scripts:")
    for script in migration_scripts:
        print(f" - {script}")

    for script in migration_scripts:
        script_path = os.path.join(MIGRATIONS_DIR, script)
        print(f"\n=== Running {script} ===")
        result = subprocess.run([sys.executable, script_path])
        if result.returncode != 0:
            print(f"❌ Migration {script} failed. Stopping further migrations.")
            break
        else:
            print(f"✅ {script} completed successfully.")

if __name__ == "__main__":
    main()