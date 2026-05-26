from fastapi import APIRouter, HTTPException, Request, Response, status, Form, File, UploadFile
from datetime import datetime, timedelta
import os
from bson import ObjectId
from functools import wraps

from src.database import db
from src.routes.config.security import create_token
from src.routes.config.settings import USERUPLOAD_FOLDER, MAX_LEN, FILE_EXT
from src.schemas import UserLogin
from src.routes.config.security import verify_token

def is_student(func):
    @wraps(func)
    def decorator(request, *args, **kwargs):
        token = request.cookies
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="you are not allow to perform this action unless you login"
            )

        payload = verify_token(request.cookies.get("access_token"))
        if not payload:
            print("you are not allow to perform this action unless you login")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="you are not allow to perform this action unless you login"
            )
        return func(request, *args, **kwargs)
    return decorator



student_records = APIRouter(prefix="/api/students/record")

@student_records.patch("/update-student")
async def update_student(request:Request, student_id:str,transcript:UploadFile=File(default=None),  adimi_letter:UploadFile=File(default=None)):
    try:
        if transcript.size > MAX_LEN or adimi_letter.size > MAX_LEN:
            
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="content too large!!\n"
            )
        
        if transcript.content_type not in FILE_EXT or adimi_letter.content_type not in FILE_EXT:
            print("file type not support")
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="file type not supported!!"
            )
        
        student = await db.students.find_one({"student_id":student_id})
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"student doesn't exist with id {student_id}"
            )
        letter_content = await adimi_letter.read()
        transcript_content = await transcript.read()
        
        admin_filename = f"{student['last_name']}_Adimision.{adimi_letter.filename.split('.').pop()}"
        transcript_filename = f"{student['last_name']}_Transcript.{transcript.filename.split('.').pop()}"

        upload_folder = os.path.join(USERUPLOAD_FOLDER, "student_records")
        os.makedirs(upload_folder, exist_ok=True)
        path_url = f"/student_records/"


        now = datetime.now()

        with open(os.path.join(upload_folder,admin_filename), 'wb') as fd:
            fd.write(letter_content)

        with open(os.path.join(upload_folder,transcript_filename), 'wb') as fd:
            fd.write(transcript_content)

        await db.students_admins.insert_one({
            "student_id":student_id,
            "created_at":now,
            "update_at":now,
            "admin_letter_url":path_url + admin_filename,
            "transcript":path_url + transcript_filename
        })
        return {"detail":"data submitted"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@student_records.post("/add_courses")
async def add_cources(course_data:dict, request:Request):
    try:
        payload = verify_token(request.cookies.get("access_token"))
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="not authorized"
            )
        print(payload)
        student = await db.students.find_one({"student_id":course_data.get("student_id")})
        course = await db.courses.find_one({"_id":ObjectId(course_data.get("course_id"))})
        existing_course = await db.student_courses.find_one({"course_id":course_data.get("course_id"),"student_id":course_data.get("student_id")})
        coures_length = await db.student_courses.count_documents({"course_id":course_data.get("course_id")})

        if coures_length >= 35:
            print("session full", coures_length)
            raise HTTPException(
                status_code=status.HTTP_207_MULTI_STATUS,
                detail="section full"
            )
        if existing_course:
            print("You already added this course")
            raise HTTPException(
                status_code=status.HTTP_208_ALREADY_REPORTED,
                detail="course already added"
            )
        if not student:
            print(f"Student with id {course_data.get('student_id')} does not exist")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="student not found"
            )
        if not course:
            print("course not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="course not found"
            )
        
        now=datetime.now()
        now_year = now+timedelta(days=31*9)
        course_data.update({
            "created_at":now, 
            "updated_at":now,
            "added_by":payload['user_id'],
            "course_name":course['course_name'],
            "academy_year":f"{now.strftime('%Y')}-{now_year.strftime('%Y')}"
            })
        
        await db.student_courses.insert_one(course_data)

        return {"detail":"Course added"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@student_records.delete("/drop_course")
async def drop_course(data:dict, request:Request):
    try:
        now = datetime.now()
        next_year = now+timedelta(days=31*9)
        academy_year = f'{now.strftime("%Y")}-{next_year.strftime("%Y")}'
        course = await db.student_courses.find_one({"_id":ObjectId(data.get("course_id"))})

        if not course:
            print("Course not found!!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="course not found!!"
            )
        
        if course["academy_year"] != academy_year:
            print("Can't drop course")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="can't drop course aready pass the year"
            )
        
        await db.student_courses.delete_one({"_id":ObjectId(data.get("course_id"))})
        return{"detail":"course drop"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@student_records.get("/student-courses")
async def get_student_courses(request:Request):
    try:
        all_courses =[]
        now = datetime.now()
        next_year = now+timedelta(days=31*9)
        academy_year = f"{now.strftime('%Y')}-{next_year.strftime('%Y')}"
        payload = verify_token(request.cookies.get("access_token"))
        
        cursor = db.student_courses.find({"student_id":payload.get("user_id"),"academy_year":academy_year}).sort("created_at", -1)

        if not cursor:
            print('cursor not found!!')
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail='cursor not found!!'
            )

        async for c in cursor:
            c["_id"] =str(c["_id"])
            all_courses.append(c)
        
        print(len(all_courses))
        return all_courses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
