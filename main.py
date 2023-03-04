# Python
import json
from uuid import UUID
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
from fastapi import Body

app = FastAPI()

# Models

class UserBase(BaseModel):
    user_id: UUID = Field(...)
    email: EmailStr = Field(...)

class UserLogin(UserBase):
    password: str = Field(
        ..., 
        min_length=8,
        max_length=64
    )

class User(UserBase):
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

class UserRegister(User):
    password: str = Field(
        ..., 
        min_length=8,
        max_length=64
    )

class Quick(BaseModel):
    Quick_id: UUID = Field(...)
    content: str = Field(
        ..., 
        min_length=1, 
        max_length=256
    )
    created_at: datetime = Field(default=datetime.now())
    update_at: Optional[datetime] = Field(default=None)
    by: User = Field(...)

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
            - user_id: UUID
            - email: Emailstr
            - first_name: str
            - last_name: str
            - birth_date: str
    """
    with open("users.json", "r+", encoding="utf-8") as f: 
        results = json.loads(f.read())
        user_dict = user.dict()
        user_dict["user_id"] = str(user_dict["user_id"])
        user_dict["birth_date"] = str(user_dict["birth_date"])
        results.append(user_dict)
        f.seek(0)
        f.write(json.dumps(results))
        return user

      

### Login a user
@app.post(
    path="/login",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Login a User",
    tags=["Users"]
)
def login(): 
    pass

### Show all users
@app.get(
    path="/users",
    response_model=List[User],
    status_code=status.HTTP_200_OK,
    summary="Show all users",
    tags=["Users"]
)
def show_all_users(): 
    pass

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
    return {"Quicker API": "Working!"}

### Post a quick
@app.post(
    path="/post",
    response_model=Quick,
    status_code=status.HTTP_201_CREATED,
    summary="Post a quick",
    tags=["Quicks"]
)
def post(): 
    pass

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