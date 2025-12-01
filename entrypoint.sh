#!/bin/bash
set -e

# Check if we are in development mode
if [ "$FLASK_ENV" = "development" ]; then
    echo "Environment: development"
    
    # Check if database exists
    if [ ! -f "wordlewise.db" ]; then
        echo "Database file not found. Initializing and seeding database..."
        uv run scripts/seed_db.py --force
    else
        echo "Database file exists. Skipping automatic seeding."
    fi
else
    echo "Environment: production (or other). Skipping automatic seeding."
fi

# Execute the CMD passed to the container
exec "$@"
