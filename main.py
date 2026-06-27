from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from database import get_note,add_note,Note,User,show_users,delete_note_by_id, update_note_by_id,register,login
from pydantic import BaseModel
from pwdlib import PasswordHash
from tokengenerator import create_access_token, verify_token
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
password_hash = PasswordHash.recommended()

class NoteModel(BaseModel):
    title : str
    content : str

class UserModel(BaseModel):
    username : str
    email : str
    password : str

oauth2scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token : str = Depends(oauth2scheme)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    return payload

@app.get("/notes")
def show_notes(note_id = None, payload = Depends(get_current_user)):
    user_id = payload["sub"]
    notes = get_note(note_id,user_id)
    if not notes:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )
    else:
        return [
            {
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "modified_at": n.modified_at,
            "created_at": n.created_at,
            "is_pinned": n.is_pinned,
            "is_archived": n.is_archived 
            }       
            for n in notes
        ]
            
@app.post("/notes")
def new_note(data : NoteModel, payload = Depends(get_current_user)):
    
    note = Note(
        title = data.title,
        content = data.content,
        user_id = payload['sub']
    )
    note_details = add_note(note)
    
    return note_details
    
@app.delete("/notes")
def delete_note(note_id : str, payload = Depends(get_current_user)):
    user_id = payload["sub"]
    deleted = delete_note_by_id(note_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="not found"
        )
         
@app.put("/notes")
def update_note(note_id: str, data:NoteModel, payload = Depends(get_current_user)):
    user_id = payload["sub"]
    note = Note(
        title = data.title,
        content = data.content,
        user_id = user_id
    )
    updated = update_note_by_id(note_id,user_id,note)
    
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Note not found to edit"
        )
   
@app.get("/users")
def get_users():
    users = show_users()
    return [{
        "id" : user.id,
        "username" : user.username,
        "email" : user.email,
        "password" :user.password,
    }
    for user in users
    ]
    
@app.post("/register")
def register_user(user_data: UserModel):
    hash_pwd = password_hash.hash(user_data.password)
    user = User(
        username = user_data.username,
        email = user_data.email,
        password = hash_pwd
    )
    user = register(user)
    
    if user is None:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )
    return {"message":"successfully registered"}
        
@app.post("/login")
def login_user(user_data:UserModel):
    
    user = User(
        username = user_data.username,
        email = user_data.email,
        password = user_data.password
    )
    user_details = login(user)
    if user_details:
        login_success = password_hash.verify(user_data.password,user_details.password)
        if not login_success:  
            raise HTTPException(
                status_code= 400,
                detail="Wrong password, check credentials"
            )
    else:
        raise HTTPException(
            status_code=404,
            detail="user not found"
        )
    
    token = create_access_token({
        "sub" : user_details.id,
        "username" : user_details.username,
    }
    )
    
    return{
        "access_token" : token,
        "token_type" : "bearer",
    }