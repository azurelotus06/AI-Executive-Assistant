# Zoom AI Assistant Backend

Real-Time AI Executive Assistant for Zoom Meetings - Backend Service

## Overview

This backend service provides the core functionality for the Zoom AI Assistant, including:
- Real-time audio processing and speech-to-text conversion using OpenAI Whisper
- AI-powered conversation analysis using GPT-4
- Natural text-to-speech synthesis using ElevenLabs
- WebSocket support for real-time communication
- RESTful API endpoints for control and configuration

## Architecture

```
backend/
├── app/
│   ├── api/          # API routes and endpoints
│   ├── core/         # Core configuration and utilities
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic schemas for validation
│   └── services/     # Business logic services
├── alembic/          # Database migrations
├── scripts/          # Utility scripts
└── main.py          # Application entry point
```

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- UV package manager
- FFmpeg (for audio processing)
- Valid API keys for:
  - OpenAI (GPT-4 and Whisper)
  - ElevenLabs (Text-to-Speech)

## Installation

1. **Install UV package manager:**
   ```bash
   pip install uv
   ```

2. **Install dependencies:**
   ```bash
   cd backend
   uv sync
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Install system dependencies:**
   
   **Windows:**
   ```bash
   # Install FFmpeg
   # Download from https://ffmpeg.org/download.html
   # Add to PATH
   
   # Install PortAudio (for PyAudio)
   # Download from http://www.portaudio.com/download.html
   ```
   
   **macOS:**
   ```bash
   brew install ffmpeg portaudio
   ```
   
   **Linux:**
   ```bash
   sudo apt-get update
   sudo apt-get install ffmpeg portaudio19-dev
   ```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory with the following:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Optional Zoom Configuration
ZOOM_MEETING_ID=your_zoom_meeting_id
ZOOM_PASSCODE=your_zoom_passcode

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/zoom_assistant

# Optional Settings (defaults shown)
AI_MODEL=gpt-4
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=150
TTS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

### Database Setup

1. **Ensure PostgreSQL is running:**
   ```bash
   # Check PostgreSQL status
   pg_ctl status
   
   # Start PostgreSQL if needed
   pg_ctl start
   ```

2. **Run the startup script:**
   ```bash
   cd backend
   uv run python scripts/startup.py
   ```

   This script will:
   - Create the database if it doesn't exist
   - Initialize Alembic for migrations
   - Run all database migrations

## Running the Application

### Development Mode

```bash
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Ngrok Deployment

To expose your backend using ngrok:

1. First start the backend server:
```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

2. In another terminal, expose the backend:
```bash
ngrok http 8000
```

3. Note the ngrok URL (e.g., `https://abc123.ngrok-free.app`) and:
   - Update frontend's API_BASE_URL in `src/services/api.ts`
   - Update any webhook URLs in your Zoom integration
   - Share this URL for external access

4. For persistent subdomains (optional):
```bash
ngrok http 8000 --subdomain your-subdomain
```

5. To monitor requests:
```bash
ngrok http 8000 --log=stdout
```

## API Documentation

Once the server is running, you can access:
- Interactive API documentation: http://localhost:8000/docs
- Alternative API documentation: http://localhost:8000/redoc

### Key Endpoints

#### Audio Processing
- `POST /api/audio/process-chunk` - Process audio chunk
- `POST /api/audio/upload-audio` - Upload and process audio file
- `POST /api/audio/start-recording` - Start microphone recording
- `POST /api/audio/stop-recording` - Stop microphone recording
- `GET /api/audio/status` - Get audio processor status

#### AI Analysis
- `POST /api/ai/analyze` - Analyze conversation transcript
- `POST /api/ai/manual-prompt` - Send manual prompt to AI
- `GET /api/ai/conversation-history` - Get conversation history
- `GET /api/ai/status` - Get AI service status

#### Control
- `POST /api/control/start-session` - Start AI assistant session
- `POST /api/control/stop-session` - Stop AI assistant session
- `GET /api/control/system-status` - Get system status
- `POST /api/control/test-pipeline` - Test the complete pipeline

### WebSocket Connection

Connect to `ws://localhost:8000/ws` for real-time communication.

Message types:
- `audio_chunk` - Send audio data for processing
- `transcript_update` - Receive transcription updates
- `ai_response` - Receive AI responses with TTS audio
- `control` - Send control commands (mute, pause, etc.)

## Testing

### Run Unit Tests

```bash
cd backend
uv run pytest
```

### Test the Pipeline

```bash
# Test individual services
curl -X POST http://localhost:8000/api/control/test-pipeline

# Test AI analysis
curl -X POST http://localhost:8000/api/ai/test-analysis \
  -H "Content-Type: application/json" \
  -d '{"test_transcript": "Let's discuss our Q4 revenue targets"}'
```

## Troubleshooting

### Common Issues

1. **PyAudio Installation Fails**
   - Ensure PortAudio is installed on your system
   - On Windows, you may need to install PyAudio wheel manually

2. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Ensure database user has proper permissions

3. **API Key Errors**
   - Verify API keys are correctly set in .env
   - Check API key permissions and quotas

4. **Audio Processing Issues**
   - Ensure FFmpeg is installed and in PATH
   - Check audio sample rate settings
   - Verify microphone permissions

### Debug Mode

Enable debug logging by setting in .env:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

## Development

### Code Structure

- **Services**: Business logic is separated into service classes
  - `AudioProcessor`: Handles audio processing and speech-to-text
  - `AIService`: Manages AI conversation analysis
  - `TTSService`: Handles text-to-speech generation

- **API Routes**: FastAPI routers organize endpoints by domain
  - `/api/audio/*` - Audio-related endpoints
  - `/api/ai/*` - AI analysis endpoints
  - `/api/control/*` - System control endpoints

- **WebSocket**: Real-time communication managed by `WebSocketManager`

### Adding New Features

1. Create new service in `app/services/`
2. Add API routes in `app/api/routes/`
3. Define schemas in `app/schemas/`
4. Update WebSocket handlers if needed

### Database Migrations

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Performance Optimization

1. **Audio Processing**
   - Adjust `AUDIO_CHUNK_DURATION` for latency vs accuracy trade-off
   - Use `AUDIO_SILENCE_THRESHOLD` to filter noise

2. **AI Response Time**
   - Adjust `AI_CONTEXT_WINDOW` to limit conversation history
   - Use streaming TTS for faster audio generation

3. **Database**
   - Enable connection pooling (configured by default)
   - Add indexes for frequently queried fields

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **CORS**: Configure allowed origins in production
3. **Database**: Use strong passwords and SSL connections
4. **WebSocket**: Implement authentication for production use

## License

MIT License - See LICENSE file for details
