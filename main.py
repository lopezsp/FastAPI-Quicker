# Python
import json
from datetime import date
from datetime import datetime
from typing import Optional, List

# Pydantic
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field

# FastAPI
from fastapi import FastAPI
from fastapi import status
from fastapi import Body, Depends, Header

from jwt_manager import create_token
from config.database import engine, Base
from config.database import Session
from models.models import User as UserModel
from models.models import Quick as QuickModel
from fastapi.responses import JSONResponse
import bcrypt
from middlewares.jwt_bearer import JWTBearer
from jwt_manager import validate_token
from fastapi import Request
from models.models import Followers

app = FastAPI()

# Models

class UserBase(BaseModel):
    user_id: int = Field(default=9)
    email: EmailStr = Field(default='seba@example.com')

class UserBaseFollow(BaseModel):
    follower_id: int = Field(default=0)
    user_followed_id: int = Field(...)

class UserBaseLogin(BaseModel):
    email: EmailStr = Field(...)

class UserLogin(UserBaseLogin):
    password: str = Field(       
        default='coiastian21'
    )

class User(UserBase):
    nick_name: str = Field(
        ...,
        min_length=1,
        max_length=20
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=50
    )
    birth_date: Optional[date] = Field(default=None)
    followers: Optional[int] = Field(default=0)
    
class UserRegister(User):
    password: str = Field(
        ..., 
        min_length=8,
        max_length=64
    )

class Quick(BaseModel):
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=256
    )
    created_at: datetime = Field(default=datetime.now())
    updated_at: Optional[datetime] = Field(default=None)
    by: Optional[str] = Field(default=None)
 
Base.metadata.create_all(bind=engine)

# Path Operations

## Users

### Register a user
@app.post(
    path="/signup",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Register a User",
    tags=["Users"]
)
def signup(user: UserRegister = Body(...)): 
    """
        Signup

        This path operation register a user in the app

        Parameters: 
            - Request body parameter
                - user: UserRegister
        
        Returns a json with the basic user information: 
            - user_id: int
            - nick_name: str
            - email: Emailstr
            - first_name: str
            - last_name: str
            - birth_date: str
    """
    db = Session()
    new_user = UserModel(**user.dict())
    hashed_password = bcrypt.hashpw(new_user.password.encode('utf-8'), bcrypt.gensalt())
    new_user.password = hashed_password
    users = db.query(UserModel).all()
    for us in users:
        if user.email == us.email:
            return JSONResponse(status_code=400, content={'message': 'Email is already in use'})
    db.add(new_user)
    db.commit()
    return JSONResponse(status_code=201, content={"message": "User has been created"})
            
### Login a user
@app.post(
    path="/login",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Login a User",
    tags=["Users"]
)
def login(user: UserLogin): 
    db = Session()
    users = db.query(UserModel).filter(UserModel.email == user.email).first()
    if bcrypt.checkpw(user.password.encode('utf-8'), users.password):
        token: str = create_token(user.dict())
        return JSONResponse(status_code=200, content=token)
    else:
        return JSONResponse(status_code=404, content={'message': 'Password incorrect or user does not exist'})   

### Follow a user
@app.post(
    path="/follow",
    response_model=List[User],
    status_code=status.HTTP_200_OK,
    summary="Follow a user",
    tags=["Users"]
)
def follow_user(follow: UserBaseFollow = Body(...), auth: str = Header(...)):
    db = Session()
    new_follow = Followers(**follow.dict())
    user_to_follow_id = db.query(UserModel).filter(UserModel.user_id == new_follow.user_followed_id).first()
    if user_to_follow_id:
        data = validate_token(auth)
        user_follower = db.query(UserModel).filter(UserModel.email == data['email']).first()
        new_follow.follower_id = user_follower.user_id
        already_follow = db.query(Followers).filter(Followers.follower_id == user_follower.user_id)
        for object in already_follow:
            if object.user_followed_id == new_follow.user_followed_id:
                return JSONResponse(status_code=400, content={'message': 'You already follow this user'})
            
        if new_follow.follower_id == new_follow.user_followed_id:
                return JSONResponse(status_code=400, content={'message': 'You can not follow yourself'})                   
        db.add(new_follow)
        user_to_follow_id.followers += 1
        db.commit()        
        return JSONResponse(status_code=200, content={'message': 'You followed'})
    else:
        return JSONResponse(status_code=404, content={'message': 'User Not Found!'})

