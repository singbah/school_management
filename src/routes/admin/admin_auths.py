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
async def login(login_data:UserLogin, request:Request, response:Response):
    print(login_data)
    try:
        now = datetime.now()
        ip = request.client.host
        user = await db.admins.find_one({"admin_id": login_data.user_id})
        if not user:
            print("User not found with student_id:", login_data.user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.get("lockout_time") and now < user["lockout_time"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked. Please try again later."
            )
        if not verify_password(login_data.password, user["password"]):
            await db.admins.update_one({"admin_id": login_data.user_id}, {"$inc": {"failed_attempts": 1}})
            if user["failed_attempts"] + 1 >= MAX_FAILED_ATTEMPTS:
                lockout_time = now + LOCKOUT_DURATION
                await db.admins.update_one({"admin_id": login_data.user_id}, {"$set": {"lockout_time": lockout_time}})
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is locked due to too many failed login attempts. Please try again later."
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        await db.admins.update_one({"admin_id": login_data.user_id}, {"$set": {"failed_attempts": 0, "lockout_time": None, "last_login": now, "last_ip": ip}})

        token_data = {
            "user_id": user["admin_id"],
            "email": user["email"],
            'role': user['role']
        }

        access_token = create_token(token_data)
        refresh_token = create_token(token_data, expires_delta=60*24*7)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="none",
        )
    
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
        )

        user['_id'] = str(user["_id"])
        user['password'] = None

        return {'detail':user}

    except Exception as e:
        print("Error during login:", str(e))
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
        
        admin = await db.admins.find_one({"admin_id":payload.get("user_id") })

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


