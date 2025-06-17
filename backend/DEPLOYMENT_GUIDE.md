# Backend Deployment Guide - Solving 503 Tunnel Unavailable Error

## Understanding the 503 Error

The "503 - Tunnel Unavailable" error occurs when:
1. Your backend server is not running on port 8000
2. The tunnel service cannot connect to your local server
3. The subdomain might be taken or expired

## Solution Steps

### Step 1: Start the Backend Server

First, ensure your backend server is running. Open a terminal and run:

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [####] using WatchFiles
INFO:     Started server process [####]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Verify Backend is Running

Open a new terminal and test:
```bash
curl http://localhost:8000/health
```

You should see a JSON response with health status.

### Step 3: Choose a Tunneling Solution

#### Option A: Using Localtunnel (Original Method)

1. Install localtunnel globally (if not already installed):
   ```bash
   npm install -g localtunnel
   ```

2. Run the improved deployment script:
   ```bash
   cd backend
   deploy_tunnel.bat
   ```

3. Important notes about Localtunnel:
   - It may show a password page when first accessing the URL
   - The password will be displayed in your terminal
   - The subdomain might not always be available

#### Option B: Using Ngrok (More Reliable)

1. Run the ngrok deployment script:
   ```bash
   cd backend
   deploy_ngrok.bat
   ```

2. Ngrok will provide a URL like: `https://xxxxx.ngrok.io`
3. Update your frontend configuration to use this new URL

### Step 4: Update Frontend Configuration

If using ngrok, update your frontend API configuration:

1. Open `frontend/src/services/api.ts`
2. Update the API_BASE_URL to your ngrok URL
3. Restart your frontend application

## Troubleshooting

### If you still see 503 error:

1. **Check if port 8000 is in use:**
   ```bash
   netstat -ano | findstr :8000
   ```

2. **Kill any process using port 8000:**
   ```bash
   taskkill /PID <process_id> /F
   ```

3. **Try a different subdomain:**
   Edit `start_tunnel.bat` and change `zoom-backend-1` to something unique like `zoom-backend-yourname`

4. **Use ngrok instead:**
   Ngrok is generally more reliable than localtunnel

### Common Issues and Solutions:

1. **"lt command not found"**
   - Solution: Run `npm install -g localtunnel`

2. **"Subdomain already in use"**
   - Solution: Choose a different subdomain or use ngrok

3. **Backend crashes on startup**
   - Check your `.env` file configuration
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

4. **CORS errors after deployment**
   - The backend already includes your localtunnel URL in CORS settings
   - If using ngrok, you'll need to add the ngrok URL to CORS origins in `main.py`

## Quick Start Commands

```bash
# Terminal 1 - Start Backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Start Tunnel (choose one)
cd backend
deploy_tunnel.bat    # For localtunnel
# OR
deploy_ngrok.bat     # For ngrok
```

## Security Note

When exposing your local server to the internet:
- Be cautious about sensitive data
- Consider adding authentication
- Monitor access logs
- Stop the tunnel when not in use
