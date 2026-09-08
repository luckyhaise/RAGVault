
def chuckey_chunkey(doc:str,chunk_size:int = 120,overlap:int = 20) -> list[str]:
    chunks = []
    stride = chunk_size - overlap
    for i in range (0,len(doc),stride):
        chunk = doc[i: i+chunk_size]
        chunks.append(chunk)

        if i + chunk_size >= len(doc):
            break
    return chunks

