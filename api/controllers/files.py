from fastapi import UploadFile, APIRouter
import bl.services.files as files_service

UPLOAD_DIR = "uploads"

files_controller = APIRouter()


@files_controller.post("/upload")
def upload(file: UploadFile):
    return files_service.merge(file=file)
