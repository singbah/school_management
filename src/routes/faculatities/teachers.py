from fastapi import APIRouter, Request, HTTPException, status
from datetime import datetime, timedelta

from src.routes.config.security import verify_token
from src.database import db

teacher_bp = APIRouter(prefix="/api/teacher")

@teacher_bp.get("/get_students")
async def get_students(request:Request, course_id:str, academy_year:str):
    try:
        token = request.cookies.get("access_token")
        payload = verify_token(token)
        role = payload.get("role")
        if not payload or role not in ['admin', 'staff']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized attempt"
            )
        
        students = []
        cursor = db.student_courses.find({"course_id":course_id,"academy_year":academy_year}).sort("_id", -1)

        async for c in cursor:
            c["_id"] = str(c["_id"])
            students.append(c)
        
        return {"users":students}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

