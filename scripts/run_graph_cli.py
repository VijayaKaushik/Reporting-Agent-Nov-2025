import argparse
import json
from app.orchestrator import run_graph
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    parser = argparse.ArgumentParser(description="Run the langgraph orchestrator with a sample payload.")
    parser.add_argument('--thread_id', type=str, default='t1', help='Thread ID (default: t1)')
    parser.add_argument('--message', type=str, default='hello', help='User message (default: Createa report based on demographics)')
    parser.add_argument('--template_id', type=str, default='', help='Selected template ID (optional)')
    parser.add_argument('--input_fields', type=str, default='', help='JSON string of input fields (optional)')
    args = parser.parse_args()

    payload = {'message': args.message}
    if args.template_id:
        payload['selected_template_id'] = args.template_id
    if args.input_fields:
        try:
            payload['input_fields'] = json.loads(args.input_fields)
        except Exception as e:
            print(f"Failed to parse input_fields: {e}")
            return

    result = run_graph(args.thread_id, payload)
    print("Result:\n" + json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
