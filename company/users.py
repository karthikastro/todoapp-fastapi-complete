import sys
sys.path.append("..")

import models
from fastapi import APIRouter,Depends,HTTPException
from database import engine,SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from routers import auth
from routers.auth import get_current_user,verify_password,get_hash_password,get_user_exception

router = APIRouter(
                    prefix="/users",
                    tags=["users"],
                    responses= {404 : {"description" : "not found"}}
)

models.Base.metadata.create_all(bind = engine)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

class UserVerification(BaseModel):
    username : str
    password : str
    new_password : str


@router.get('/')
async def read_all(db : Session = Depends(get_db)):
    return db.query(models.Users).all()

@router.get('/user/{user_id}')
async def read_all_by_user(user_id:int,db : Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.id==user_id).first()

    if user_model is not None:
        return user_model
    return "invalid user id"

@router.put('/update/password')
async def user_password_change(user_verify : UserVerification,user : dict = Depends(get_current_user),db :Session = Depends(get_db)):
    if user is  None:
        raise get_user_exception()

    user_model = db.query(models.Users).filter(models.Users.id == user.get("id")).first()

    if user_model is not None:
        if user_verify.username == user_model.username and verify_password(user_verify.password,user_model.hashed_password):
            user_model.hashed_password= get_hash_password(user_verify.new_password)
            db.add(user_model)
            db.commit()
            return "sucessful"
        return "invalid user or request"

@router.delete('/delete/user')
async def delete_user(user : dict = Depends(get_current_user),db :Session = Depends(get_db)):
    if user is None:
        return "invalid token"
    user_model = db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    if user_model is None:
        return "invalid username or password"
    db.query(models.Users).filter(models.Users.id == user.get("id")).delete()
    db.commit()

    return "User account deleted sucessfully"