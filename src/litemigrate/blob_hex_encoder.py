class BlobHexEncoder:
    @staticmethod
    def to_blob_literal(data: bytes) -> str:
        if data is None:
            return "NULL"
        hex_str = data.hex().upper()
        return f"X'{hex_str}'"
