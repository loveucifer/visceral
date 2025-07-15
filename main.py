# main.py

from visceral.core.agent import VisceralAgent

"""
The main entry point for running the Visceral agent in a console.
"""

def main():
    print("--- Visceral AI Agent ---")
    print("Type 'quit' to exit.")
    
    agent = VisceralAgent()

    # Add a default rule if none exist, for demonstration
    if not agent.rule_engine.rules:
        print("INFO: No rules found. Adding a default 'hello' rule.")
        agent.rule_engine.add_rule("hello", "Hello! How can I assist you today?")

    while True:
        query = input("\n> ")
        if query.lower() == 'quit':
            break

        decision = agent.process_query(query)
        
        print(f"\nVisceral: {decision.output}")
        print(f"(Decision ID: {decision.id}, Confidence: {decision.final_confidence:.2f})")
        
        # Simple feedback loop
        feedback = input("Was this helpful? (y/n): ").lower()
        if feedback == 'y':
            agent.provide_feedback(decision.id, 5) # 5-star rating
        elif feedback == 'n':
            agent.provide_feedback(decision.id, 1) # 1-star rating


if __name__ == "__main__":
    main()

