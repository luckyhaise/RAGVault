
from  fastapi import FastAPI , HTTPException
from app.api.router import api_router
from app.core.exceptions.handlers import register_expection_handler

app = FastAPI(title = "Ragvault",version="1.0.0")
register_expection_handler(app=app)
# INITIALIZE ALL THE TABLES FOR DATABASE 
# models.Base.metadata.drop_all(bind=database.engine)

app.include_router(api_router)