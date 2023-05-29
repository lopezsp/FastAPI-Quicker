from fastapi.security import HTTPBearer
from fastapi import Request, HTTPException
from utils.jwt_manager import validate_token
from config.database import Session
from models.models import User as UserModel



class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        auth = await super().__call__(request)
        data = validate_token(auth.credentials)
        db = Session()
        user = db.query(UserModel).filter(UserModel.email == data['email']).first()
        if data['email'] != user.email:
               raise HTTPException(status_code=403, detail="Credenciales son invalidas")
        
        request.state.current_user = data
        return auth
    