from fastapi import APIRouter

test_controller = APIRouter()


@test_controller.post("/test")
def test():
    return 'Hi, guys.......'
