from litemigrate.wal_frame_header_parser import WalFrameHeaderParser

def test_wal_frame_header_parser():
    raw = bytes([0] * 24)
    parsed = WalFrameHeaderParser.parse_header(raw)
    assert parsed is not None
    assert parsed["page_number"] == 0
    assert WalFrameHeaderParser.parse_header(b"short") is None
