from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.documents_schema import RetrieveAllUserDocuments
from math import ceil
from app.core.exceptions.exceptions import NotFoundError, AppError
from app.core.exceptions.database_errors import translate_database_error
from app.repositories.documents_repository import get_all_user_documents , get_user_document_count

async def fetch_all_user_documents(session:AsyncSession,document_command:RetrieveAllUserDocuments):
    try:
            user_id = document_command.user_id
            limit = document_command.limit
            offset = ((document_command.page -1) *limit)

            documents=await get_all_user_documents(limit=limit,session=session,offset=offset,user_id=user_id)

            total =await get_user_document_count(session=AsyncSession,user_id=user_id)
            total_pages = ceil(total/limit) if total > 0 else 1
            if document_command.page > total_pages:
                raise NotFoundError(public_message=f"Page {document_command.page} does not exists. There are only {total_pages} pages",
                                    internal_message=f"Page requested for is out of bounds. user_id:{user_id} page:{document_command.page} total_pages:{total_pages}")
            return {
                "items":documents,
                "pagination":{
                    "total_items":total,
                    "total_pages":total_pages,
                    "has_next": total_pages > document_command.page,
                    "has_previous": document_command.page > 1
                }
            }
    except (NotFoundError,SQLAlchemyError):
         raise 
    except SQLAlchemyError as exc:
        raise translate_database_error(exc=exc)
    except Exception as exc:
         raise AppError(public_message="Unexpected error occured. Unable to fetch all documents",internal_message=str(exc),status_code=500,error_code="UNEXPECTED_ERROR")
