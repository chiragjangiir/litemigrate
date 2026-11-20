from litemigrate.blob_hex_encoder import BlobHexEncoder

def test_blob_hex_encoder():
    assert BlobHexEncoder.to_blob_literal(b"abc") == "X'616263'"
    assert BlobHexEncoder.to_blob_literal(None) == "NULL"
