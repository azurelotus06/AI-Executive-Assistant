# Quick Start Guide - Zoom AI Assistant

Get up and running in 5 minutes! 🚀

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] PostgreSQL installed and running
- [ ] OpenAI API key (with GPT-4 access)
- [ ] ElevenLabs API key

## Step 1: Clone and Setup (2 minutes)

```bash
# Clone the repository
git clone <repository-url>
cd zoom-ai-assistant

# Install UV (Python package manager)
pip install uv
```

## Step 2: Backend Setup (2 minutes)

```bash
# Navigate to backend
cd backend

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env
```

**Edit `.env` file and add your API keys:**
```env
OPENAI_API_KEY=sk-...your-key-here...
ELEVENLABS_API_KEY=...your-key-here...
```

## Step 3: Database Setup (1 minute)

```bash
# Still in backend directory
uv run python scripts/startup.py
```

This will:
- Create the database
- Run migrations
- Set up all tables

## Step 4: Start the Backend

```bash
# Start the backend server
uv run uvicorn main:app --reload
```

Backend will be running at: http://localhost:8000

## Step 5: Frontend Setup (in a new terminal)

```bash
# From project root
cd frontend

# Install dependencies
npm install

# Start the frontend
npm start
```

Frontend will open at: http://localhost:3000

## 🎉 You're Ready!

### Test Your Setup

1. Open http://localhost:3000 in your browser
2. Click "Start Session"
3. Allow microphone access
4. Start speaking - you should see transcripts appear
5. The AI will analyze and respond when appropriate

### Quick Test Commands

```bash
# Test backend setup (in a new terminal)
cd backend
uv run python scripts/test_setup.py

# Test the pipeline
curl -X POST http://localhost:8000/api/control/test-pipeline
```

## Common Issues & Solutions

### 1. "API key not configured"
- Make sure you've added your keys to `backend/.env`
- Keys should not have quotes around them

### 2. "Cannot connect to PostgreSQL"
- Start PostgreSQL: `pg_ctl start` or `sudo service postgresql start`
- Check connection string in `.env`

### 3. "Port already in use"
- Backend: Change port in `.env` (APP_PORT=8001)
- Frontend: `npm start -- --port 3001`

### 4. "Module not found" errors
- Backend: Run `uv sync` again
- Frontend: Run `npm install` again

## Next Steps

1. **Test Audio Input**: Click the microphone icon and speak
2. **Manual Prompts**: Type questions in the input field
3. **Review Logs**: Check terminal for backend logs
4. **Customize AI**: Edit prompts in `backend/app/services/ai_service.py`

## Need Help?

- Check full documentation: [README.md](README.md)
- Backend API docs: http://localhost:8000/docs
- Review logs in both terminal windows

Happy meeting! 🎤🤖
