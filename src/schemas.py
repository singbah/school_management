from pydantic import BaseModel, EmailStr


class CreateStudent(BaseModel):
    first_name: str
    last_name: str 
    email: EmailStr
    birth_date: str
    gender: str
    nationality:str
    phone:str
    password: str

class StudentLogin(BaseModel):
    student_id: str
    password: str

