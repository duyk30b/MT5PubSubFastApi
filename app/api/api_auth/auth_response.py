from pydantic import Field

from app.core.camel_model import CamelModel


class LoginResponse(CamelModel):
    username: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
