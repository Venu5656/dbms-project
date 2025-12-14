# Milestone - Smart Savings Goal Tracker

A full-stack web application for managing savings goals with automated rules and progress tracking. Built with Flask, PostgreSQL, and modern JavaScript.

## Features

- 🎯 **Goal Management**: Create, edit, and delete savings goals with custom images
- 💰 **Automated Savings Rules**: Four rule types (Recurring, Habit Reward, Guilty Pleasure Tax, Round-up)
- 📊 **Progress Tracking**: Visual progress bars and real-time statistics
- 🎨 **Modern UI**: Dark theme with animations and responsive design
- 🔐 **Secure Authentication**: Session-based auth with password hashing
- 📸 **Image Uploads**: Upload custom images for your goals

## Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Git

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Venu5656/dbms-project.git
cd dbms-project
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE dbms_project;

-- Create user (optional)
CREATE USER app_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE dbms_project TO app_user;
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
DATABASE_URL=postgresql://app_user:your_password@localhost:5432/dbms_project
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
```

### 6. Run the Application

```bash
export DATABASE_URL="postgresql://app_user:your_password@localhost:5432/dbms_project"
export FLASK_APP=app.py
export FLASK_ENV=development

flask run
```

The app will be available at: **http://127.0.0.1:5000**

## Default Demo Account

- **Username:** `gowrisankar`
- **Password:** `pass`

## Project Structure

```
milestone-app/
├── app.py              # Main Flask application
├── models.py           # Database models
├── extensions.py       # Flask extensions
├── config.py          # Configuration
├── middleware.py      # Activity logging
├── requirements.txt   # Python dependencies
├── runtime.txt       # Python version
├── templates/
│   ├── index.html    # Dashboard
│   ├── login.html    # Login page
│   ├── register.html # Registration page
│   ├── home.html     # Landing page
│   └── goal.html     # Goal detail page
└── static/
    └── uploads/      # User-uploaded images
```

## Usage

1. **Register/Login**: Create an account or use demo credentials
2. **Create Goal**: Click "Create new goal", fill details, optionally upload image
3. **Add Rules**: Click "Create savings rule", choose type, configure settings
4. **Track Progress**: View dashboard with goals, rules, and statistics
5. **Edit/Delete**: Use 3-dots menu on goal cards to modify or remove

## Tech Stack

**Backend:**
- Flask 3.0
- PostgreSQL
- SQLAlchemy ORM
- Werkzeug (security)

**Frontend:**
- Vanilla JavaScript
- Modern CSS (animations, gradients)
- Responsive design

**Deployment:**
- Railway (production)
- Gunicorn (WSGI server)

## Deployment

### Railway

1. Create account at [railway.app](https://railway.app)
2. Create new project and add PostgreSQL
3. Connect GitHub repository
4. Set environment variables:
   - `DATABASE_URL` (from Railway Postgres)
   - `SECRET_KEY`
   - `PYTHON_VERSION=3.11`
5. Deploy

## Contributing

This is a student project. Feel free to fork and modify for your own use.

## License

MIT License
