from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routers import users
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

Base.metadata.create_all(bind=engine)

app.include_router(users.router)


@app.get("/")
def home():
    return {"message": "Welcome to Registration App"}