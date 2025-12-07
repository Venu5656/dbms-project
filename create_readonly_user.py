import os
import sys
from sqlalchemy import text
from app import app, db
from models import User  # Import any models needed for table names

def create_readonly_user():
    with app.app_context():
        try:
            # Get database connection
            conn = db.engine.connect()
            
            # Create read-only user (username and password can be customized)
            username = 'readonly_user'
            password = 'readonly_pass_123'  # In production, use a strong password
            
            # Create the user
            conn.execute(text(f"CREATE USER {username} WITH PASSWORD '{password}';"))
            
            # Get all tables in the public schema
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """))
            tables = [row[0] for row in result]
            
            # Grant connect to database (replace 'your_database' with your actual database name)
            conn.execute(text(f"GRANT CONNECT ON DATABASE {db.engine.url.database} TO {username};"))
            
            # Grant usage on schema
            conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {username};"))
            
            # Grant select on all tables and sequences
            for table in tables:
                conn.execute(text(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {username};"))
                conn.execute(text(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {username};"))
            
            # For sequences (if using SERIAL or IDENTITY columns)
            conn.execute(text(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {username};"))
            conn.execute(text(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {username};"))
            
            # Commit the changes
            conn.commit()
            
            print(f"Successfully created read-only user:")
            print(f"Username: {username}")
            print(f"Password: {password}")
            print("\nConnection string template:")
            print(f"postgresql://{username}:{password}@your-db-host:5432/{db.engine.url.database}")
            
            return True
            
        except Exception as e:
            print(f"Error creating read-only user: {str(e)}")
            return False
        finally:
            conn.close()

if __name__ == '__main__':
    print("Creating read-only database user...")
    if create_readonly_user():
        print("Read-only user created successfully!")
    else:
        print("Failed to create read-only user.")
