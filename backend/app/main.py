from fastapi import FastAPI
from app.api.router import api_router
from app.core.exceptions.handlers import register_expection_handler
from app.core.log_config.configarion import configure_logging
import logging
from contextlib import asynccontextmanager

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
   logger.info("Ragvault app started")
   yield
   logger.info("Ragvault app stopped")


app = FastAPI(title="Ragvault", version="1.0.0", lifespan=lifespan)

register_expection_handler(app=app)

app.include_router(api_router)
