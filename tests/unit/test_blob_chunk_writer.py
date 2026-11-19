import io
from litemigrate.blob_chunk_writer import BlobChunkWriter

def test_blob_chunk_writer():
    data = b"abcdefghij" * 100
    stream = io.BytesIO(data)
    chunks = list(BlobChunkWriter.chunk_stream(stream, chunk_size=50))
    assert len(chunks) == 20
    assert b"".join(chunks) == data
