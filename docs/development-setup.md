# ExamNexus — Development Setup

ExamNexus uses a React/Vite frontend, Flask backend, and PostgreSQL database.

## Technology Stack

| Layer      | Technologies                                                      |
| ---------- | ----------------------------------------------------------------- |
| Frontend   | React 19, Vite, Tailwind CSS, Lucide React                        |
| Backend    | Python, Flask, Flask-SQLAlchemy, Flask-CORS, Flask-Migrate, PyJWT |
| Database   | PostgreSQL, psycopg / psycopg2-binary                             |
| Testing    | pytest                                                            |
| Supporting | QRCode, Pillow                                                    |

## Prerequisites

Install:

* Python
* Node.js and npm
* PostgreSQL
* Git

## Project Structure

```text
ExamNexus/
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── scripts/
│   ├── tests/
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
└── docs/
```

## Backend Setup

```bash
cd backend
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables:

```env
DATABASE_URL=
JWT_SECRET_KEY=
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=
```

Start the backend:

```bash
python run.py
```

The application is created through the Flask application factory.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Configure the API endpoint:

```env
VITE_API_BASE_URL=
```

Production build:

```bash
npm run build
```

Additional commands:

```bash
npm run lint
npm run preview
```

## Database

ExamNexus uses PostgreSQL with Flask-Migrate/Alembic for schema migrations.

Database access is configured through:

```env
DATABASE_URL=
```

## Testing

Backend tests use pytest:

```bash
cd backend
pytest
```

Detailed verification evidence is documented in [`testing-and-verification.md`](testing-and-verification.md).

## Development Flow

```text
PostgreSQL
    ↓
Flask Backend
    ↓
REST API
    ↓
React + Vite Frontend
```

The frontend communicates with the backend through `VITE_API_BASE_URL`.

## Security

* Never commit `.env` files or secrets.
* Keep database credentials outside source control.
* Use a strong `JWT_SECRET_KEY`.
* Use environment-specific configuration for production.

## Local Verification Checklist

* [ ] PostgreSQL running
* [ ] Backend environment configured
* [ ] Backend dependencies installed
* [ ] Backend starts successfully
* [ ] Frontend dependencies installed
* [ ] Frontend starts successfully
* [ ] API base URL configured
* [ ] Backend tests pass
* [ ] Frontend build succeeds