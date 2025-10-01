import json
import datetime
import re
from app.features.ai import get_ai_response
from app.core.agent import AIAgent

def propose_code_change(current_code_snippet, problem_description, desired_outcome):
    """
    Uses the AI to propose a code change based on a problem description and desired outcome.
    The proposed change is saved to a file for manual review.
    """
    prompt = f"""You are an AI assistant that helps in improving code.
Given the following Python code snippet, a problem description, and a desired outcome,
propose a code change. The output should be only the new code snippet.

--- Current Code Snippet ---
```python
{current_code_snippet}
```

--- Problem Description ---
{problem_description}

--- Desired Outcome ---
{desired_outcome}

--- Proposed Code Change (Python only) ---
```python
"""

    # For this, we need a fresh AI brain context, not tied to the current conversation
    # This is a simplified approach for demonstration.
    agent = AIAgent(None) # Create a dummy agent to load the AI brain
    ai_brain = agent.load_ai_brain()

    proposed_code = get_ai_response(prompt, [], ai_brain)

    # Extract only the code block if the AI adds extra text
    match = re.search(r'```python\n(.*?)```', proposed_code, re.DOTALL)
    if match:
        proposed_code = match.group(1).strip()
    else:
        # If no code block found, take the whole response
        proposed_code = proposed_code.strip()

    # Save the proposed change to a file
    file_name = "proposed_changes.py"
    with open(file_name, "a") as f:
        f.write(f"# Proposed Change - {datetime.datetime.now()}\n")
        f.write(f"# Problem: {problem_description}\n")
        f.write(f"# Desired: {desired_outcome}\n")
        f.write(f"# Original Code:\n")
        for line in current_code_snippet.splitlines():
            f.write(f"#   {line}\n")
        f.write(f"\n{proposed_code}\n\n")

    return f"Proposed code change saved to {file_name}. Please review it manually."

# Example usage (for testing/demonstration)
if __name__ == "__main__":
    sample_code = """
def my_function(x):
    return x * 2
"""
    problem = "The function should add 5 instead of multiplying by 2."
    desired = "The function should return x + 5."
    print(propose_code_change(sample_code, problem, desired))