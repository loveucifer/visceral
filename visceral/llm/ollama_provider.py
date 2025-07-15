# visceral/llm/ollama_provider.py

import ollama

class OllamaProvider:
    """A provider to interact with a local Ollama-served LLM."""
    def __init__(self, model: str = "llama3:latest", host: str = "http://127.0.0.1:11434"):
        """
        Initializes the Ollama client. Defaults to llama3.
        Explicitly sets the host to avoid potential resolution issues with 'localhost'.
        """
        self.model = model
        try:
            # AI ENHANCEMENT: Explicitly define the host. '127.0.0.1' is often more reliable than 'localhost'.
            self.client = ollama.Client(host=host)
            print(f"Attempting to connect to Ollama at {host}...")
            print(f"Checking for Ollama model '{self.model}'...")
            
            # A quick check to see if the model is available locally.
            self.client.show(self.model)
            print(f"Successfully connected to Ollama with model '{self.model}'.")
        except Exception as e:
            print(f"FATAL: Could not connect to Ollama or find model '{self.model}'.")
            print(f"1. Please ensure the Ollama application is running on your Mac.")
            print(f"2. Verify that the model is downloaded by running 'ollama list' in your terminal.")
            print(f"3. Check if another service is using port 11434.")
            print(f"Error details: {e}")
            raise e

    def query(self, prompt: str) -> str:
        """Sends a prompt to the LLM and returns the response."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"ERROR: Failed to get response from Ollama: {e}")
            return "Sorry, I'm having trouble connecting to my reasoning core."
