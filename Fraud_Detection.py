"""
Fraud_Detection.py — Entry point for the AI Fraud Shield Detection Agent.

This module provides the top-level interface for running the AI Fraud Shield
coordinator agent from the command line or programmatically.

Usage:
    python Fraud_Detection.py
    python Fraud_Detection.py --query "Check this URL: http://example.com"
    python Fraud_Detection.py --all
"""

import argparse
import json
import logging
import sys

from fraud_shield.coordinator import CoordinatorAgent
from fraud_shield.config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger("fraud_detection")

# Pre-configured demonstration scenarios
DEMO_SCENARIOS = [
    "Analyze this email: Dear customer, your account is suspended. Click here to verify your password or wire $500.",
    "Is this WhatsApp message a scam? 'Hey mom, I lost my phone, please transfer $2000 to my friend's account immediately.'",
    "Check this URL: https://goog1e-security-login.com/index.html",
    "Is this internship genuine? I received a Telegram message offering a remote data entry job paying $100 per hour, but I need to deposit $50 first for training.",
    "Is this shopping website trustworthy? The online store is selling high-end cameras with a 95% discount, but they have no refund policy or phone contact details.",
    "My bank called and asked for my OTP verification code because of an unusual login.",
    "Analyze everything and give me a risk report: Here is the email urgent security warning, the payment link is http://amazon-security-update.com, and they want me to send a gift card verification code.",
]


def analyze(query: str, coordinator: CoordinatorAgent) -> None:
    """Run fraud detection analysis on a single query and print the result."""
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)
    response = coordinator.process_request(query)
    print("\nRESULT (JSON):")
    print(json.dumps(response.model_dump(), indent=2))
    print("=" * 80)
    print()


def run_interactive(coordinator: CoordinatorAgent) -> None:
    """Launch the interactive CLI menu."""
    print("\n" + "*" * 80)
    print("              AI FRAUD SHIELD — DETECTION AGENT (Interactive Mode)              ")
    print("*" * 80)
    print("Running in offline mock mode. Type 0 to exit.\n")

    while True:
        print("Options:")
        for i, scenario in enumerate(DEMO_SCENARIOS, 1):
            print(f"  {i}. {scenario[:80]}{'...' if len(scenario) > 80 else ''}")
        print(f"  {len(DEMO_SCENARIOS) + 1}. Run ALL scenarios")
        print(f"  {len(DEMO_SCENARIOS) + 2}. Enter a custom query")
        print("  0. Exit\n")

        choice = input("Select an option: ").strip()

        if choice == "0":
            print("Exiting AI Fraud Shield. Stay safe!")
            sys.exit(0)
        elif choice.isdigit() and 1 <= int(choice) <= len(DEMO_SCENARIOS):
            analyze(DEMO_SCENARIOS[int(choice) - 1], coordinator)
        elif choice == str(len(DEMO_SCENARIOS) + 1):
            for i, scenario in enumerate(DEMO_SCENARIOS, 1):
                print(f"\n--- Scenario {i} of {len(DEMO_SCENARIOS)} ---")
                analyze(scenario, coordinator)
        elif choice == str(len(DEMO_SCENARIOS) + 2):
            custom = input("Enter your query: ").strip()
            if custom:
                analyze(custom, coordinator)
            else:
                print("Query cannot be empty.\n")
        else:
            print("Invalid choice. Please try again.\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Fraud Shield Detection Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="A single query to analyze (e.g. a suspicious URL, email, or message).",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all built-in demo scenarios and exit.",
    )
    args = parser.parse_args()

    coordinator = CoordinatorAgent()

    if args.query:
        analyze(args.query, coordinator)
    elif args.all:
        print(f"Running all {len(DEMO_SCENARIOS)} scenarios...\n")
        for i, scenario in enumerate(DEMO_SCENARIOS, 1):
            print(f"--- Scenario {i} ---")
            analyze(scenario, coordinator)
    else:
        run_interactive(coordinator)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)
