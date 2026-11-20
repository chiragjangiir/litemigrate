import hashlib

class MigrationChecksumVerifier:
    @staticmethod
    def verify(script_content: str, recorded_sha256: str) -> bool:
        if not script_content or not recorded_sha256:
            return False
        computed = hashlib.sha256(script_content.encode("utf-8")).hexdigest()
        return computed.lower() == recorded_sha256.lower()
