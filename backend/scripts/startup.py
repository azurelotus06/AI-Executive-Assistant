"""Startup script to initialize the database and run migrations"""
import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.models.database import engine, Base
from app.core.config import settings


def create_database():
    """Create database if it doesn't exist"""
    # For PostgreSQL, we need to connect to the default 'postgres' database first
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    # Parse database URL
    db_url = settings.database_url
    # Extract database name from URL
    db_name = db_url.split('/')[-1].split('?')[0]
    
    # Connect to PostgreSQL server
    conn_str = db_url.rsplit('/', 1)[0] + '/postgres'
    
    try:
        # Connect to default database
        conn = psycopg2.connect(conn_str)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created successfully")
        else:
            print(f"Database '{db_name}' already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        print("Make sure PostgreSQL is running and accessible")
        sys.exit(1)


def init_alembic():
    """Initialize Alembic if not already initialized"""
    alembic_dir = Path(__file__).parent.parent / "alembic"
    versions_dir = alembic_dir / "versions"
    
    if not versions_dir.exists():
        versions_dir.mkdir(parents=True, exist_ok=True)
        print("Created alembic/versions directory")


def run_migrations():
    """Run database migrations"""
    try:
        # Change to backend directory
        os.chdir(Path(__file__).parent.parent)
        
        # Check if there are any existing migrations
        versions_dir = Path("alembic/versions")
        migration_files = list(versions_dir.glob("*.py"))
        
        if not migration_files:
            # Create initial migration using virtual environment's Python
            print("Creating initial migration...")
            subprocess.run([".venv/Scripts/python", "-m", "alembic", "revision", "--autogenerate", "-m", "Initial migration"], check=True)
        
        # Run migrations using virtual environment's Python
        print("Running migrations...")
        subprocess.run([".venv/Scripts/python", "-m", "alembic", "upgrade", "head"], check=True)
        print("Migrations completed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)


def main():
    """Main startup function"""
    print("Starting Zoom AI Assistant Backend Setup...")
    
    # Create database if needed
    create_database()
    
    # Initialize Alembic
    init_alembic()
    
    # Run migrations
    run_migrations()
    
    print("\nSetup completed successfully!")
    print("\nYou can now start the backend server with:")
    print("  cd backend")
    print("  uv run uvicorn main:app --reload")


if __name__ == "__main__":
    main()
