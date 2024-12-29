from pydantic import BaseModel

# Pydantic models for requests
class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str

