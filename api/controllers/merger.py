from fastapi import UploadFile, APIRouter
from fastapi.responses import FileResponse
import bl.services.merger as merger_service


files_controller = APIRouter()


@files_controller.post("/merge")
def upload(file: UploadFile) -> FileResponse:
    return merger_service.merge(file=file)
