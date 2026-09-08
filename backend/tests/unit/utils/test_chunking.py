from app.utils.chunk_data import chuckey_chunkey


def test_chuncky_chuncky():
    document = "this is a test document "
    document = [f"{document}{i}" for i in range(1000)   ]
    chunks = chuckey_chunkey(document)

    # check that the every chuck is not bigger than 120 
    assert  all([len(chunk)<= 120 for chunk in chunks ]  )

    #No chunk is empty
    assert  all([len(chunk) > 0 for chunk in chunks])

    # check that chunks overap
    for current_chunk,next_chunk in zip(chunks,chunks[1:]):
        assert current_chunk[-20:] == next_chunk[:20]
    # Check by reconstructing the document
    reconstructed_document:list = chunks[0].copy()
    for chunk in chunks[1:]:
        reconstructed_document.extend(chunk[20:])
    
    assert document == reconstructed_document
    
      
        
        




test_chuncky_chuncky()
