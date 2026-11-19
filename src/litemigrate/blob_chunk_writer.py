from typing import Generator, BinaryIO

class BlobChunkWriter:
    @staticmethod
    def chunk_stream(stream: BinaryIO, chunk_size: int = 65536) -> Generator[bytes, None, None]:
        while True:
            data = stream.read(chunk_size)
            if not data:
                break
            yield data
