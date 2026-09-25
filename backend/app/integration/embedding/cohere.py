import httpx

class CohereEmbeddingService:
   def __init__(self,api_key:str,client:httpx.AsyncClient) -> None:
      self.api_key = api_key,
      self.client = client

   async def embed_documents(self,texts:list[str]):
       url = "https://api.cohere.com/v2/embed"
       payload = { "model":"embed-v4.0",
           "texts": texts,
           "input_type": "search_document",
           "embedding_types": ["float"],
       }
       headers = { "Authorization": f"Bearer {self.api_key}",}

       response = await self.client.post(headers=headers,json=payload,url=url) 
       response.raise_for_status()

       return response.json()["embeddings"]["float"]