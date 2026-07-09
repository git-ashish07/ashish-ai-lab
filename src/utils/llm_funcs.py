from langchain_groq import ChatGroq

def llm_setup(api_key: str, model_name: str = "llama-3.1-8b-instant", temperature: float = 0.0) -> ChatGroq:
    """
    Set up the LLM with the provided API key and model name.

    Args:
        api_key (str): The API key for authentication.
        model_name (str): The name of the model to use. Default is "llama-3.1-8b-instant".

    Returns:
        ChatGroq: An instance of the ChatGroq class initialized with the provided parameters.
    """
    return ChatGroq(
        model=model_name,
        api_key=api_key,
        temperature=temperature,
    )