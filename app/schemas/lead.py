from pydantic import BaseModel, field_validator
import re


class LeadFormData(BaseModel):
    first_name: str
    last_name: str
    phone: str
    vehicle_id: str
    vehicle_label: str

    @field_validator("phone")
    @classmethod
    def phone_digits_only(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError("Phone must contain 7–15 digits")
        return digits