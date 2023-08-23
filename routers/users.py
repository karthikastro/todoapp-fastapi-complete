import sys 
sys.path.append("..")

from fastapi import APIRouter,Depends,Request,Form
from starlette import status
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
import models 
from database import SessionLocal,engine
from .auth import get_current_user,get_hash_password,verify_password
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

router = APIRouter(
    prefix='/users',
    tags=["users"],
    responses={404 :{"detail " : "Not found"}}
)

models.Base.metadata.create_all(bind = engine)

templates = Jinja2Templates(directory="templates")

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

@router.get('/edit-password', response_class = HTMLResponse)
async def edit_user_password(request : Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse('edit-user-password.html',{"request" : request,"user" : user})

@router.post('/edit-password', response_class=HTMLResponse)
async def user_password_change(request : Request,username : str = Form(...),password : str=Form(...),password2 : str = Form(...), db: Session = Depends(get_db)):
    user =await get_current_user(request) 
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    user_model = db.query(models.Users).filter(models.Users.username==username).first()

    msg = "Invalid password or username"

    if user_model is not None:
        if username == user_model.username and verify_password(password,user_model.hashed_password):
           new_hash_password = get_hash_password(password2)
           user_model.hashed_password=new_hash_password
           db.add(user_model)
           db.commit() 
           msg = "password Updated"
    return templates.TemplateResponse("edit-user-password.html",{"request":request,"user":user,"msg":msg})