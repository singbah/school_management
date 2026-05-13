from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Response, Request, Query
from bson import ObjectId
import uuid


from src.schemas import UserLogin
from src.database import db
from src.routes.config.security import verify_token, create_token, validate_phone
from src.routes.auths import set_password, verify_password

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=5)

admin_auths = APIRouter(prefix="/admin/auths")

@admin_auths.post("/login")
async def login(admin_log:UserLogin, request:Request, response:Response):
    try:
        admin_id = admin_log.user_id
        password = admin_log.password
        now = datetime.now()

        admin = await db.admins.find_one({"_id": admin_id})
        if not admin:
            print("Admin not found with admin_id:", admin_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        if admin.get("lockout_time") and now < admin["lockout_time"]:
            remaining_lockout = (admin["lockout_time"] - now).seconds // 60
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked. Try again in {remaining_lockout} minutes."
            )
        if not verify_password(password, admin["password"]):
            failed_attempts = admin.get("failed_attempts", 0) + 1
            update_data = {"failed_attempts": failed_attempts}
            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                update_data["lockout_time"] = now + LOCKOUT_DURATION
            await db.admins.update_one({"_id": admin_id}, {"$set": update_data})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        await db.admins.update_one({"_id", admin.get("_id")},{"$set":{"failed_attempts":0, "lockout_time":None}, "last_login":now})

        user_data = {"user_id":admin.get("_id"), "role":"admin", "email":admin.get("email")}
        access_token = create_token(user_data, 60*24*7)
        refresh_token = create_token(user_data, 60*24*30)

        response.set_cookie(
            key="access_token",
            value=access_token,
            secure=True,
            samesite="None",
            httponly=True
            )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            secure=True,
            samesite="None",
            httponly=True
            )
        
        admin['_id'] = str(admin['_id'])
        return {'detail':admin}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@admin_auths.get("/me")
async def get_admin(request:Request):
    try:
        token = request.cookies.get("access_token")
        payload = verify_token(token)
        if not payload or payload.get("role") != 'admin':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="unauthorized attempt"
            )
        
        admin = await db.admins.find_one({"_id",ObjectId(payload.get("user_id")) })

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found")

        admin["_id"] = str(admin["_id"])
        return {"detail":admin}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@admin_auths.post("/logout")
async def student_logout(response:Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message":"Logged out successfully"}


@admin_auths.post("/refresh")
async def refresh_token(request:Request, response:Response):
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing"
            )
        payload = verify_token(refresh_token)
        admin = await db.admins.find_one({"_id", ObjectId(payload.get("_id"))})
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="admin error!!"
            )
        
        payload["exp"] = datetime.now() + timedelta(minutes=60*24*7)
        new_access_token = create_token(payload)
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="none",
        )
        
        admin['_id'] = str(admin["_id"])
        admin["password"] = None
        return admin
    except Exception as e:
        print("Error refreshing token:", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@admin_auths.post("/forgot-password")
async def forgot_password(request:Request, email:str=Query(...)):
    try:
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="you didn't enter your email"
            )
        admin = await db.admins.find_one({"email": email})
        otp_code =uuid.uuid4().hex[0:6]
        now = datetime.now()
        ip = request.headers.get("host")
        print(ip)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='admin not found with email'
            )
        
        OTPS = {
            "email":admin['email'],
            "ip":ip,
            'code':otp_code,
            "created_at":now,
            "expire_at":now + timedelta(minutes=5)
            }
        
        reset_link = f'http://localhost:8000/admin/password/reset?email={email}&&code={otp_code}'
        msg = f"click the link below to reset password.\nthe link expire in 5 minutes\n{reset_link}"
        # await send_email("Password Reset", email, msg, "admin.get("last_name")")
        await db.OTPS.insert_one(OTPS)

        return {"detail":msg}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

