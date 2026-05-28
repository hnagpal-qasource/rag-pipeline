"""
CLI entry point for the telecom RAG chatbot.
Usage: python main.py
"""
import os
import sys
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from dotenv import load_dotenv

load_dotenv()


def main():
    if sys.version_info >= (3, 14):
        print("Unsupported Python version for this project.")
        print("Detected:", sys.version.split()[0])
        print("Please use Python 3.11, 3.12, or 3.13 and recreate the virtual environment.")
        return

    from rag_chain import build_chain

    print("=== Telecom Customer Care Chatbot (RAG) ===")
    print("Type your question and press Enter. Type 'quit' to exit.\n")

    chain = build_chain()

    while True:
        question = input("Customer: ").strip()
        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        print("\nAssistant: ", end="", flush=True)
        for chunk in chain.stream(question):
            print(chunk, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    main()
