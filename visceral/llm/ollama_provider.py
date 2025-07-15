# visceral/llm/ollama_provider.py

import ollama

class OllamaProvider:
    """
    A provider to interact with a local Ollama-served LLM.
    """
    def __init__(self, model: str = "mistral:latest", host: str = None):
        """
        Initializes the Ollama client.
        Args:
            model (str): The name of the model to use (e.g., 'mistral', 'llama3').
            host (str, optional): The host address for Ollama. Defaults to None.
        """
        self.model = model
        self.client = ollama.Client(host=host)
        try:
            print(f"Connecting to Ollama and pulling model '{self.model}'...")
            self.client.pull(self.model, insecure=True)
            print("Model pulled successfully.")
        except Exception as e:
            print(f"ERROR: Could not connect to Ollama or pull the model. Is Ollama running?")
            print(f"Exception: {e}")
            # It might still work if the model is already available, so we don't exit.

    def query(self, prompt: str) -> str:
        """
        Sends a prompt to the LLM and returns the response.
        """
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content']
        except Exception as e:
            print(f"ERROR: Failed to get response from Ollama: {e}")
            return "Sorry, I'm having trouble connecting to my reasoning core."
