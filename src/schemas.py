from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta


class CreateStudent(BaseModel):
    first_name: str
    last_name: str 
    email: EmailStr
    birth_date: str
    gender: str
    nationality:str
    phone:str
    password: str

class CreateFacultity(BaseModel):
    created_at:str=datetime.now()
    first_name: str
    last_name: str 
    email: EmailStr
    birth_date: str
    gender: str
    nationality:str
    phone:str
    password: str
    salary:float=None
    address:str=None

class UserLogin(BaseModel):
    user_id: str
    password: str

class CreateCourse(BaseModel):
    course_name:str
    schedule:list
    grade_class:str
    room:str
    academy_year:str=None
