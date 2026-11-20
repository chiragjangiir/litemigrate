import struct
from typing import Optional, Dict

class WalFrameHeaderParser:
    FRAME_HEADER_SIZE = 24

    @staticmethod
    def parse_header(data: bytes) -> Optional[Dict[str, int]]:
        if len(data) < WalFrameHeaderParser.FRAME_HEADER_SIZE:
            return None
        page_num, commit_records, salt1, salt2, chk1, chk2 = struct.unpack(">IIIIII", data[:24])
        return {
            "page_number": page_num,
            "commit_records": commit_records,
            "salt1": salt1,
            "salt2": salt2,
            "checksum1": chk1,
            "checksum2": chk2
        }
