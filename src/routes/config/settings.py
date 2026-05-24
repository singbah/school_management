import os

USERUPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "user_upload")
FILE_EXT = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
MAX_LEN = 1024*1024*6.5
os.makedirs(USERUPLOAD_FOLDER, exist_ok=True)