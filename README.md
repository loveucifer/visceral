# Visceral: A Self-Correcting AI Agent

This project is a proof-of-concept for an AI agent that can evolve its own logic based on user feedback, without retraining a neural network. It uses a symbolic rule engine for deterministic reasoning and falls back to an LLM for novel queries. Its most important feature is its ability to create new symbolic rules based on user corrections.

## How It Works

1.  **Symbolic Core**: The agent first tries to match a user's query against a set of human-readable rules stored in `data/rules.json`.
2.  **LLM Fallback**: If no rule matches, it queries a local LLM (via Ollama) to generate a response.
3.  **Feedback Loop**: The user can rate the agent's response.
    * **Positive Feedback**: Increases the success score of the rule that was used, making it more likely to be chosen in the future.
    * **Negative Feedback**: If the user provides a correction, the agent sends the original query and the correction to the LLM, asking it to synthesize a *new rule*. This new rule is then added to its logic base.
4.  **Evolution**: Over time, the agent's behavior becomes more refined and aligned with the user's preferences as its symbolic rule set grows and adapts.

## ⚙️ Setup and Installation

### Prerequisites

1.  **Python 3.9+**: Make sure you have a modern version of Python installed.
2.  **Ollama**: You need Ollama running on your machine to serve the local LLM.
    * [Download Ollama here](https://ollama.com/).
    * After installing, run the following command in your terminal to download the Mistral model:
        ```bash
        ollama pull mistral
        ```

### Installation Steps

1.  **Create Project Structure**:
    Organize the files provided into the following structure:

    ```
    .
    ├── app.py
    ├── pyproject.toml
    └── visceral/
        ├── __init__.py  (can be empty)
        ├── core/
        │   ├── __init__.py (can be empty)
        │   ├── agent.py
        │   ├── datamodels.py
        │   └── engine.py
        ├── llm/
        │   ├── __init__.py (can be empty)
        │   └── ollama_provider.py
        └── memory/
            ├── __init__.py (can be empty)
            └── json_memory.py
    ```

2.  **Install Dependencies**:
    Navigate to the root directory of your project in the terminal and install the required Python packages.

    ```bash
    pip install streamlit ollama
    ```

## 🚀 Running the Agent

1.  **Start Ollama**: Ensure the Ollama application is running in the background.
2.  **Run the Streamlit App**: Open your terminal, navigate to the project's root directory, and run:

    ```bash
    streamlit run app.py
    ```

A new tab should open in your web browser with the Visceral AI interface. You can now start chatting with it and providing feedback to watch it learn.