### Unfollow a user
@app.post(
    path="/unfollow",
    response_model=List[User],
    status_code=status.HTTP_200_OK,
    summary="Unfollow a user",
    tags=["Users"]
)
def unfollow_user(unfollow: UserBaseFollow = Body(...), auth: str = Header(...)):
    db = Session()
    follow = Followers(**unfollow.dict())
    user_to_unfollow = db.query(UserModel).filter(UserModel.user_id == follow.user_followed_id).first()
    if user_to_unfollow:
        data = validate_token(auth)
        user_follower = db.query(UserModel).filter(UserModel.email == data['email']).first()
        followed_list = db.query(Followers).filter(Followers.follower_id == user_follower.user_id)
        for object in followed_list:
            if object.user_followed_id == follow.user_followed_id:
                db.delete(object)
                user_to_unfollow.followers -= 1
                db.commit()
                break
            else:
                return JSONResponse(status_code=404, content={'message': 'You are not following this user'})
        return JSONResponse(status_code=200, content={'message': 'You unfollowed'})
    else:
        return JSONResponse(status_code=404, content={'message': 'User Not Found!'})


### Show all followed
@app.get(
    path="/usersfollowed",
    response_model=List[User],
    status_code=status.HTTP_200_OK,
    summary="Show all users i follow",
    tags=["Users"]
)
def show_followed():
    pass

### Show all followers
@app.get(
    path="/followers",
    response_model=List[User],
    status_code=status.HTTP_200_OK,
    summary="Show all followers",
    tags=["Users"]
)
def show_all_followers(): 
    """
    This path operation shows all users in the app

    Parameters: 
        -

    Returns a json list with all users in the app, with the following keys: 
        - user_id: UUID
        - email: Emailstr
        - first_name: str
        - last_name: str
        - birth_date: datetime
    """
    with open("users.json", "r", encoding="utf-8") as f: 
        results = json.loads(f.read())
        return results

### Show a user
@app.get(
    path="/users/{user_id}",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Show a User",
    tags=["Users"]
)
def show_a_user(): 
    pass

### Delete a user
@app.delete(
    path="/users/{user_id}/delete",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Delete a User",
    tags=["Users"]
)
def delete_a_user(): 
    pass

### Update a user
@app.put(
    path="/users/{user_id}/update",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Update a User",
    tags=["Users"]
)
def update_a_user(): 
    pass


## Quicks

### Show  all quicks
@app.get(
    path="/",
    response_model=List[Quick],
    status_code=status.HTTP_200_OK,
    summary="Show all quicks",
    tags=["Quicks"]
)
def home():
    """
    This path operation shows all quicks in the app

    Parameters: 
        -

    Returns a json list with all quicks in the app: 
            quick_id: UUID  
            content: str    
            created_at: datetime
            updated_at: Optional[datetime]
            by: User
    """
    return JSONResponse(status_code=200, content={'message': 'hello quickers'})

## Post a quick
@app.post(
    path="/post",
    response_model=Quick,
    status_code=status.HTTP_201_CREATED,
    summary="Post a quick",
    tags=["Quicks"],
    dependencies=[Depends(JWTBearer())]
)
def post(request: Request, quick: Quick = Body(...)):
    """
        Post a quick

        This path operation post a quick in the app

        Parameters: 
            - Request body parameter
                - quick: quick
        
        Returns a json with the basic quick information: 
            quick_id: UUID  
            content: str    
            created_at: datetime
            updated_at: Optional[datetime]
            by: User
    """
    db = Session()
    data = request.state.current_user
    quick.by = data['email']
    new_quick = QuickModel(**quick.dict()) 
    db.add(new_quick)
    db.commit()
    return JSONResponse(status_code=201, content={"message": "You quicked"})
    

### Show a quick
@app.get(
    path="/quicks/{quick_id}",
    response_model=Quick,
    status_code=status.HTTP_200_OK,
    summary="Show a quick",
    tags=["Quicks"]
)
def show_a_quick(): 
    pass

### Delete a quick
@app.delete(
    path="/quicks/{quick_id}/delete",
    response_model=Quick,
    status_code=status.HTTP_200_OK,
    summary="Delete a quick",
    tags=["Quicks"]
)
def delete_a_quick(): 
    pass

### Update a quicks
@app.put(
    path="/quicks/{quick_id}/update",
    response_model=Quick,
    status_code=status.HTTP_200_OK,
    summary="Update a quick",
    tags=["Quicks"]
)
def update_a_quick(): 
    pass