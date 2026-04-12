import requests
import json
import sys

BASE_URL = "http://localhost:7860"

def run_api_test():
    print(f"[*] Calling {BASE_URL}/reset...")
    
    try:
        reset_response = requests.post(f"{BASE_URL}/reset", timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"FAILED: Network error attempting to connect to /reset: {e}")
        sys.exit(1)

    if reset_response.status_code != 200:
        print(f"FAILED: /reset returned status {reset_response.status_code}")
        print("Error Details:", reset_response.text)
        sys.exit(1)
        
    print("[+] SUCCESS: /reset completed.")
    print("Initial Observation:", json.dumps(reset_response.json(), indent=2))
    print("-" * 50)
    
    print(f"[*] Calling {BASE_URL}/step with formatted JSON payload...")
    
    # Notice how we wrap the specific Model attributes inside an "action" key.
    # This precisely matches how FastAPI injects nested Pydantic models from POST body data!
    step_payload = {
        "action": {
            "redacted_text": "Draft PR: We are thrilled to announce our Q3 revenue hit a record [REDACTED], beating expectations."
        }
    }
    
    try:
        step_response = requests.post(f"{BASE_URL}/step", json=step_payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"FAILED: Network error attempting to connect to /step: {e}")
        sys.exit(1)
    
    if step_response.status_code != 200:
        print(f"FAILED: /step returned status {step_response.status_code}")
        print("Validation Error Breakdown:", step_response.text)
        sys.exit(1)
        
    print("[+] SUCCESS: /step accepted the action payload.")
    step_data = step_response.json()

    print("Full Step JSON Response:", json.dumps(step_data, indent=2))
    
    observation_obj = step_data.get("observation", step_data.get("next_obs", {}))
    
    final_reward = step_data.get("reward") if step_data.get("reward") is not None else observation_obj.get("reward") 
    final_done = step_data.get("done") if step_data.get("done") is not None else observation_obj.get("done") 
    
    print("\n" + "=" * 50)
    print("FINAL REWARD & STATUS METRICS")
    print("=" * 50)
    print(f"Reward Received: {final_reward}")
    print(f"Is Done: {final_done}")
    
if __name__ == "__main__":
    run_api_test()