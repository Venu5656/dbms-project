import os
import re
from decimal import Decimal
from urllib.parse import urlparse, urlunparse


class Config:
    # Database configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Get the database URL from environment variable
        database_url = os.environ.get("DATABASE_URL", "sqlite:///local.db")
        
        # If using SQLite (development)
        if database_url.startswith('sqlite'):
            return database_url
            
        # If using PostgreSQL (production on Render)
        if database_url.startswith('postgres://'):
            # Convert postgres:// to postgresql:// for SQLAlchemy
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
            # Add SSL requirement for Render's external connections
            if 'localhost' not in database_url and '127.0.0.1' not in database_url:
                if '?' in database_url:
                    database_url += '&sslmode=require'
                else:
                    database_url += '?sslmode=require'
        
        return database_url

    # Round-up configuration
    ROUND_UP_MODE = os.environ.get("ROUND_UP_MODE", "fixed")
    FIXED_ROUND_UP_STEP = Decimal(os.environ.get("FIXED_ROUND_UP_STEP", "0.50"))
    MIN_ROUND_UP_FLOOR = Decimal(os.environ.get("MIN_ROUND_UP_FLOOR", "0.00"))

    # Pace bonus mapping (Conservative/Moderate/Aggressive)
    PACE_BONUS = {
        "Conservative": Decimal(os.environ.get("PACE_BONUS_CONSERVATIVE", "0.50")),
        "Moderate": Decimal(os.environ.get("PACE_BONUS_MODERATE", "1.00")),
        "Aggressive": Decimal(os.environ.get("PACE_BONUS_AGGRESSIVE", "1.50")),
    }

    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")


# Create instance of config
config = Config()
