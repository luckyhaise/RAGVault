from math import ceil
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.database_errors import translate_database_error
from app.core.exceptions.exceptions import AppError, NotFoundError
from app.repositories.documents_repository import (
    get_all_user_documents,
    get_user_document_count,
    user_document_size,
    view_document,
)
from app.schemas.documents_schema import RetrieveAllUserDocuments, RetrieveDocument


async def fetch_all_user_documents(session:AsyncSession,document_command:RetrieveAllUserDocuments,user_id:UUID):
    try:
            limit = document_command.limit
            offset = ((document_command.page -1) *limit)

            documents=await get_all_user_documents(limit=limit,session=session,offset=offset,user_id=user_id)

            total =await get_user_document_count(session=session,user_id=user_id)
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
    except (NotFoundError,AppError):
         raise 
    except SQLAlchemyError as exc:
        raise translate_database_error(exc=exc) from exc
    except Exception as exc:
         raise AppError(public_message="Unexpected error occured. Unable to fetch all documents",internal_message=str(exc),status_code=500,error_code="UNEXPECTED_ERROR") from exc

async def get_user_document(session: AsyncSession, document_command: RetrieveDocument,user_id:UUID) :
    try:
        doc_length = await user_document_size(document_id=document_command.id,session=session,user_id=user_id)
        if document_command.start > doc_length:
            raise NotFoundError(internal_message=f"User id: {user_id} requested start/offset out of bound ",
                public_message="Request out of bound. Please refresh the page",
                status_code=416)
        document = await view_document(user_id=user_id, session=session,
            document_id=document_command.id,
            start=document_command.start, 
            limit=document_command.limit,
            prev=document_command.prev)
        next_start = document_command.start - len(document) if document_command.prev else document_command.start + len(document)
        if document is not None:
            return {
                "items":document,
                "pagination": {
                    "text_length":doc_length,
                    "next_start":next_start,
                    "has_next" : next_start < doc_length,
                    "has_prev": next_start > 1
                    
                }
                
            }
            
        
                         
    except (NotFoundError, AppError):
        raise
    except SQLAlchemyError as exc:
        context = getattr(exc,"context",None)
        print(context)
        # to use figured out later
        raise translate_database_error(exc=exc) from exc
    except Exception as exc:
        raise AppError(public_message="Unexpected error occured. Unable to fetch document", internal_message=str(exc), status_code=500, error_code="UNEXPECTED_ERROR") from exc