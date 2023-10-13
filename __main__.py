import uvicorn
from fastapi import FastAPI

from api.controllers.merger import files_controller

app = FastAPI()
app.include_router(router=files_controller, tags=['Merger'])


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
