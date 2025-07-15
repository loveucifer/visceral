# debug_ollama.py
# A simple script to test the connection to Ollama, independent of Streamlit.

import ollama

HOST = "http://127.0.0.1:11434"
MODEL = "llama3:latest"

print("--- Ollama Connection Test ---")

try:
    print(f"1. Attempting to create Ollama client for host: {HOST}")
    client = ollama.Client(host=HOST)
    print("   Client created successfully.")

    print(f"\n2. Checking for model: {MODEL}")
    client.show(MODEL)
    print("   Model found successfully.")

    print("\n3. Sending a test query to the model...")
    response = client.chat(
        model=MODEL,
        messages=[{'role': 'user', 'content': 'Hello! Is this a test?'}]
    )
    print("   Query sent successfully.")

    print("\n4. Receiving response...")
    message = response['message']['content']
    print(f"   Response received: '{message}'")

    print("\n--- TEST SUCCEEDED ---")
    print("Your Python environment can successfully connect to and query Ollama.")

except Exception as e:
    print("\n--- !!! TEST FAILED !!! ---")
    print("An error occurred. This means the problem is with the Python environment's ability to connect to Ollama.")
    print("\nError details:")
    print(e)
    print("\nNext Steps:")
    print("1. Ensure the Ollama application is running.")
    print("2. Double-check that the `ollama` Python library is installed in the correct environment (`pip3 install ollama`).")

