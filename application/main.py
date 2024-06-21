# application/__init__.py
from fastapi import FastAPI
from .routers import apirouter
from . import config

app_configs = {"title": "sckeduler-api",
               "HOST": config.HOST,
               "RABBIT_SERVER_URL": config.RABBIT_SERVER_URL}

def create_app():
    app = FastAPI()
    app.include_router(apirouter.router)
    return app
