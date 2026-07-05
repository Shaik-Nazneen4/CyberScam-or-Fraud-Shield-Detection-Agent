"""CLI entry point and testing harness for the AI Fraud Shield Coordinator Agent.

Provides an interactive CLI interface to test the 7 user scenarios and custom queries.
Runs offline using the MockModelProvider by default.
"""

import json
import logging
import sys
from typing import List

from fraud_shield.coordinator import CoordinatorAgent
from fraud_shield.config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger("fraud_shield_main")

# List of supported user examples from requirements
EXAMPLES: List[str] = [
    "Analyze this email: Dear customer, your account is suspended. Click here to verify your password or wire $500.",
    "Is this WhatsApp message a scam? 'Hey mom, I lost my phone, please transfer $2000 to my friend's account immediately.'",
    "Check this URL: https://goog1e-security-login.com/index.html",
    "Is this internship genuine? I received a Telegram message offering a remote data entry job paying $100 per hour, but I need to deposit $50 first for training.",
    "Is this shopping website trustworthy? The online store is selling high-end cameras with a 95% discount, but they have no refund policy or phone contact details.",
    "My bank called and asked for my OTP verification code because of an unusual login.",
    "Analyze everything and give me a risk report: Here is the email urgent security warning, the payment link is http://amazon-security-update.com, and they want me to send a gift card verification code."
]

def print_separator():
    print("=" * 80)

def run_query(coordinator: CoordinatorAgent, query: str):
    print_separator()
    print(f"USER REQUEST: {query}")
    print_separator()
    
    # Run the coordinator agent
    response = coordinator.process_request(query)
    
    # Print the structured JSON response
    print("\nSTRUCTURED JSON RESPONSE:")
    print(json.dumps(response.model_dump(), indent=2))
    print_separator()
    print("\n")

def main():
    coordinator = CoordinatorAgent()
    
    print("\n")
    print("*" * 80)
    print("                 AI FRAUD SHIELD - COORDINATOR AGENT HARNESS                  ")
    print("*" * 80)
    print("Initialized Coordinator Agent (Offline Mock Mode).")
    print("This harness demonstrates dynamic routing, sub-agent execution, and result aggregation.\n")
    
    while True:
        print("Select an option:")
        print("1-7. Run one of the supported capstone scenarios")
        print("8.   Run all 7 scenarios sequentially")
        print("9.   Test with a custom input query")
        print("0.   Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "0":
            print("Exiting AI Fraud Shield. Stay safe!")
            sys.exit(0)
            
        elif choice in [str(i) for i in range(1, 8)]:
            index = int(choice) - 1
            run_query(coordinator, EXAMPLES[index])
            
        elif choice == "8":
            print(f"Running all {len(EXAMPLES)} scenarios sequentially...")
            for i, example in enumerate(EXAMPLES, 1):
                print(f"\n--- Scenario {i} ---")
                run_query(coordinator, example)
                
        elif choice == "9":
            custom_query = input("\nEnter your custom scam query: ").strip()
            if custom_query:
                run_query(coordinator, custom_query)
            else:
                print("Query cannot be empty.")
                
        else:
            print("Invalid choice. Please select 0-9.")
            print_separator()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting program.")
        sys.exit(0)
