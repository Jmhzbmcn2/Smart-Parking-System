from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class MeResponse(BaseModel):
    username: str
    role: str


class LoginResponse(MeResponse):
    token: str
