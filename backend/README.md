# PillPulse AI Backend

This is the FastAPI backend for the PillPulse AI healthcare assistant.

## Requirements

- Python 3.8+
- PostgreSQL
- Ollama running locally with the `llama3:8b` model

## Setup Database

1. Ensure PostgreSQL is running and you have a database created.
2. You can set the connection string via the `DATABASE_URL` environment variable. By default, it tries to connect to:
   `postgresql://postgres:postgres@localhost:5432/pillpulse`

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

Run the backend server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

## API Endpoints

- `POST /api/chat`: Chat with the PillPulse AI assistant.
- `POST /api/symptoms/start`: Start a new symptom check session.
- `POST /api/symptoms/step`: Submit a symptom step answer.
- `POST /api/symptoms/analyze`: Analyze all collected symptoms for a session and get risk level, conditions, and recommendations.

### Medication Adherence API

- `POST /users/register`: Register user.
- `POST /medicines/add`: Add medication schedule.
- `POST /medicines/confirm-dose`: Patient confirms medication intake. recorded in adherence_logs.
- `GET /medicines/today`: Return today's medication schedule and status.
- `GET /medicines/remaining`: Return remaining pills and predicted refill date.
- `GET /adherence/score`: Returns adherence score percentage.
- `GET /adherence/missed`: Returns count and details of missed medication doses.

## Automation Setup (n8n)

The application utilizes n8n for scheduled automation triggers (Cron Workflows):
1. **Medication Reminder**: Fetches `/medicines/today` and checks if current time matches scheduled dose.
2. **Missed Dose Detection**: Fetches `/adherence/missed`. Triggers Caregiver Alert if missed doses >= 3.
3. **Refill Prediction**: Fetches `/medicines/remaining`. Triggers alert if remaining days < 5.

Ensure that [Ollama](https://ollama.ai) is running locally on port 11434 before making API requests!
