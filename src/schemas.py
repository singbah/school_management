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

class UserLogin(BaseModel):
    user_id: str
    password: str

class CreateCourse(BaseModel):
    course_name:str
    schedule:list
    grade_class:str
    academy_year:str=None
    room:str
