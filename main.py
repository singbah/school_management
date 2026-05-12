from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, status, Form, File, UploadFile, Request
from fastapi.responses import FileResponse
import os
from datetime import datetime, timedelta
from bson import ObjectId

from src.routes import all_bps
from src.database import db 
from src.routes.config.security import verify_token

USERUPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "user_upload")
FILE_EXT = ["image/jpeg", "image/jpg", "image/png"]
MAX_LEN = 1024*1024*3
os.makedirs(USERUPLOAD_FOLDER, exist_ok=True)

app = FastAPI(title="School Management System", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_headers = ["*"],
    allow_methods = ["*"],
    allow_credentials=True
)

@app.patch("/api/user/set-profile-pic")
async def upgrade_profile_pic(request:Request, picture:UploadFile = File(...)):

    token = request.cookies.get("access_token")
    payload = verify_token(token)

    if picture.content_type not in FILE_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File Type Error!!"
        )
    
    content = await picture.read()
    if len(content) > MAX_LEN:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File Content Too Large"
        )
    
    ext = picture.filename.split(".").pop()
    filename = f"{datetime.now().strftime('%d%m%y%H%M%S')}.{ext}"
    folder_dir = os.path.join(USERUPLOAD_FOLDER, "profile_pic")
    os.makedirs(folder_dir, exist_ok=True)

    photo_path = os.path.join(folder_dir,filename)
    photo_url = f"/profile_pic/{filename}"

    with open(photo_path, "wb") as pf:
        pf.write(content)

    await db.students.update_one({"email":payload["email"]},{"$set":{"profile_pic":photo_url}})

    return {"detail":str(picture.filename)}

for bp in all_bps:
    app.include_router(bp)