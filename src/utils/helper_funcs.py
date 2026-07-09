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


# ── Fake tools (simulating real tool responses) for ReAct prompting example ───────────────
# In a real system these would call actual APIs or databases
def get_order_status(order_id: str) -> str:
    orders = {
        "ORD-001": "Delivered on 2nd July 2026 to 123 Main St.",
        "ORD-002": "Out for delivery. Expected today by 6pm.",
        "ORD-003": "Processing. Estimated dispatch in 2 days.",
        "ORD-004": "Cancelled. Refund of $49.99 issued on 1st July 2026.",
    }
    return orders.get(order_id, f"No order found with ID {order_id}.")


def get_account_balance(account_id: str) -> str:
    accounts = {
        "ACC-101": "Current balance: $120.00. Last payment: $49.99 on 28th June 2026.",
        "ACC-102": "Current balance: $0.00. No pending charges.",
        "ACC-103": "Current balance: $89.50. Payment overdue since 30th June 2026.",
    }
    return accounts.get(account_id, f"No account found with ID {account_id}.")
