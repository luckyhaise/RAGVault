
type contentType = "application/json" | "multipart/form-data" 

export async function apiRequest<T>(data:unknown,url:string,contentType:contentType) :Promise<T>{
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": contentType,
      
    },
    body: JSON.stringify(data),
  },)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error instanceof Error ? error.message : "Request Failed")
  }
  const result = await response.json()
  return result
} 