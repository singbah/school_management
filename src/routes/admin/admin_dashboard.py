from fastapi import APIRouter, Request, Response, HTTPException, status, Query

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
async def get_student(student_id:str = Query(...)):
    pass