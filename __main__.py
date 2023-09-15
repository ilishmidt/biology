import uvicorn
from fastapi import FastAPI

from api.controllers.files import files_controller
from api.controllers.test import test_controller

app = FastAPI()
app.include_router(router=files_controller, tags=['Files'])
app.include_router(router=test_controller, tags=['Test'])


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
