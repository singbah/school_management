from fastapi import APIRouter, Request, Response, HTTPException, status, Query, routing

from src.database import db
from src.routes.config.security import verify_token

admin_dashboard = APIRouter(prefix="/admin/dashboard")

@admin_dashboard.get("/get_students")
async def get_students(request:Request):
    try:
        token = request.cookies.get("access_token")
        payload = verify_token(token)
        if not payload or payload.get("role") != 'admin':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized attempt"
            )
        
        students = []
        cursor = db.students.find().sort("_id", -1).limit(100)

        async for c in cursor:
            c["_id"] = str(c["_id"])
            students.append(c)
        
        return {"users":students}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@admin_dashboard.get("/student")
async def get_student(request:Request, student_id:str = Query(...)):
    try:
        token = request.cookies.get("access_token")
        payload = verify_token(token)
        if not payload or payload.get("role") != 'admin':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized attempt"
            )
        
        student = await db.students.find_one({"student_id": student_id})

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found")
        
        student["_id"] = str(student["_id"])
        return {"user": student}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@admin_dashboard.get("/get_admins")
async def get_admins(request:Request):
    try:
        token = request.cookies.get("access_token")
        payload = verify_token(token)
        if not payload or payload.get("role") != 'admin':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized attempt"
            )
        
        admins = []
        cursor = db.admins.find().sort("_id", -1).limit(100)

        async for c in cursor:
            c["_id"] = str(c["_id"])
            admins.append(c)
        
        return {"admins":admins}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@admin_dashboard.get("/admin")
async def get_admin(request:Request, admin_id:str = Query(...)):
    try:
        token = request.cookies.get("access_token")
        payload = verify_token(token)
        if not payload or payload.get("role") != 'admin':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized attempt"
            )
        
        admin = await db.admins.find_one({"admin_id": admin_id})

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found")
        
        admin["_id"] = str(admin["_id"])
        return {"user": admin}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@admin_dashboard.get("/courses")
async def get_courses(request:Request):
    try:
        token = request.cookies.get("access_token")
        payload = verify_token(token)
        if not payload or payload.get("role") != 'admin':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized attempt"
            )
        
        courses = []
        cursor = db.courses.find().sort("_id", -1).limit(100)

        async for c in cursor:
            c["_id"] = str(c["_id"])
            courses.append(c)
        
        return {"courses":courses}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )