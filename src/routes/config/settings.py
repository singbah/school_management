import os

USERUPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "user_upload")
os.makedirs(USERUPLOAD_FOLDER, exist_ok=True)

FILE_EXT = ["image/jpeg", "image/jpg", "image/png", "application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]

MAX_LEN = 1024*1024*6.5