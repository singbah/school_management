from fastapi import APIRouter, HTTPException, Request, Response, status, Form, File, UploadFile
from datetime import datetime, timedelta
import os

from src.database import db
from src.routes.config.security import create_token
from src.routes.config.settings import USERUPLOAD_FOLDER, MAX_LEN, FILE_EXT
from src.schemas import UserLogin

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