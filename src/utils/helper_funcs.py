import re
from typing import Callable
from langchain.messages import AIMessage, HumanMessage
from langchain_groq import ChatGroq

def parse_category(response: str) -> str | None:
    """
    Extracts the category from the LLM response.

    Args:
        response (str): The response from the LLM.
    Returns:
        str | None: The parsed category, or None if it cannot be determined.
    """
    
    # Iterate through each line of the response to find the category
    for line in response.strip().split("\n"):
        # Check if the line starts with "Category:" and extract the category
        if line.startswith("Category:"):
            # Remove the "Category:" prefix and any leading/trailing whitespace, then return the category
            return line.replace("Category:", "").strip()
    return None


# --- Fake tools (simulating real tool responses) for ReAct prompting example ----------------------
# In a real system these would call actual APIs or databases
def get_order_status(order_id: str) -> str:
    """
    Returns the status of the specified order.

    Args:
        order_id (str): The ID of the order to check.
    Returns:
        str: The status of the order or a message indicating that the order was not found.
    """

    orders = {
        "ORD-001": "Delivered on 2nd July 2026 to 123 Main St.",
        "ORD-002": "Out for delivery. Expected today by 6pm.",
        "ORD-003": "Processing. Estimated dispatch in 2 days.",
        "ORD-004": "Cancelled. Refund of $49.99 issued on 1st July 2026.",
    }
    return orders.get(order_id, f"No order found with ID {order_id}.")


def get_account_balance(account_id: str) -> str:
    """
    Returns the balance of the specified account.
    
    Args:
        account_id (str): The ID of the account to check.
    Returns:
        str: The account balance or a message indicating that the account was not found.
    """
    accounts = {
        "ACC-101": "Current balance: $120.00. Last payment: $49.99 on 28th June 2026.",
        "ACC-102": "Current balance: $0.00. No pending charges.",
        "ACC-103": "Current balance: $89.50. Payment overdue since 30th June 2026.",
    }
    return accounts.get(account_id, f"No account found with ID {account_id}.")

# template of react agent function to simulate the ReAct prompting for customer support
# this can be used for any use case by changing the system prompt and tools
def run_react_agent(
    llm: ChatGroq,
    prompt_template: str,
    input_variables: dict,
    tools: dict[str, Callable],
    tool_descriptions: str,
    max_steps: int = 5
) -> str:
    """
    Reusable ReAct agent that works for any use case.

    Args:
        llm: the language model to use
        prompt_template: prompt template with {tool_descriptions} placeholder at minimum
        input_variables: dict of all variables to inject into the human message template
            e.g. {"customer_id": "ACC-101", "query": "..."}
        tools: dict mapping tool name strings to callable Python functions
            e.g. {"get_order_status": get_order_status}
        tool_descriptions: string describing available tools — gets injected into {tool_descriptions} in the system prompt
        max_steps: maximum number of Thought/Action/Observation loops before stopping (default 5)

    Returns:
        Final answer string from the model
    """

    # Format initial messages
    # Merge tool_descriptions + input_variables into one dict for template formatting
    all_variables = {
        "tool_descriptions": tool_descriptions,
        **input_variables
    }

    messages = prompt_template.format_messages(**all_variables)

    print(f"Input: {input_variables}\n")

    # Loop through Thought/Action/Observation steps
    for step in range(max_steps):

        print(f"------------- Step {step + 1} of {max_steps}---------------\n")
        # call the LLM with the current messages
        response = llm.invoke(messages)
        response_text = response.content
        print(response_text)

        # check if the response contains a final answer
        if "Final Answer:" in response_text:
            final = response_text.split("Final Answer:")[-1].strip()
            return final

        # parse the action and tool input from the response
        action_match = re.search(
            r"Action:\s*(\w+)\(([^)]+)\)",
            response_text
        )

        # If no action is found, we stop the loop
        if not action_match:
            print("No action found — stopping.")
            break

        # Extract tool name and input from the matched action
        tool_name = action_match.group(1).strip()
        # Extract the tool input, handling potential quotes and whitespace
        tool_input = (
            action_match.group(2)
            .strip()
            .strip('"')
            .strip("'")
            .split("=")[-1]
            .strip()
            .strip('"')
            .strip("'")
        )

        # Call the corresponding tool function and get the observation
        if tool_name in tools:
            real_observation = tools[tool_name](tool_input)
        else:
            real_observation = f"Error: tool '{tool_name}' not found."

        print(f"\nObservation: {real_observation}\n")

        # Append the observation to the messages for the next loop iteration
        messages.append(AIMessage(content=response_text))
        messages.append(HumanMessage(
            content=f"Observation: {real_observation}"
        ))

    return "Max steps reached without a final answer."
    

# --- Self refine helper functions -------------------------------------------
def parse_critique(critique: str) -> bool:
    """
    Checks if the critic said PASSED: yes
    
    Args:
        critique (str): The critique text from the critic LLM.
    Returns:
        bool: True if the critique indicates the draft passed, False otherwise.
    """

    for line in critique.strip().split("\n"):
        if line.strip().lower().startswith("passed:"):
            return "yes" in line.lower()
    return False

def self_refine(complaint: str, prompt_dict, llm: ChatGroq, llm_critic: ChatGroq, llm_refiner: ChatGroq, max_iterations: int = 3) -> str:
    """
    Self-refine loop for generating and refining a customer support email.
    
    Args:
        complaint (str): The customer complaint to address.
        prompt_dict (dict): Dictionary containing the generator, critic, and refiner prompts.
        llm (ChatGroq): The language model for generating and refining the email.
        llm_critic (ChatGroq): The language model for critiquing the email.
        llm_refiner (ChatGroq): The language model for refining the email.
        max_iterations (int): Maximum number of refinement iterations (default is 3).
    Returns:
        str: The final refined email draft.
    """
    
    # Generate initial draft email based on the customer complaint
    generator_prompt_template = prompt_dict['generator']

    generator_chain = generator_prompt_template | llm
    draft = generator_chain.invoke({"complaint": complaint}).content

    print("-"*50)
    print("INITIAL DRAFT")
    print("-"*50)
    print(draft)

    # refine loop
    for iter in range(max_iterations):
        print(f"\n{'=' * 50}")
        print(f"CRITIQUE (iteration {iter + 1})")
        print("=" * 50)

        # Critique the draft
        critic_prompt_template = prompt_dict['critic']

        critic_chain = critic_prompt_template | llm_critic
        critique = critic_chain.invoke({
            "complaint": complaint,
            "email_draft": draft
        }).content

        print(critique)

        # Check if it passed the critique
        if parse_critique(critique):
            print(f"\nDraft passed the critique on iteration {iter + 1}. No further refinement needed.")
            break

        print(f"\n{'=' * 50}")
        print(f"REFINED DRAFT (iteration {iter + 1})")
        print("=" * 50)

        # Refine the draft based on critique
        refiner_prompt_template = prompt_dict['refiner']

        refiner_chain = refiner_prompt_template | llm_refiner
        draft = refiner_chain.invoke({
            "complaint": complaint,
            "email_draft": draft,
            "critique": critique
        }).content

        print(draft)

    print(f"\n{'=' * 50}")
    print(f"FINAL DRAFT")
    print("=" * 50)
    print(draft)

    return draft