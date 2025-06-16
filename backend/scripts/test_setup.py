"""Test script to verify backend setup and API functionality"""
import asyncio
import httpx
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


async def test_api_keys():
    """Test if API keys are configured"""
    print("🔑 Testing API Keys Configuration...")
    
    issues = []
    
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        issues.append("❌ OpenAI API key not configured")
    else:
        print("✅ OpenAI API key configured")
    
    if not settings.elevenlabs_api_key or settings.elevenlabs_api_key == "your_elevenlabs_api_key_here":
        issues.append("❌ ElevenLabs API key not configured")
    else:
        print("✅ ElevenLabs API key configured")
    
    return len(issues) == 0, issues


async def test_server_connection():
    """Test if the server is running"""
    print("\n🌐 Testing Server Connection...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/")
            if response.status_code == 200:
                print("✅ Server is running")
                return True, []
            else:
                return False, [f"❌ Server returned status code: {response.status_code}"]
    except Exception as e:
        return False, [f"❌ Could not connect to server: {str(e)}"]


async def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n🏥 Testing Health Check...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                data = response.json()
                print("✅ Health check passed")
                print(f"   Audio Processor: {'✅' if data['services']['audio_processor'] else '❌'}")
                print(f"   AI Service: {'✅' if data['services']['ai_service'] else '❌'}")
                print(f"   TTS Service: {'✅' if data['services']['tts_service'] else '❌'}")
                return True, []
            else:
                return False, [f"❌ Health check failed with status: {response.status_code}"]
    except Exception as e:
        return False, [f"❌ Health check error: {str(e)}"]


async def test_system_status():
    """Test the system status endpoint"""
    print("\n📊 Testing System Status...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/control/system-status")
            if response.status_code == 200:
                data = response.json()
                print("✅ System status retrieved successfully")
                return True, []
            else:
                return False, [f"❌ System status failed with status: {response.status_code}"]
    except Exception as e:
        return False, [f"❌ System status error: {str(e)}"]


async def test_ai_analysis():
    """Test AI analysis with sample data"""
    print("\n🤖 Testing AI Analysis...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/ai/test-analysis",
                json={"test_transcript": "Let's discuss our Q4 revenue targets and growth strategy."}
            )
            if response.status_code == 200:
                data = response.json()
                print("✅ AI analysis test passed")
                if data.get('ai_response'):
                    print(f"   AI decided to speak: {data['ai_response'].get('should_speak', False)}")
                    if data['ai_response'].get('response'):
                        print(f"   AI response: {data['ai_response']['response'][:100]}...")
                return True, []
            else:
                return False, [f"❌ AI analysis failed with status: {response.status_code}"]
    except Exception as e:
        return False, [f"❌ AI analysis error: {str(e)}"]


async def test_websocket():
    """Test WebSocket connection"""
    print("\n🔌 Testing WebSocket Connection...")
    
    try:
        import websockets
        
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            # Send a test message
            test_message = json.dumps({
                "type": "control",
                "action": "ping"
            })
            await websocket.send(test_message)
            
            # Wait for response (with timeout)
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print("✅ WebSocket connection successful")
            return True, []
            
    except ImportError:
        return False, ["❌ websockets library not installed"]
    except Exception as e:
        return False, [f"❌ WebSocket connection error: {str(e)}"]


async def main():
    """Run all tests"""
    print("🚀 Zoom AI Assistant Backend Test Suite")
    print("=" * 50)
    
    all_passed = True
    all_issues = []
    
    # Test API keys
    passed, issues = await test_api_keys()
    all_passed &= passed
    all_issues.extend(issues)
    
    # Test server connection
    passed, issues = await test_server_connection()
    if not passed:
        all_passed = False
        all_issues.extend(issues)
        print("\n⚠️  Server is not running. Please start it with:")
        print("  cd backend")
        print("  uv run uvicorn main:app --reload")
        return
    
    # Test other endpoints
    for test_func in [test_health_endpoint, test_system_status, test_ai_analysis, test_websocket]:
        passed, issues = await test_func()
        all_passed &= passed
        all_issues.extend(issues)
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! Your backend is ready to use.")
    else:
        print("❌ Some tests failed. Please fix the following issues:")
        for issue in all_issues:
            print(f"   {issue}")
        
        print("\n📝 Next steps:")
        if any("API key" in issue for issue in all_issues):
            print("   1. Configure your API keys in backend/.env")
        if any("connect to server" in issue for issue in all_issues):
            print("   1. Start the backend server")
        print("   2. Run this test again")


if __name__ == "__main__":
    asyncio.run(main())
