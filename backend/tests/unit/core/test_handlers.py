import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarLetteHttpException

from app.core.exceptions.handlers import AppError, register_expection_handler

app = FastAPI()
app = TestClient(app=app)

@pytest.fixture
def app():
    app = FastAPI()
    register_expection_handler(app)
    return app


@pytest.fixture
def client(app):

    return TestClient(app,raise_server_exceptions=False)



def test_app_error_handler(client,app):

    @app.get("/app-error")
    def endpoint():
        raise AppError(public_message="user already exists",
                       internal_message= "duplicate key",
                       error_code="USER_EXISTS",
                       status_code=409)
    response = client.get("/app-error")
    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": 409,
            "error_code": "USER_EXISTS",
            "message": "user already exists",
        }
    }

class Age(BaseModel):
    age:int

def test_validation_error_handler(app,client):
    @app.post("/validation-error")
    def validation(age:Age):
        return
    response = client.post("/validation-error",json={"age":"abc"})
    print(response.status_code)
    assert response.status_code == 422
    body = response.json()
    
    assert  body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "The submitted request data is invalid"
    details = body["error"]["details"][0]  
    assert details["field"] == "body.age"
    assert details["type"] == "int_parsing"
    print(details["type"])

def test_http_exception_handler(app,client):
    @app.post("/http-exception")
    def exception():
        raise HTTPException(status_code=404,detail="resource not found")
    response = client.post("/http-exception")
    assert response.status_code == 404
    detail = response.json()
    assert detail["error"]["code"] == "http_error"
    assert detail["error"]["message"] == "resource not found"

def test_unexpected_exception_handler(app,client):
    
    @app.post("/unexpected-handler")
    def unexpected():
        raise Exception()
    response = client.post("unexpected-handler")
    response.status_code == 500
    detail =  response.json() 
    assert detail["error"]["code"] == "UNEXPECTED_ERROR"
    assert detail["error"]["message"] == "An unexpected server error occured"

def test_exception_handlers_registered(app):

    handlers = app.exception_handlers

    assert AppError in handlers
    assert RequestValidationError in handlers
    assert StarLetteHttpException in handlers
    assert Exception in handlers