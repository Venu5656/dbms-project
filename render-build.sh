#!/usr/bin/env bash
# exit on error
set -o errexit

# Set environment variables
export FLASK_APP=app.py
export PYTHONUNBUFFERED=1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize migrations if not already done
if [ ! -d "migrations" ]; then
  echo "Initializing database migrations..."
  flask db init
fi

# Create and apply migrations
echo "Creating database migrations..."
flask db migrate -m "Initial migration"

echo "Applying database migrations..."
flask db upgrade

# Seed the database
echo "Seeding database..."
python seeds.py

echo "Build completed successfully!"
