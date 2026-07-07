from fastapi import UploadFile, File, HTTPException, status

MAX_FILE_SIZE = 50 * 1024 * 1024

ALLOWED_FILE_TYPES = [
    "text/plain",
    "text/csv",
    "text/markdown",
]
async def validate_file(
        text_file: UploadFile = File(...)):
    if text_file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,detail="Only .txt , .csv , .md files are allowed")
    file_bytes = await text_file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE,detail="File size should be with 50 MB")
    try:
     original_file = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
       raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid text encoding")
    title = text_file.filename or "Untitled_document"
    return original_file , title
