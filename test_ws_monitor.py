import asyncio
import websockets
import json
import sys

async def test_monitor(session_id):
    uri = f"ws://localhost:8000/api/ws/portfolio-scraping/{session_id}"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for events...")
            print("(Events will appear as scraping progresses)")
            print("-" * 50)
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    print(f"\n[{data.get('type', 'info').upper()}] {data.get('message', 'Update')}")
                    if 'total_companies' in data:
                        print(f"  Total: {data.get('total_companies', 0)} | YC: {data.get('yc_companies', 0)} | Antler: {data.get('antler_companies', 0)}")
                    if 'screenshot' in data:
                        print(f"  [Screenshot received - {len(data['screenshot'])} bytes]")
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else "demo-test"
    print(f"Testing WebSocket monitor for session: {session_id}")
    asyncio.run(test_monitor(session_id))
