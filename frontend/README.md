# Real-Time AI Assistant - Frontend

This is the frontend application for the Real-Time AI Executive Assistant for Zoom Meetings. Built with React, TypeScript, and Tailwind CSS, it provides a modern, responsive interface for interacting with the AI assistant during meetings.

## 🎨 Features

- **Real-time Audio Visualization**: Visual feedback of audio levels and recording status
- **Live Transcription Display**: See speech-to-text results as they happen
- **AI Response History**: Track all AI-generated insights and responses
- **Interactive Controls**: Mute/unmute, manual prompts, and session management
- **System Status Monitoring**: Real-time status of all backend services
- **WebSocket Communication**: Low-latency bidirectional communication with backend

## 🛠️ Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **WebSocket** for real-time communication
- **React Icons** for UI icons
- **React Hot Toast** for notifications
- **Framer Motion** for animations

## 📋 Prerequisites

- Node.js 16+ and npm
- Backend server running on `https://bold-chow-trivially.ngrok-free.app`

## 🔧 Installation

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file (if needed for any frontend-specific configs):
```bash
# Currently, all API endpoints are configured to use localhost:8000
# Modify src/services/api.ts if you need different endpoints
```

## 🚀 Development

Start the development server:
```bash
npm start
```

The app will be available at `http://localhost:3000`

## 🏗️ Project Structure

```
src/
├── components/           # React components
│   ├── Header.tsx       # App header with connection controls
│   ├── AudioVisualizer.tsx # Real-time audio level visualization
│   ├── ConversationPanel.tsx # Transcription and AI response display
│   ├── ControlPanel.tsx # Manual controls and text input
│   └── StatusPanel.tsx  # System status indicators
├── hooks/               # Custom React hooks
│   └── useAudioRecorder.ts # Audio recording and streaming logic
├── services/            # API and WebSocket services
│   └── api.ts          # Backend API client
├── App.tsx             # Main application component
├── App.css             # Global styles
└── index.css           # Tailwind CSS imports
```

## 🎯 Key Components

### Header
- Connection status indicator
- Connect/disconnect button
- Mute/unmute toggle
- Export conversation history

### AudioVisualizer
- Real-time audio level meter
- Recording status indicator
- Visual feedback during speech

### ConversationPanel
- Displays transcribed text
- Shows AI responses with timestamps
- Auto-scrolls to latest messages
- Differentiates between user and AI messages

### ControlPanel
- Manual text input for direct AI queries
- Send button for submitting prompts
- Keyboard shortcuts (Enter to send)

### StatusPanel
- WebSocket connection status
- Audio recording status
- AI service availability
- TTS service status

## 🔌 API Integration

The frontend communicates with the backend through:

### REST API Endpoints
- Audio processing endpoints
- AI analysis endpoints
- System control endpoints
- Conversation history management

### WebSocket Events
- `transcription`: Receives real-time transcriptions
- `ai_response`: Receives AI-generated responses
- `status_update`: System status changes
- `error`: Error notifications

## 🎨 Styling

The app uses Tailwind CSS with a dark theme:
- Primary colors: Blue accents (#3B82F6)
- Background: Dark grays (#111827, #1F2937)
- Text: White and gray variations
- Responsive design for various screen sizes

## 📦 Building for Production

Create an optimized production build:
```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

## 🧪 Testing

Run the test suite:
```bash
npm test
```

Run tests in watch mode:
```bash
npm test -- --watch
```

## 🔧 Configuration

### API Endpoints
Modify `src/services/api.ts` to change backend URLs:
```typescript
const API_BASE_URL = 'https://bold-chow-trivially.ngrok-free.app';
const WS_URL = 'ws://bold-chow-trivially.ngrok-free.app/ws';
```

### Audio Settings
Adjust audio recording parameters in `src/hooks/useAudioRecorder.ts`:
- Sample rate: 16000 Hz (default)
- Chunk duration: 100ms
- Audio format: 16-bit PCM

## 🚀 Deployment

### Development Deployment with Ngrok

1. Start the development server:
```bash
npm start
```

2. In another terminal, expose the frontend:
```bash
ngrok http 3000
```

3. Access the frontend via the ngrok URL (e.g., `https://abc123.ngrok-free.app`)

### Production Deployment with Ngrok

1. Build the production bundle:
```bash
npm run build
```

2. Serve the production build:
```bash
npx serve -s build -l 3000
```

3. In another terminal, expose the frontend:
```bash
ngrok http 3000
```

4. Access the frontend via the ngrok URL

### Important Notes
- Update `API_BASE_URL` in `src/services/api.ts` to point to your backend ngrok URL
- For persistent subdomains (optional):
```bash
ngrok http 3000 --subdomain your-subdomain
```
- To monitor requests:
```bash
ngrok http 3000 --log=stdout
```

## 🐛 Troubleshooting

### Microphone Access
- Ensure browser has microphone permissions
- Check browser console for permission errors
- Try using HTTPS in production for reliable mic access

### WebSocket Connection
- Verify backend is running on port 8000
- Check for CORS issues in browser console
- Ensure firewall allows WebSocket connections

### Audio Issues
- Check browser compatibility (Chrome/Edge recommended)
- Verify audio input device is selected correctly
- Monitor console for audio processing errors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
