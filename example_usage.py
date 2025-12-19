import urllib.request
import json

BASE_URL = "http://127.0.0.1:5010"

def get_data(endpoint):
    url = f"{BASE_URL}{endpoint}"
    try:
        print(f"Requesting: {url}")
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
            else:
                print(f"Failed with status: {response.status}")
    except Exception as e:
        print(f"Error accessing {url}: {e}")
    return None

def main():
    print("--- Checking Proxy Pool Status ---")
    
    # Check count
    count_info = get_data("/count/")
    if count_info:
        count = count_info.get("count", 0)
        print(f"Current proxy count: {count}")
        
        if count > 0:
            # Get a proxy
            print("\n--- Fetching a Random Proxy ---")
            proxy_info = get_data("/get/")
            if proxy_info:
                print(f"Fetched Proxy: {proxy_info.get('proxy')}")
                print(f"Full Info: {proxy_info}")
            else:
                print("Failed to fetch proxy or pool returned empty.")
        else:
            print("\nPool is empty. Wait a few moments for the scheduler to fetch proxies.")
    else:
        print("Could not connect to Proxy Pool API.")

if __name__ == "__main__":
    main()
