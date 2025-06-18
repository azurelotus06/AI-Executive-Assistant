import React, { useState, useEffect } from 'react';
import { 
  Phone, 
  PhoneOff, 
  Users, 
  AlertCircle, 
  CheckCircle,
  Download,
  Clock,
  Mic
} from 'lucide-react';
import { joinMeeting, leaveMeeting, getMeetingStatus, wsService } from '../services/api';

interface MeetingPanelProps {
  onStatusChange?: (status: string) => void;
}

interface StatusDetails {
  code: string;
  created_at?: string;
  start_time?: string;
  error_message?: string;
  error_type?: string;
}

interface ErrorDetails {
  code?: string;
  message?: string;
  type?: string;
}

export const MeetingPanel: React.FC<MeetingPanelProps> = ({ onStatusChange }) => {
  const [meetingUrl, setMeetingUrl] = useState('');
  const [botId, setBotId] = useState<string | null>(null);
  const [isJoining, setIsJoining] = useState(false);
  const [meetingStatus, setMeetingStatus] = useState<string>('idle');
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [statusDetails, setStatusDetails] = useState<StatusDetails | null>(null);
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const [speakers, setSpeakers] = useState<string[]>([]);
  const [errorDetails, setErrorDetails] = useState<ErrorDetails | null>(null);

  // WebSocket status updates
  useEffect(() => {
    const handleStatusUpdate = (data: any) => {
      const newStatus = data.status;
      setMeetingStatus(newStatus);
      
      // Update status message based on status
      switch (newStatus) {
        case 'joining_call':
          setStatusMessage('Bot is joining the meeting...');
          break;
        case 'in_waiting_room':
          setStatusMessage('Bot is in the waiting room. Please admit it to the meeting.');
          break;
        case 'in_call_not_recording':
          setStatusMessage('Bot has joined but is not recording yet...');
          break;
        case 'in_call_recording':
          setStatusMessage('Bot is actively recording the meeting.');
          break;
        case 'call_ended':
          setStatusMessage('Meeting has ended. Processing transcript...');
          break;
        case 'completed':
          setStatusMessage('Meeting completed successfully!');
          break;
        default:
          if (newStatus && newStatus.startsWith('failed_')) {
            setStatusMessage(`Failed: ${newStatus.replace('failed_', '').replace(/_/g, ' ')}`);
          }
      }
      
      if (onStatusChange) {
        onStatusChange(newStatus);
      }
    };

    wsService.on('status', handleStatusUpdate);
    
    // Connect websocket if not already connected
    if (!wsService.isConnected()) {
      wsService.connect();
    }

    return () => {
      wsService.off('status', handleStatusUpdate);
    };
  }, [onStatusChange]);

  // Polling for MeetingBass webhook status
  useEffect(() => {
    if (!botId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await getMeetingStatus(botId);
        if (response.success && response.bot_status) {
          const status = response.bot_status.status;
          setMeetingStatus(status);
          
          // Update status details if available
          if (response.bot_status.status_details) {
            setStatusDetails(response.bot_status.status_details);
          }

          // Update recording URL if available
          if (response.bot_status.mp4_url) {
            setRecordingUrl(response.bot_status.mp4_url);
          }

          // Update speakers if available
          if (response.bot_status.speakers) {
            setSpeakers(response.bot_status.speakers);
          }

          // Update error details if available
          if (response.bot_status.error_details) {
            setErrorDetails(response.bot_status.error_details);
          }
        }
      } catch (err) {
        console.error('Error polling meeting status:', err);
      }
    }, 1500); // Poll every 1.5 seconds

    return () => clearInterval(pollInterval);
  }, [botId]);

  const handleJoinMeeting = async () => {
    if (!meetingUrl.trim()) {
      setError('Please enter a meeting URL');
      return;
    }

    setIsJoining(true);
    setError(null);

    try {
      const response = await joinMeeting(meetingUrl);
      setBotId(response.bot_id);
      setMeetingStatus('joining');
      setStatusMessage(response.message);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to join meeting');
    } finally {
      setIsJoining(false);
    }
  };

  const handleLeaveMeeting = async () => {
    if (!botId) return;

    try {
      await leaveMeeting(botId);
      setBotId(null);
      setMeetingStatus('idle');
      setStatusMessage('Bot has left the meeting');
      setMeetingUrl('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to leave meeting');
    }
  };

  const getStatusIcon = () => {
    switch (meetingStatus) {
      case 'in_call_recording':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'joining_call':
      case 'in_waiting_room':
      case 'in_call_not_recording':
        return <AlertCircle className="w-5 h-5 text-yellow-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-blue-500" />;
      default:
        if (meetingStatus && meetingStatus.startsWith('failed_')) {
          return <AlertCircle className="w-5 h-5 text-red-500" />;
        }
        return <Users className="w-5 h-5 text-gray-400" />;
    }
  };

  const isInMeeting = !!(botId && meetingStatus && meetingStatus !== 'idle' && meetingStatus !== 'completed' && (!meetingStatus || !meetingStatus.startsWith('failed_')));

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Meeting Integration</h2>
        {getStatusIcon()}
      </div>

      <div className="space-y-4">
        {/* Meeting URL Input */}
        <div>
          <label htmlFor="meeting-url" className="block text-sm font-medium text-gray-700 mb-1">
            Meeting URL
          </label>
          <input
            id="meeting-url"
            type="text"
            value={meetingUrl}
            onChange={(e) => setMeetingUrl(e.target.value)}
            placeholder="https://zoom.us/j/123456789"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isInMeeting}
          />
          <p className="mt-1 text-xs text-gray-500">
            Supports Zoom, Teams, Google Meet, and other platforms
          </p>
        </div>

        {/* Status Message */}
        {statusMessage && (
          <div className={`p-3 rounded-md text-sm ${
            statusDetails?.code === 'in_call_recording' ? 'bg-green-50 text-green-800' :
            statusDetails?.code === 'complete' ? 'bg-blue-50 text-blue-800' :
            ['failed', 'bot_rejected', 'bot_removed', 'waiting_room_timeout', 'invalid_meeting_url', 'meeting_error'].includes(statusDetails?.code || '') ? 
              'bg-red-50 text-red-800' :
            'bg-blue-50 text-blue-800'
          }`}>
            <div className="font-medium">{statusMessage}</div>
            {statusDetails?.created_at && (
              <div className="text-xs mt-1 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(statusDetails.created_at).toLocaleString()}
              </div>
            )}
            {errorDetails && (
              <div className="mt-2 text-xs">
                {errorDetails.message && <p>Error: {errorDetails.message}</p>}
                {errorDetails.type && <p>Type: {errorDetails.type}</p>}
              </div>
            )}
          </div>
        )}

        {/* Recording URL */}
        {recordingUrl && (
          <div className="p-3 bg-green-50 text-green-800 rounded-md text-sm">
            <div className="font-medium flex items-center gap-2">
              <Download className="w-4 h-4" />
              Recording Available
            </div>
            <a 
              href={recordingUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-xs mt-1 block underline truncate"
            >
              {recordingUrl}
            </a>
            <p className="text-xs mt-1 text-green-600">
              Note: This URL expires in 2 hours
            </p>
          </div>
        )}

        {/* Speakers List */}
        {speakers.length > 0 && (
          <div className="p-3 bg-blue-50 text-blue-800 rounded-md text-sm">
            <div className="font-medium flex items-center gap-2">
              <Mic className="w-4 h-4" />
              Speakers
            </div>
            <ul className="mt-1 text-xs">
              {speakers.map((speaker, i) => (
                <li key={i}>{speaker}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-red-50 text-red-800 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* Bot ID Display */}
        {botId && (
          <div className="p-3 bg-gray-50 rounded-md">
            <p className="text-xs text-gray-600">Bot ID: {botId}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          {!isInMeeting ? (
            <button
              onClick={handleJoinMeeting}
              disabled={isJoining || !meetingUrl.trim()}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              <Phone className="w-4 h-4" />
              {isJoining ? 'Joining...' : 'Join Meeting'}
            </button>
          ) : (
            <button
              onClick={handleLeaveMeeting}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              <PhoneOff className="w-4 h-4" />
              Leave Meeting
            </button>
          )}
        </div>

        {/* Instructions */}
        <div className="mt-4 p-3 bg-gray-50 rounded-md">
          <h3 className="text-sm font-medium text-gray-700 mb-2">How it works:</h3>
          <ol className="text-xs text-gray-600 space-y-1 list-decimal list-inside">
            <li>Enter your meeting URL above</li>
            <li>Click "Join Meeting" to send the AI assistant</li>
            <li>Admit the bot when it appears in the waiting room</li>
            <li>The AI will listen and provide insights in real-time</li>
            <li>Transcripts and insights appear in the conversation panel</li>
          </ol>
        </div>
      </div>
    </div>
  );
};
