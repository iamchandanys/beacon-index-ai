import structlog
import jwt
import os

from datetime import datetime, timedelta, timezone
from passlib.hash import bcrypt
from src.models.view_models.user_registration_model import UserRegistrationModel
from src.services.azure.cosmos import CosmosService

class UserRegistrationRepository:
    def __init__(self):
        self.log = structlog.get_logger(self.__class__.__name__)
        self.cosmos_service = CosmosService()
        self.SECRET_KEY = os.getenv("JWT_SECRET_KEY", None)
        self.ALGORITHM = "HS256"
        self.ISSUER = "beacon-index-ai"

    async def register_user(self, user_data: UserRegistrationModel):
        self.log.info("Registering new user")
            
        # Check if user already exists
        existing_users = list(await self.cosmos_service.query_items_async(
            "user-registration",
            "SELECT * FROM c WHERE c.email = @email",
            [
                {"name": "@email", "value": user_data.email}
            ]
        ))
        
        if existing_users:
            self.log.error("User with this email already exists")
            raise ValueError("User with this email already exists.")

        user_data.password = bcrypt.hash(user_data.password)

        await self.cosmos_service.create_item_async("user-registration", user_data.model_dump())
        
        self.log.info("User registered successfully")
        
        return {"message": "User registered successfully."}
    
    def _create_access_token(self, subject: str, extra_claims: dict | None = None, expires_minutes: int = 15) -> str:
        now = datetime.now(timezone.utc)
        
        payload = {
            "sub": subject,  # who the token is about (e.g., user id)
            "iss": self.ISSUER,  # optional but recommended
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=expires_minutes),
            **(extra_claims or {}),
        }

        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    async def login_user(self, email: str, password: str):
        self.log.info("Logging in user")

        users = list(await self.cosmos_service.query_items_async(
            "user-registration",
            "SELECT * FROM c WHERE c.email = @email",
            [
                {"name": "@email", "value": email}
            ]
        ))
        
        if not users:
            self.log.error("Invalid email or password")
            raise ValueError("Invalid email or password.")
        
        if not bcrypt.verify(password, users[0]["password"]):
            self.log.error("Invalid email or password")
            raise ValueError("Invalid email or password.")
        
        access_token = self._create_access_token(
            subject=users[0]["id"],
            extra_claims={"scope": "user", "email": users[0]["email"]},
            expires_minutes=15
        )
        
        self.log.info("User logged in successfully")

        return {
            "message": "User logged in successfully.", 
            "id": users[0]["id"],
            "email": users[0]["email"],
            "access_token": access_token
        }
