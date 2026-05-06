from pydantic import BaseModel, EmailStr
from fastapi import Form, File, UploadFile


class CreateUser(BaseModel):
    username:str
