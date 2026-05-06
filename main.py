from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, status, Form, File, UploadFile
from pydantic import BaseModel
from src.routes import all_bps

app = FastAPI(title="School App")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5173"],
    allow_headers = ["*"],
    allow_methods = ["*"],
    allow_credentials=True
)


for bp in all_bps:
    app.include_router(bp)