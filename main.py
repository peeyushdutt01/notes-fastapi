from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from database import (
    get_note,
    add_note,
    Note,
    User,
    show_users,
    delete_note_by_id,
    update_note_by_id,
    register,
    login,
    logout
)
from pydantic import BaseModel
from pwdlib import PasswordHash
from tokengenerator import generate_tokens, verify_token, verify_refresh_token
from typing import Optional
import re

app = FastAPI()
password_hash = PasswordHash.recommended()


class NoteModel(BaseModel):
    title: Optional[str] | None = None
    content: Optional[str] | None = None
    is_pinned: Optional[bool] | None = None
    is_archived: Optional[bool] | None = None

class RefreshRequest(BaseModel):
    refresh_token : str

class UserModel(BaseModel):
    username: str
    email: str
    password: str



def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    payload = verify_token(token)
    if payload == None:
        raise HTTPException(
            status_code=401,
            detail="Refresh kar bhosdike"
        )
    return payload


@app.get("/notes")
def show_notes(note_id=None, payload=Depends(get_current_user)):
    user_id = payload["sub"]
    notes = get_note(note_id, user_id)
    if not notes:
        raise HTTPException(status_code=404, detail="Note not found")
    else:
        return [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "modified_at": n.modified_at,
                "created_at": n.created_at,
                "is_pinned": n.is_pinned,
                "is_archived": n.is_archived,
            }
            for n in notes
        ]


@app.post("/notes")
def new_note(data: NoteModel, payload=Depends(get_current_user)):

    note = Note(title=data.title, content=data.content, user_id=payload["sub"])
    note_details = add_note(note)

    return note_details


@app.delete("/notes")
def delete_note(note_id: str, payload=Depends(get_current_user)):
    user_id = payload["sub"]
    deleted = delete_note_by_id(note_id, user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="not found")


@app.patch("/notes")
def update_note(note_id: str, data: NoteModel, payload=Depends(get_current_user)):
    user_id = payload["sub"]
    update_data = data.model_dump(exclude_unset=True)
    
    updated = update_note_by_id(note_id, user_id, update_data)

    if not updated:
        raise HTTPException(status_code=404, detail="Note not found to edit")
    return updated


@app.get("/users")
def get_users():
    users = show_users()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "password": user.password,
            "refresh_token" : user.refresh_token
        }
        for user in users
    ]


@app.post("/register")
def register_user(user_data: UserModel):
    x = r"^[a-zA-Z0-9._/%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if re.match(x, user_data.email):
        pass
    else:
        raise HTTPException(
            status_code=401,
            detail="Wrong email format"
            )
    hash_pwd = password_hash.hash(user_data.password)
    user = User(username=user_data.username, email=user_data.email, password=hash_pwd)
    user = register(user)

    if user is None:
        raise HTTPException(status_code=409, detail="Username or email already exists")
    return {"message": "successfully registered"}


@app.post("/login")
def login_user(response:Response,login_data : dict):
    user_details = login({
        "username":login_data["username"],
        "email":login_data["email"]
        })

    if user_details:
        login_success = password_hash.verify(
            login_data["password"],
            user_details.password
        )

        if not login_success:
            raise HTTPException(
                status_code=401,
                detail="Invalid username/email or password"
            )
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid username/email or password"
        )

    tokens = generate_tokens(
        {
            "sub": user_details.id,
            "username": user_details.username,
        }
    )

    response.set_cookie(
        key="access_token",
        value = tokens["access_token"],
        httponly=True,
        secure=False,
        samesite="lax")

    response.set_cookie(
        key="refresh_token",
        value = tokens["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax")
    
    return {
        "access_token" : tokens["access_token"],
        "refresh_token" : tokens["refresh_token"],
    }

    
@app.post("/refresh")
def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    payload = verify_refresh_token(refresh_token)
    if payload == None:
        raise HTTPException(
            status_code=401,
            detail="refresh token expired ! login again"
        )
    tokens = generate_tokens({
        "sub":payload["sub"],
        "username" :payload["username"]
    })
    
    response.set_cookie(
        key="access_token",
        value = tokens["access_token"],
        httponly=True,
        secure=False,
        samesite="lax")

    response.set_cookie(
        key="refresh_token",
        value = tokens["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax")
    
    return {
        "access_token" : tokens["access_token"],
        "refresh_token" : tokens["refresh_token"],
    }
    
@app.post("/logout")
def logout_user(request: Request, response: Response):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    payload = verify_token(access_token)
    if payload == None:
        payload = verify_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    success = logout({
        "sub":payload["sub"],
        "refresh_token":refresh_token
    })
    
    if success == None:
        raise HTTPException(
            status_code=404,
            detail= "logout failed"
        )
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message" : "successfully logged out"}