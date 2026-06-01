from fastapi import APIRouter, Request, Response, HTTPException, status, Query
from datetime import datetime, timedelta
from functools import wraps
from bson import ObjectId

from src.database import db
from src.routes.config.security import verify_token
from src.schemas import CreateCourse

def admin_required():

    def decorator(func):
        wraps(func)
        def wrapper(request, *args, **kwargs):
            token = request.cookies.get("access_token")
            payload = verify_token(token)
            if not payload or payload.get("role") != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="unauthorized attempt"
                )
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

admin_dashboard = APIRouter(prefix="/admin/dashboard")


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

@admin_dashboard.post("/create_course")
async def create_course(course_data:CreateCourse, request:Request):
    try:
        payload = verify_token(request.cookies.get("access_token"))
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="you must be an admin"
            )

        new_course = course_data.dict()
        now = datetime.now()
        added_time = now+timedelta(days=31*9)
        academy_year = f"{now.strftime('%Y')}-{added_time.strftime('%Y')}"
        new_course['created_at'] = now
        new_course['updated_at'] = now
        new_course['created_by'] = "admin_id"
        if not new_course.get('academy_year'):
            new_course['academy_year'] = academy_year

        await db.courses.insert_one(new_course)

        return {"detail":"Course Register"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@admin_dashboard.get("/get-staff")
async def get_staff(request:Request, last_id:str=Query(default=None), limit:str=Query(default=100, le=10)):
    try:
        token = request.cookies
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized to access service"
            )
        payload = verify_token(token.get("access_token"))
        query = {}

        if last_id != None:
            query["_id"] = {"$gt":ObjectId(last_id)}

        staffs = []
        cursor = db.facultities.find(query).sort("_id", -1).limit(limit)

        async for c in cursor:
            c["_id"] = str(c["_id"])
            staffs.append(c)
        
        return {"admins":staffs}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@admin_dashboard.post("/assign-course")
async def assign_course(request:Request, staff_id:str, course_id:str):
    try:
        token = request.cookies
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized to access service"
            )
        payload = verify_token(token.get("access_token"))
        if payload['role'].lower() != 'admin':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized to access service"
            )

        staff = await db.facultities.find_one({"_id":ObjectId(staff_id)})
        course = await db.courses.find_one({"_id":ObjectId(course_id)})

        if not course or not staff:
            print("course or instructor does not exist")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="course or teacher does not exist"
            )
        
        for c in staff["assigned_courses"]:
            if not c['course_id']:
                continue
            elif c['course_id'] == course_id:
                print("Course aready added")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="course already added"
                )
            
        staff_fullname = f"{staff['first_name']} {staff['last_name']}"
        now = datetime.now()

        course_update = {
            "instructor_name":staff_fullname,
            "instructor_id":staff['_id'],
            "updated_at":now
        }

        staff_update = {
            "updated_at":now,
            "assigned_courses":[*staff["assigned_courses"], {"course_id":course_id, 
            "created_at":now,
            "course_name":course['course_name']}]
        }


        await db.courses.update_one({"_id":course["_id"]},{"$set":course_update})

        await db.facultities.update_one({"_id":staff["_id"]},{"$set":staff_update})

        return {"detail":"course added"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

