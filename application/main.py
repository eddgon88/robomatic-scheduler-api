# application/__init__.py
from fastapi import FastAPI
from .routers import apirouter

def create_app():
    app = FastAPI()
    app.include_router(apirouter.router)
    return app
