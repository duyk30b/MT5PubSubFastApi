from pydantic import BaseModel, Field


class LoginBody(BaseModel):
    username: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)


class LoginRootBody(BaseModel):
    username: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    userId: int = Field(...)


class RefreshTokenBody(BaseModel):
    refreshToken: str = Field(..., min_length=10)


class LogoutBody(BaseModel):
    refreshToken: str = Field(..., min_length=10)
