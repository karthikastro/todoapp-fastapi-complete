import sys
sys.path.append("..")


from fastapi import Depends,HTTPException,APIRouter,Request,Form
import models
from database import engine,SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel,Field
from typing import Optional
from .auth import get_current_user,get_user_exception

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from starlette.responses import RedirectResponse
from starlette import status

router = APIRouter(
    prefix="/todos",
    tags= ["todos"],
    responses= {404:{"description" : "not found"}}
)

models.Base.metadata.create_all(bind = engine)

templates = Jinja2Templates(directory="templates")


class Todo(BaseModel):
    title : str
    description : Optional[str] = None
    priority : int = Field(gt=0,lt=6,description="the value between 1-5")
    complete : bool



def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()




@router.get('/')  
async def read_all_todo(request : Request, db : Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth",status_code=status.HTTP_302_FOUND)
    todos = db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()

    return templates.TemplateResponse("home.html", {"request" : request,"todos" : todos, "user":user})


@router.get('/add-todo')  
async def addtodo(request : Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth",status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("add-todo.html", {"request" : request,"user":user})

@router.post('/add-todo',response_class = HTMLResponse)
async def create_todo(request : Request,title: str = Form(...),description : str = Form(...),priority : int = Form(...),db : Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth",status_code=status.HTTP_302_FOUND)

    todo_model = models.Todos()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.complete = False
    todo_model.owner_id = user.get("id")
    db.add(todo_model)
    db.commit()

    return RedirectResponse(url='/todos',status_code=status.HTTP_302_FOUND,)

@router.get('/edittodo/{todo_id}',response_class = "HTMLResponse")  
async def edittodo(request : Request, todo_id : int ,db : Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth",status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    return templates.TemplateResponse("edit-todo.html", {"request" : request, "todo" : todo,"user":user})

@router.post('/edittodo/{todo_id}', response_class = "HTMLResponse")
async def edit_todo_commit(request : Request,todo_id : int,title : str = Form(...),description : str = Form(...),priority : int = Form (...),db :Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth",status_code=status.HTTP_302_FOUND)
    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    todo.title = title
    todo.description = description
    todo.priority = priority
    db.add(todo)
    db.commit()
    return RedirectResponse(url= "/todos", status_code=status.HTTP_302_FOUND)

@router.get('/deletetodo/{todo_id}')
async def delete_todo(request : Request,todo_id : int ,db : Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth",status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    if todo_model is None:
        return RedirectResponse(url= "/todos",status_code=status.HTTP_404_NOT_FOUND)

    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
    db.commit()
    return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)

@router.get('/completetodo/{todo_id}',response_class = "HTMLResponse")
async def complete_todo(request : Request,todo_id : int,db : Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth",status_code=status.HTTP_302_FOUND)
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todo_model.complete = not todo_model.complete
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url='/todos',status_code=status.HTTP_302_FOUND  )


@router.get("/user")
async def read_all_by_user(user : dict= Depends(get_current_user), db : Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()
    list1 = db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()
    return list1



@router.get('/{todo_id}')
async def read_todo(todo_id : int,user : dict = Depends(get_current_user),db : Session= Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos)\
                    .filter(models.Todos.id == todo_id)\
                    .filter(models.Todos.owner_id == user.get("id"))\
                    .first()

    if todo_model is not None:
        return todo_model
    else:
        raise http_not_found_except()

@router.post('/')
async def create_todo(todo : Todo, user : dict = Depends(get_current_user),
                                    db : Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = models.Todos()
    todo_model.title = todo.title
    todo_model.description = todo.description 
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()

    return {
        'status ' : 201,
        'transaction' : 'sucessful'
    }

@router.put('/{todo_id}')
async def update_todo(todo_id : int,todo : Todo, user:dict=Depends(get_current_user),db : Session=Depends(get_db)):

    if user is None:
        raise get_user_exception()

    
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id)\
                    .filter(models.Todos.owner_id == user.get("id"))\
                    .first()
    if todo_model is None:
        raise http_not_found_except()
    
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()

    return { 'status ' : 200, 'transaction' : 'sucessful'}

@router.delete('/{todo_id}')
async def delete_todo(todo_id : int, user : dict= Depends(get_current_user),
                                    db : Session = Depends(get_db) ):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos)\
                    .filter(models.Todos.id == todo_id)\
                    .filter(models.Todos.owner_id == user.get("id"))\
                    .first()
    if todo_model is None:
        raise http_not_found_except()
    
    
    db.query(models.Todos)\
                    .filter(models.Todos.id == todo_id)\
                    .delete()
    db.commit()
    return {'status ' : '201 transaction sucessful'}




def http_not_found_except():
    return HTTPException(status_code=404,detail = "Todo not found")
