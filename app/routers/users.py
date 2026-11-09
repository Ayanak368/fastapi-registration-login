
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models import User
from app.internal.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.dependencies import get_current_user

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Registration page
@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={}
    )


# Registration form submission
@router.post("/register")
def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        return JSONResponse(
            status_code=400,
            content={"message": "Email already registered"}
        )

    hashed_password = hash_password(password)

    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(
    url="/login?registered=success",
    status_code=303
)


# Login page
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )


# Login form submission
@router.post("/login")
def login_user(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        return JSONResponse(
            status_code=401,
            content={"message": "Invalid email or password"}
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    response = RedirectResponse(
        url="/dashboard",
        status_code=303
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=1800
    )

    return response


# Dashboard page
@router.get("/dashboard")
def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"user": current_user}
    )


# Logout
@router.post("/logout")
def logout_user():
    response = RedirectResponse(
        url="/login",
        status_code=303
    )

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
    )

    return response