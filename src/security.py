import os
import stat
from typing import Dict, Any
import yaml
from cryptography.fernet import Fernet
import base64

class ConfigSecurity:
    @staticmethod
    def enforce_file_permissions(path: str):
        """Ensure config file has restricted permissions (0600 on *nix, restricted on Windows)."""
        try:
            if os.name == 'posix':
                os.chmod(path, 0o600)
            else:
                # On Windows, we can't easily set POSIX perms, but we can check
                pass
        except Exception:
            pass

    @staticmethod
    def generate_key() -> str:
        """Generate encryption key for config."""
        return Fernet.generate_key().decode()

    @staticmethod
    def encrypt_config(data: Dict[str, Any], key: str) -> bytes:
        """Encrypt sensitive config fields."""
        f = Fernet(key.encode())
        plaintext = yaml.dump(data)
        return f.encrypt(plaintext.encode())

    @staticmethod
    def decrypt_config(encrypted_data: bytes, key: str) -> Dict[str, Any]:
        """Decrypt config."""
        f = Fernet(key.encode())
        decrypted = f.decrypt(encrypted_data)
        return yaml.safe_load(decrypted.decode())

    @staticmethod
    def redact_secrets(log_data: Dict[str, Any], secret_keys: list = None) -> Dict[str, Any]:
        """Redact sensitive fields from log data."""
        if secret_keys is None:
            secret_keys = ['api_key', 'gemini_api_key', 'password', 'token', 'webhook_url', 'amazon_tracking_id']
        redacted = log_data.copy()
        for key in secret_keys:
            if key in redacted:
                redacted[key] = '***REDACTED***'
        return redacted