# Business Club Management System

A comprehensive business club management system providing operational control through integrated modules for member administration, financial management, and performance tracking.

## Features

- Member Management
- Financial Planning
- Reports & KPIs
- Scenario Planning
- Data Management
- ML-driven Forecasting
- Multi-country Support (Netherlands, Belgium, Germany)

## Technology Stack

- Python (Streamlit)
- SQLAlchemy ORM
- PostgreSQL Database
- Machine Learning Models
- Plotly for Visualizations

## Public Access via GitHub Codespaces

1. Quick Start:
   - Navigate to the GitHub repository
   - Click the green "Code" button
   - Select "Open in Codespaces"
   - Wait for the environment to build (this includes automatic database initialization)
   - The application will automatically start on port 5000

2. Required Environment Variables:
   Create a `.env` file or set up GitHub secrets with:
   ```
   DATABASE_URL=postgresql://user:password@host:port/dbname
   PGUSER=your_db_user
   PGPASSWORD=your_db_password
   PGHOST=localhost
   PGPORT=5432
   PGDATABASE=your_db_name
   ```

3. Access Points:
   - The application automatically runs on port 5000
   - Access via the "Ports" tab in Codespaces
   - Or click the "Open in Browser" button
   - The application will be available at http://localhost:5000

4. Security Notes:
   - Never commit sensitive data or .env files
   - Use GitHub secrets for sensitive information
   - Keep your database credentials secure

## Development with GitHub Codespaces

1. Open in Codespaces:
   - Click the "Code" button on the repository
   - Select "Open with Codespaces"
   - Click "New codespace"

2. Environment Setup (Automatic):
   - Python 3.11 installation
   - Dependencies installation
   - PostgreSQL setup
   - Database initialization
   - Application startup
   - Code formatting and linting setup

3. Access the Application:
   - The application automatically starts on port 5000
   - Click the "Open in Browser" button or use the Ports tab

4. Development:
   - Make changes to the code
   - The application will automatically reload
   - Use the integrated terminal for commands
   - Use the integrated VS Code for editing
   - Code formatting on save is enabled

## Local Installation

1. Clone the repository:
```bash
git clone [repository-url]
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
DATABASE_URL=your_database_url
```

4. Run the application:
```bash
streamlit run main.py
```

[Rest of README.md content remains the same...]
