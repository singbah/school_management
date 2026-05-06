from fastapi import APIRouter, HTTPException, status, Request, Response, Form, UploadFile, File, Query
from fastapi.responses import FileResponse
from src.database import db
from src.schemas import CreateUser
from src.routes.auths import set_password, verify_password


user_auths_bp = APIRouter(prefix="/api/user/auth")

user_password = {}

@user_auths_bp.post("/register")
def register(CreateUser):
    pass
