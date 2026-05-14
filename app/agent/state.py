from langgraph.graph import MessagesState


class State(MessagesState):
    lead_submitted: bool
    crm_lead_id: int | None
    customer_first_name: str | None
    customer_last_name: str | None
    customer_phone: str | None
    customer_email: str | None
    customer_interest: str | None