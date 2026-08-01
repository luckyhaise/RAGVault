import pytest
from app.api.dependencies.upload_file_validation import validate_file
import io
from pathlib import Path

from fastapi.testclient import TestClient
from fastapi import UploadFile , HTTPException
from fastapi import FastAPI

file_path = Path(__file__).with_name("output.txt")
MAX_FILE_SIZE = 50 * 1024 * 1024

ALLOWED_FILE_TYPES = [
    "text/plain",
    "text/csv",
    "text/markdown",
]

@pytest.fixture
def app():
    app = FastAPI()
    return app


@pytest.fixture
def client(app):
    

    return TestClient(app)

@pytest.mark.parametrize(
        ("file_name","file_data","type")
        ,[("wonder.csv","wonder "*100 ,"text/csv"),
          ("test_file.txt", "today is a lucky day" *100, "text/plain"),
           ("markdown_test.md",f"#Markdown test \n {"today is a lucky day" *100}","text/markdown") ]
         
)
def test_validate_file(app,client,file_name,file_data,type):
    @app.post("/validate-file")
    async def file(file:UploadFile):
         original_file , title = await validate_file(text_file=file)
         return original_file , title
         

    file_like_object = io.BytesIO(file_data.encode("utf-8"))
    
    files = {"file": (file_name, file_like_object, type)}

    response = client.post("/validate-file",files=files)
    data = response.json()
  
    file_title = data[1]
    original_text = data[0]
   
    assert file_title == file_name or "Untitled_document"
    assert len(original_text.encode("utf-8")) <= MAX_FILE_SIZE
   
    assert file_data  == original_text
@pytest.mark.asyncio
async def test_validate_file_rejects_file_too_large(app,client):
    @app.post("/size")
    async def operation(file:UploadFile):
       original_text , title = await validate_file(text_file=file)
       return original_text,title
    file_data = "A" * 51 * 1024 * 1024 
    files = {"file":("text.txt",file_data.encode("utf-8"),"text/plain")}
    
    # with pytest.raises(HTTPException) as excinfo:
    response = client.post("/size", files = files)
    assert response.status_code == 413
    assert not response.is_success
    assert response.json().get("detail") == "File size should be with 50 MB"

@pytest.mark.asyncio
async def test_validate_only_accepts_sepcified_files(app,client):
    @app.post("/type")
    async def operation(file:UploadFile):
        original_text , title = await validate_file(text_file=file)
    data = "today is a good day" * 10
    files = {"file":("test_file.rtf",data.encode("ascii"),"application/rtf")}
    response = client.post("/type",files=files)
    assert response.status_code == 415
    assert response.json().get("detail") == "Only .txt , .csv , .md files are allowed"

@pytest.mark.asyncio
async def test_validate_file_rejects_bad_encoding(app,client):
    @app.post("/encoding")
    async def operation(file:UploadFile):
        await validate_file(text_file=file)
    data = "today is a good day" * 10
    file = {"file":("test.txt",data.encode("utf-16"),"text/plain")}
    response = client.post("/encoding",files=file)
    assert response.status_code == 400
    assert response.json().get("detail") == "Invalid text encoding"
