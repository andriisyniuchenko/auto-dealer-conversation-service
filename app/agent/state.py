from langgraph.graph import MessagesState


class State(MessagesState):
    # Lead info
    lead_submitted: bool
    crm_lead_id: int | None
    customer_first_name: str | None
    customer_last_name: str | None
    customer_phone: str | None
    customer_email: str | None
    customer_interest: str | None
    # Contact collection tracking
    asked_for_name: bool
    asked_for_phone: bool
    # Test drive
    test_drive_asked: bool
    wants_test_drive: bool | None
    # Appointment
    asked_for_datetime: bool
    appointment_at: str | None
    appointment_booked: bool
    # Chat status
    chat_complete: bool