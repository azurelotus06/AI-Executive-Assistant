# Real-Time AI Executive Assistant for Zoom Meetings

An intelligent AI assistant that actively participates in Zoom meetings by listening, analyzing conversations in real-time using GPT-4, and providing strategic insights via natural text-to-speech.

## 🎯 Overview

This project creates an AI-powered executive assistant that:
- **Listens** to Zoom meetings in real-time
- **Analyzes** conversations using GPT-4 for strategic insights
- **Speaks** naturally using ElevenLabs TTS when appropriate
- **Provides** executive-level insights and recommendations

## 🚀 Key Features

### ✅ Real-Time Audio Processing
- Captures Zoom audio via MeetingBaaS integration
- Automatic bot joins meetings with provided URL
- Converts speech to text using OpenAI Whisper
- Implements Voice Activity Detection (VAD) for efficient processing
- Speaker identification and tracking

### ✅ AI-Powered Insights
- Context-aware analysis with GPT-4
- Executive-style prompt engineering for professional responses
- Maintains conversation history for contextual understanding
- Identifies key topics, risks, and opportunities

### ✅ Natural Voice Interaction
- Human-like speech synthesis using ElevenLabs
- Speaks only during natural pauses (non-intrusive)
- Configurable voice settings for different scenarios

### ✅ User Control
- Real-time mute/unmute functionality
- Pause/resume AI analysis
- Manual prompt injection
- Emergency stop feature

## 🛠️ Tech Stack

- **Frontend**: React with TypeScript
- **Backend**: Python with FastAPI
- **Database**: PostgreSQL
- **Package Management**: UV (Python), npm (JavaScript)
- **APIs**: 
  - OpenAI (Whisper + GPT-4)
  - ElevenLabs (Text-to-Speech)
  - MeetingBaaS (Zoom integration)
- **Real-time Communication**: WebSockets
- **Audio Processing**: WebRTC VAD, librosa, sounddevice

## 📋 Prerequisites

- Node.js 16+ and npm
- Python 3.9+
- PostgreSQL 12+
- FFmpeg
- Valid API keys for:
  - OpenAI (with GPT-4 access)
  - ElevenLabs
  - MeetingBaaS (for Zoom integration)
- Devtunnel or ngrok for webhook endpoints

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/zoom-ai-assistant.git
cd zoom-ai-assistant
```

### 2. Backend Setup

```bash
# Install UV package manager
pip install uv

# Navigate to backend
cd backend

# Install dependencies
uv sync

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Set up database
uv run python scripts/startup.py

# Start the backend server
uv run uvicorn main:app --reload
```

### 3. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

## 🔑 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Required
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# MeetingBaaS Configuration (Required for Zoom integration)
MEETINGBAAS_API_KEY=your_meetingbaas_api_key
DEVTUNNEL_HOST=your-devtunnel-host.devtunnels.ms

# Optional
ZOOM_MEETING_ID=your_meeting_id
ZOOM_PASSCODE=your_passcode
DATABASE_URL=postgresql://user:password@localhost:5432/zoom_assistant

# AI Settings
AI_MODEL=gpt-4
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=150

# TTS Settings
TTS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

## 📱 Usage

1. **Start Both Servers**
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:3000`

2. **Set up Devtunnel (for MeetingBaaS webhooks)**
   ```bash
   # Install devtunnel
   winget install Microsoft.devtunnel
   
   # Login and create tunnel
   devtunnel user login
   devtunnel create --allow-anonymous
   devtunnel port create -p 8000
   devtunnel host
   
   # Copy the URL and set DEVTUNNEL_HOST in .env
   ```

3. **Connect to a Meeting**
   - Enter the Zoom meeting URL in the Meeting Integration panel
   - Click "Join Meeting" to send the AI bot
   - Admit the bot when it appears in the waiting room
   - The AI will begin listening and analyzing

3. **During the Meeting**
   - The AI listens continuously
   - Transcripts appear in real-time
   - AI speaks when it has valuable insights
   - Use controls to mute/pause as needed

4. **Manual Interaction**
   - Type custom prompts in the input field
   - AI will respond based on conversation context

## 🏗️ Architecture

```
project/
├── frontend/               # React TypeScript application
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API and WebSocket services
│   │   └── types/         # TypeScript definitions
│   └── public/            # Static assets
│
├── backend/               # FastAPI Python application
│   ├── app/
│   │   ├── api/          # REST API endpoints
│   │   ├── core/         # Core configuration
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   ├── alembic/          # Database migrations
│   └── scripts/          # Utility scripts
│
└── docs/                 # Additional documentation
```

## 🔄 Data Flow

1. **Meeting Join** → Bot joins via MeetingBaaS API
2. **Audio Stream** → Real-time WebSocket from meeting
3. **Audio Processing** → VAD + Speaker identification
4. **Speech-to-Text** → OpenAI Whisper (local)
5. **AI Analysis** → GPT-4 Context Analysis
6. **Decision Making** → Should AI speak?
7. **Text-to-Speech** → ElevenLabs API
8. **Audio Output** → Through meeting bot

## 🧪 Testing

### Backend Tests
```bash
cd backend
uv run pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### End-to-End Pipeline Test
```bash
# With backend running
curl -X POST http://localhost:8000/api/control/test-pipeline
```

## 📊 Performance Considerations

- **Audio Chunk Duration**: 1 second (configurable)
- **AI Response Cooldown**: 30 seconds minimum
- **Context Window**: Last 10 messages
- **WebSocket Reconnection**: Automatic with 5s interval

## 🔒 Security

- API keys stored in environment variables
- CORS configured for local development
- WebSocket connections validated
- Database connections use SSL in production

## 🐛 Troubleshooting

### Common Issues

1. **Audio Not Capturing**
   - Check microphone permissions
   - Verify FFmpeg installation
   - Test with `api/audio/test-recording`

2. **AI Not Responding**
   - Verify OpenAI API key and GPT-4 access
   - Check conversation context window
   - Review AI pause status

3. **No Speech Output**
   - Confirm ElevenLabs API key
   - Check TTS mute status
   - Verify voice ID configuration

## 🚀 Deployment

### Ngrok Deployment

To expose your local development environment using ngrok:

1. **Install ngrok** (if not already installed):
   ```bash
   # Download from https://ngrok.com/download
   # Or use the included ngrok.exe on Windows
   ```

2. **Backend Deployment**:
   ```bash
   cd backend
   # Start backend server first
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   
   # In another terminal, expose backend
   ngrok http 8000
   ```
   
   Note the ngrok URL (e.g., `https://abc123.ngrok-free.app`) and update:
   - Frontend's API_BASE_URL in `src/services/api.ts`
   - Any webhook URLs in your Zoom integration

3. **Frontend Deployment**:
   ```bash
   cd frontend
   # Build production version
   npm run build
   
   # Serve frontend
   npx serve -s build -l 3000
   
   # In another terminal, expose frontend
   ngrok http 3000
   ```

4. **Access the Application**:
   - Frontend: Use the ngrok URL for port 3000
   - Backend: Use the ngrok URL for port 8000 for API calls

### Production Considerations

1. Use environment-specific configurations
2. Enable SSL/TLS for WebSocket connections
3. Implement proper authentication
4. Set up monitoring and logging
5. Configure auto-scaling for high load

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API logs for debugging

---

Built with ❤️ for enhancing meeting productivity with AI
