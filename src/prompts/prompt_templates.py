from langchain_core.prompts import ChatPromptTemplate
from src.prompts.system_prompts import zero_shot_customer_support_ticket_classifier_system_prompt

customer_support_ticket_classifier_prompt_template = ChatPromptTemplate.from_messages([
    ("system", zero_shot_customer_support_ticket_classifier_system_prompt),
])