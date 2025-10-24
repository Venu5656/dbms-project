# Milestone App

A savings and goal tracking application built with Flask and PostgreSQL.

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Venu5656/dbms-project.git
   cd dbms-project
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the database connection string and other settings

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the application:
   ```bash
   flask run
   ```

## Project Structure

- `app/` - Main application package
- `migrations/` - Database migrations (auto-generated)
- `templates/` - HTML templates
- `config.py` - Configuration settings
- `extensions.py` - Flask extensions
- `models.py` - Database models
- `wsgi.py` - WSGI entry point

## License

This project is licensed under the MIT License - see the LICENSE file for details.
