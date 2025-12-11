"""Check if Ollama is running and which models are available"""
import requests

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODELS = ["llama3.2", "mistral", "phi3", "qwen2.5", "llama3.1"]

def check_ollama():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            available_models = [m.get('name', '') for m in models]
            
            print("[OK] Ollama is running")
            print(f"\nAvailable models: {len(available_models)}")
            for model in available_models:
                print(f"  - {model}")
            
            # Check for preferred models
            preferred_found = []
            for preferred in OLLAMA_MODELS:
                if any(preferred in m for m in available_models):
                    preferred_found.append(preferred)
            
            if preferred_found:
                print(f"\n[OK] Preferred models found: {', '.join(preferred_found)}")
                print(f"  Will use: {preferred_found[0]}")
            else:
                print(f"\n[WARN] No preferred models found. Install one with:")
                print(f"  ollama pull {OLLAMA_MODELS[0]}")
            
            return True
        else:
            print(f"[ERROR] Ollama returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Ollama is not running")
        print("\nTo start Ollama:")
        print("  1. Install: https://ollama.ai")
        print("  2. Start: ollama serve")
        print(f"  3. Pull a model: ollama pull {OLLAMA_MODELS[0]}")
        return False
    except Exception as e:
        print(f"[ERROR] Error checking Ollama: {e}")
        return False

if __name__ == "__main__":
    check_ollama()

