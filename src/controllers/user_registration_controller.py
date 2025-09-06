import sys
import structlog

from fastapi import APIRouter, status
from src.repositories.user_registration_repository import UserRegistrationRepository
from src.utils.custom_exception import CustomException
from src.models.view_models.user_registration_model import UserRegistrationModel
from fastapi import HTTPException

router = APIRouter()

class UserRegistrationController:
    def __init__(self):
        self.log = structlog.get_logger(self.__class__.__name__)
        self.repository = UserRegistrationRepository()

    async def register_user(self, user_data: UserRegistrationModel):
        try:
            result = await self.repository.register_user(user_data)
            return result
        
        except ValueError as ve:
            error_msg = CustomException(str(ve), sys).__str__()
            self.log.error("User registration failed", error_msg=error_msg)
            raise HTTPException(status_code=400, detail=f"{ve}")

        except Exception as e:
            error_msg = CustomException(str(e), sys).__str__()
            self.log.error("User registration failed", error_msg=error_msg)
            raise HTTPException(status_code=500, detail=f"Unexpected error during user registration.")
        
    async def login_user(self, email: str, password: str):
        try:
            result = await self.repository.login_user(email, password)
            return result
        
        except ValueError as ve:
            error_msg = CustomException(str(ve), sys).__str__()
            self.log.error("User login failed", error_msg=error_msg)
            raise HTTPException(status_code=400, detail=f"{ve}")

        except Exception as e:
            error_msg = CustomException(str(e), sys).__str__()
            self.log.error("User login failed", error_msg=error_msg)
            raise HTTPException(status_code=500, detail=f"Unexpected error during user login.")

user_registration_controller = UserRegistrationController()

endpoints = [
    {
        "path": "/register",
        "method": "post",
        "handler": user_registration_controller.register_user
    },
    {
        "path": "/login",
        "method": "post",
        "handler": user_registration_controller.login_user
    }
]

# Register the endpoints with the router
for endpoint in endpoints:
    router.add_api_route(
        path=endpoint["path"],
        endpoint=endpoint["handler"],
        methods=[endpoint["method"]],
        status_code=status.HTTP_200_OK
    )
