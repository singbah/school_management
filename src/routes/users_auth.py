from fastapi import APIRouter, HTTPException, status, Request, Response, Form, UploadFile, File, Query
from fastapi.responses import FileResponse
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.database import db
from src.schemas import CreateStudent, StudentLogin
from src.routes.auths import set_password, verify_password, send_email
from src.routes.config.security import create_token, verify_token, validate_phone
import uuid

load_dotenv()
MAX_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=5)

user_auths_bp = APIRouter(prefix="/api/user/auths")

@user_auths_bp.post("/register")
async def student_register(user:CreateStudent, request:Request, response:Response):
    try:
        now = datetime.now()
        if user.phone:
            validate_phone(user.phone)

        existing_user = await db.students.find_one({"$or":[{"email":user.email}, {"phone":user.phone}]})

        if existing_user:
            print("User already exists with email or phone:", user.email, user.phone)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or phone already exists"
            )
        
        hashed_password = set_password(user.password)
        user_dict = user.dict()

        user_dict["password"] = hashed_password
        user_dict["created_at"] = now
        user_dict["updated_at"] = now
        user_dict["student_id"] = str(uuid.uuid4().int)[0:4]
        user_dict["failed_attempts"] = 0
        user_dict["lockout_time"] = None
        await db.students.insert_one(user_dict)

        return {"message":"User registered successfully"}
    
    except Exception as e:
        print("Error during registration:", str(e)) 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@user_auths_bp.post("/login")
async def student_login(login_data:StudentLogin, request:Request, response:Response):
    print(login_data)
    try:
        now = datetime.now()
        ip = request.client.host
        user = await db.students.find_one({"student_id": login_data.student_id})
        if not user:
            print("User not found with student_id:", login_data.student_id)
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
            await db.students.update_one({"student_id": login_data.student_id}, {"$inc": {"failed_attempts": 1}})
            if user["failed_attempts"] + 1 >= MAX_ATTEMPTS:
                lockout_time = now + LOCKOUT_DURATION
                await db.students.update_one({"student_id": login_data.student_id}, {"$set": {"lockout_time": lockout_time}})
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is locked due to too many failed login attempts. Please try again later."
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        await db.students.update_one({"student_id": login_data.student_id}, {"$set": {"failed_attempts": 0, "lockout_time": None, "last_login": now, "last_ip": ip}})

        token_data = {
            "student_id": user["student_id"],
            "email": user["email"],
            'role': 'student'
        }

        access_token = create_token(token_data)
        refresh_token = create_token(token_data, expires_delta=60*60*24*7)

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

@user_auths_bp.post("/logout")
async def student_logout(response:Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message":"Logged out successfully"}

@user_auths_bp.get("/me")
async def get_current_user(request:Request):
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        payload = verify_token(token)
        student_id = payload.get("student_id")
        user = await db.students.find_one({"student_id": student_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        user['_id'] = str(user["_id"])
        user['password'] = None
        return user
    except Exception as e:
        print("Error fetching current user:", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@user_auths_bp.post("/refresh")
async def refresh_token(request:Request, response:Response):
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing"
            )
        payload = verify_token(refresh_token)
        student_id = payload.get("student_id")
        user = await db.students.find_one({"student_id": student_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        token_data = {
            "student_id": user["student_id"],
            "email": user["email"],
            'role': 'student'
        }

        new_access_token = create_token(token_data)
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="none",
        )
        
        user['_id'] = str(user["_id"])
        user["password"] = None
        return user
    except Exception as e:
        print("Error refreshing token:", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@user_auths_bp.patch("/update")
async def update_student(student_data:dict, request:Request):
    try:
        student_id = student_data.get("student_id")
        db_user = await db.students.find_one({"student_id":student_id})
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user not found"
            )
        data_to_update = {}
        db_user["_id"] = str(db_user["_id"])
        for key, value in student_data.items():
            if key in db_user.keys():
                db_user[key] = value
                data_to_update[key] = value

        await db.students.update_one({"student_id":student_id},{"$set":data_to_update})

        return {"detail":db_user}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@user_auths_bp.post("/forgot-password")
async def forgot_password(request:Request, email:str=Query(...)):
    try:
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="you didn't enter your email"
            )
        user = await db.students.find_one({"email": email})
        otp_code =uuid.uuid4().hex[0:6]
        now = datetime.now()
        ip = request.headers.get("host")
        print(ip)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='user not found with email'
            )
        
        OTPS = {
            "email":user['email'],
            "ip":ip,
            'code':otp_code,
            "created_at":now,
            "expire_at":now + timedelta(minutes=5)
            }
        
        await db.OPTS.insert_one(OTPS)

        return {"detail":"Check your email for the OTP CODE"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@user_auths_bp.patch("reset_password")
async def check_otp(request:Request, response:Response, otp_code:str=Query(...), email:str=Query(...)):
    try:
        cursor = db.OPTS.find({"email":email}).sort({"created_at":-1}).limit(1)
        otps = []
        if not cursor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Code Error"
            )
        async for code in cursor:
            otps.append(code)

        otp_ = otps[0]


        if otp_.get("code") != otp_code.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wrong Error"
            )

        if otp_.get("expire_at") > datetime.now() and otp_.get("code") == otp_code.strip():
            reset_link = f'http://localhost:8000/user/password/reset?email={email}&&code={otp_code}'
            msg = f"click the link below to reset password.\nthe link expire in 5 minutes\n{reset_link}"
            
            send_email("Password", email, msg, "User")
            return {"detail":msg}
        
        if otp_['expire_at'] < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="CODE EXPIRED"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=str(e)
        )