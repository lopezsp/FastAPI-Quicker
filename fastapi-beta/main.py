# Python
import itertools
import bcrypt
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
from fastapi import Body, Depends, Header, Path
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import Request

from utils.jwt_manager import create_token
from config.database import engine, Base
from config.database import Session
from models.models import User as UserModel
from models.models import Quick as QuickModel
from middlewares.jwt_bearer import JWTBearer
from utils.jwt_manager import validate_token
from models.models import Followers
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

origins = [
    "http://localhost:5173",
    "https://master--lucent-torrone-6b45b7.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models

class UserBase(BaseModel):
    email: EmailStr = Field(default='user@example.com')
    user_id: int = Field(default= 0)

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
    followers: int = Field(default=0)
        
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
    by: Optional[str] = Field(default=None)

class UpdateQuick(Quick):
    updated_at: Optional[datetime] = Field(default=datetime.now())

 
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
    user_with_same_email = db.query(UserModel).filter(UserModel.email == user.email).first()
    if user_with_same_email:
        return JSONResponse(status_code=400, content={'message': 'Email is already in use'})
    
    users_ids = db.query(UserModel.user_id).all()
    new_user.user_id = len(users_ids)
    user_with_same_id = db.query(UserModel).filter(UserModel.user_id == new_user.user_id).first()
    while user_with_same_id:
        new_user.user_id = new_user.user_id + 1
        user_with_same_id = db.query(UserModel).filter(UserModel.user_id == new_user.user_id).first()

    db.add(new_user)
    db.commit()
    return JSONResponse(status_code=201, content={'message': 'User has been created'})
            
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
    if users:
        decoded_password = bytes.fromhex(users.password[2:]).decode('utf-8')
        user_without_password = users.__dict__
        user_without_password.pop('password', None) 
        if bcrypt.checkpw(user.password.encode('utf-8'), decoded_password.encode('utf-8')):
            token: str = create_token(user.dict())
            return JSONResponse(status_code=200, content={ 'user': jsonable_encoder(user_without_password), 'token': token })
    return JSONResponse(status_code=404, content={'message': 'Password incorrect or user does not exist'})

'''def login(user: UserLogin): 
    db = Session()
    users = db.query(UserModel).filter(UserModel.email == user.email).first()
    decoded_password = bytes.fromhex(users.password[2:]).decode('utf-8')
    if bcrypt.checkpw(user.password.encode('utf-8'), decoded_password):
        token: str = create_token(user.dict())
        return JSONResponse(status_code=200, content=token)
    else:
        return JSONResponse(status_code=404, content={'message': 'Password incorrect or user does not exist'})'''

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
        user_to_follow_id.followers += 1
        db.add(new_follow)
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
        followed_list = db.query(Followers).filter(Followers.follower_id == user_follower.user_id).all()
        for object in followed_list:
            if object.user_followed_id == follow.user_followed_id:
                db.delete(object)
                user_to_unfollow.followers -= 1
                db.commit()
                return JSONResponse(status_code=200, content={'message': 'You unfollowed'})          
                
        return JSONResponse(status_code=404, content={'message': 'You are not following this user'})
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
def show_followed(auth: str = Header(...)):
    db = Session()
    data = validate_token(auth)
    current_user = db.query(UserModel).filter(UserModel.email == data['email']).first()
    my_followed = db.query(Followers).filter(Followers.follower_id == current_user.user_id).all()
    users_followers = [None] * len(my_followed)
    for i, object in enumerate(my_followed):
        users_followers[i] = db.query(UserModel).filter(UserModel.user_id == object.user_followed_id).first()

    exclude_pass = [None] * len(users_followers)

    for i in range(len(users_followers)):
        exclude_pass[i] = User(nick_name='nick_name', first_name='first_name', last_name='last_name')
        exclude_pass[i].user_id = users_followers[i].user_id
        exclude_pass[i].email = users_followers[i].email
        exclude_pass[i].nick_name = users_followers[i].nick_name
        exclude_pass[i].first_name = users_followers[i].first_name
        exclude_pass[i].last_name = users_followers[i].last_name
        exclude_pass[i].birth_date = users_followers[i].birth_date
        exclude_pass[i].followers = users_followers[i].followers
    return JSONResponse(status_code=200, content=jsonable_encoder(exclude_pass))

### Show all followers
@app.get(
    path="/myfollowers",
    response_model=List[User],
    status_code=status.HTTP_200_OK,
    summary="Show my followers",
    tags=["Users"]
)
def show_my_followers(auth: str = Header(...)): 
    """
    This path operation shows all your followers in the app

    Parameters: 
        -

    Returns a json list with all users in the app, with the following keys: 
        - user_id: int
        - email: Emailstr
        - nick_name: str
        - first_name: str
        - last_name: str
        - birth_date: datetime
        - followers
    """
    db = Session()
    data = validate_token(auth)
    current_user = db.query(UserModel).filter(UserModel.email == data['email']).first()
    my_followers = db.query(Followers).filter(Followers.user_followed_id == current_user.user_id).all()
    users_followers = [None] * len(my_followers)
    for i, object in enumerate(my_followers):
        users_followers[i] = db.query(UserModel).filter(UserModel.user_id == object.follower_id).first()

    exclude_pass = [None] * len(users_followers)

    for i in range(len(users_followers)):
        exclude_pass[i] = User(nick_name='nick_name', first_name='first_name', last_name='last_name')
        exclude_pass[i].user_id = users_followers[i].user_id
        exclude_pass[i].email = users_followers[i].email
        exclude_pass[i].nick_name = users_followers[i].nick_name
        exclude_pass[i].first_name = users_followers[i].first_name
        exclude_pass[i].last_name = users_followers[i].last_name
        exclude_pass[i].birth_date = users_followers[i].birth_date
        exclude_pass[i].followers = users_followers[i].followers
    return JSONResponse(status_code=200, content=jsonable_encoder(exclude_pass))

### Show a user
@app.get(
    path="/users/{id}",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Show a User",
    tags=["Users"]
)
def show_a_user(id: str = Path()): 
    db = Session()
    user = db.query(UserModel).filter(UserModel.nick_name == id).first()
    if user:
        user_with_out_password = User(nick_name='nick_name', first_name='first_name', last_name='last_name')
        user_with_out_password.email = user.email
        user_with_out_password.user_id = user.user_id
        user_with_out_password.nick_name = user.nick_name
        user_with_out_password.birth_date = user.birth_date.strftime('%Y-%m-%d')
        user_with_out_password.first_name = user.first_name
        user_with_out_password.last_name = user.last_name
        user_with_out_password.followers = user.followers
        return JSONResponse(status_code=200, content=jsonable_encoder(user_with_out_password))
    else:
        return JSONResponse(status_code=404, content={'message': "User not found!"})

### Delete a user
@app.delete(
    path="/users/delete",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Delete a User",
    tags=["Users"]
)
def delete_a_user(auth: str = Header(...)): 
    db = Session()
    data = validate_token(auth)
    current_user = db.query(UserModel).filter(UserModel.email == data['email']).first()
    quicks_user = db.query(QuickModel).filter(QuickModel.by == current_user.nick_name).all()
    for quick in quicks_user:
        db.delete(quick)
    followed_users = db.query(Followers).filter(Followers.follower_id == current_user.user_id).all()
    for follow in followed_users:
        user = db.query(UserModel).filter(UserModel.user_id == follow.user_followed_id).first()
        user.followers -= 1
        db.delete(follow)
    users_following_me = db.query(Followers).filter(Followers.user_followed_id == current_user.user_id).all()
    for follow in users_following_me:
        db.delete(follow)

    db.delete(current_user)
    db.commit()
    return JSONResponse(status_code=200, content={'message': 'User deleted'})

### Update a user
@app.put(
    path="/users/update",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Update a User",
    tags=["Users"]
)
def update_a_user(new_data: UserRegister = Body(...), auth: str = Header(...)):
        db = Session()
        data = validate_token(auth)
        current_user = db.query(UserModel).filter(UserModel.email == data['email']).first()
        current_user.email = new_data.email
        current_user.nick_name = new_data.nick_name
        current_user.first_name = new_data.first_name
        current_user.last_name = new_data.last_name
        current_user.birth_date = new_data.birth_date
        current_user.password = bcrypt.hashpw(new_data.password.encode('utf-8'), bcrypt.gensalt())
        db.commit()
        return JSONResponse(status_code=200, content={'message': 'Updated'})

## Quicks

### Show quicks (Users you follow)
@app.get(
    path="/",
    response_model=List[Quick],
    status_code=status.HTTP_200_OK,
    summary="Show all quicks",
    tags=["Quicks"]
)
async def home(auth: str = Header(default='0')):
    """
    This path operation shows all quicks of users you follow

    Parameters: 
        -

    Returns a json list with all quicks in the app: 
            quick_id: int  
            content: str    
            created_at: datetime
            updated_at: Optional[datetime]
            by: User (nick_name)
    """
    try:
        data = validate_token(auth)
    except:
        data = None
    if not data:
        db = Session()
        quicks = db.query(QuickModel).all()
        list_quicks = jsonable_encoder(quicks)        
        for obj in list_quicks:
            obj['created_at'] = datetime.fromisoformat(obj['created_at'].replace('Z', '+00:00'))
        reversed_quicks = sorted(list_quicks, key=lambda x:-x['created_at'].timestamp())
        for obj in reversed_quicks:
            obj['created_at'] = obj['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return JSONResponse(status_code=200, content=reversed_quicks)
            
    db = Session()
    current_user = db.query(UserModel).filter(UserModel.email == data['email']).first()
    follows = db.query(Followers).filter(Followers.follower_id == current_user.user_id).all()
    users_i_follow = [None] * len(follows)
    for i, follow in enumerate(follows):
        users_i_follow[i] = db.query(UserModel).filter(UserModel.user_id == follow.user_followed_id).first()
        
    quicks = [None] * len(users_i_follow)
    count = 0
    for user in users_i_follow:
        quicks[count] = db.query(QuickModel).filter(QuickModel.by == user.nick_name).all()
        list_quicks = jsonable_encoder(quicks[count])
        if len(list_quicks) != 0:
            count += 1

    quicks_iterable = jsonable_encoder(quicks)
    quicks_sin_none = [lista for lista in quicks_iterable if lista is not None]
    quicks_list = list(itertools.chain.from_iterable(quicks_sin_none))
    for obj in quicks_list:
        obj['created_at'] = datetime.fromisoformat(obj['created_at'].replace('Z', '+00:00'))
    sorted_list = sorted(quicks_list, key=lambda x:-x['created_at'].timestamp())
    for obj in sorted_list:
        obj['created_at'] = obj['created_at'].strftime('%Y-%m-%d %H:%M:%S')

    return JSONResponse(status_code=200, content=sorted_list)

        
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
            quick_id: int  
            content: str    
            created_at: datetime
            updated_at: Optional[datetime]
            by: User
    """
    db = Session()
    data = request.state.current_user
    if data:
        user = db.query(UserModel).filter(UserModel.email == data['email']).first()
        quick.by = user.nick_name
        new_quick = QuickModel(**quick.dict()) 
        db.add(new_quick)
        db.commit()
        return JSONResponse(status_code=201, content={"message": "You quicked"})
    else:
        return JSONResponse(status_code=400, content={'message': 'You need to log in'})
    

### Show a quick
@app.get(
    path="/quicks/{id}",
    response_model=Quick,
    status_code=status.HTTP_200_OK,
    summary="Show a quick",
    tags=["Quicks"]
)
def show_a_quick(id: int = Path()):
    db = Session()
    quick = db.query(QuickModel).filter(QuickModel.quick_id == id).first()
    if quick:
        return JSONResponse(status_code=200, content=jsonable_encoder(quick))
    else:
        return JSONResponse(status_code=404, content={'message': "Quick not found, may have been deleted"})

### Delete a quick
@app.put(
    path="/quicks/{id}/delete",
    response_model=Quick,
    status_code=status.HTTP_200_OK,
    summary="Delete a quick",
    tags=["Quicks"]
)
def delete_a_quick(id: int = Path(), auth: str = Header(...)):
    db = Session()
    data = validate_token(auth)
    current_user = db.query(UserModel).filter(UserModel.email == data['email']).first()
    quick_to_delete = db.query(QuickModel).filter(QuickModel.quick_id  == id).first()
    if quick_to_delete:           
        if  current_user.nick_name == quick_to_delete.by:
            quick_to_delete.content = 'Quick deleted'
            quick_to_delete.updated_at = datetime.now()
            db.commit()
            return JSONResponse(status_code=200, content={'message': 'Quick Deleted!'})
        else:
            return JSONResponse(status_code=400, content={'message': 'You can not delete this quick'})
    else:
        return JSONResponse(status_code=404, content={'message':'Quick not found!'})

### Update a quick
@app.put(
    path="/quicks/{id}/update",
    response_model=Quick,
    status_code=status.HTTP_200_OK,
    summary="Update a quick",
    tags=["Quicks"]
)
def update_a_quick(id: int = Path(), auth: str = Header(...), new_data: UpdateQuick = Body(...)):
    db = Session()
    data = validate_token(auth)
    current_user = db.query(UserModel).filter(UserModel.email == data['email']).first()
    quick_to_update = db.query(QuickModel).filter(QuickModel.quick_id == id).first()
    if new_data.content == quick_to_update.content:
        return JSONResponse(status_code=400, content={'message': 'No changes'})
    elif current_user.nick_name == quick_to_update.by:
        quick_to_update.content = new_data.content
        quick_to_update.by = current_user.nick_name
        quick_to_update.updated_at = new_data.updated_at
        db.commit()
        return JSONResponse(status_code=200, content={'message': 'Quick updated!'})
    else:
        return JSONResponse(status_code=400, content={'message': 'You can not update this quick'})

    
