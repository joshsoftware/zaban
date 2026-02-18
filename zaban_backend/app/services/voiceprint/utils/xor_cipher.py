"""
XOR Cipher Utility

Purpose:
- Lightweight transport-level obfuscation for audio bytes
- NOT cryptographic security
- Reversible using the same key

IMPORTANT:
- This should only be used at API boundaries
- Never store encrypted audio
- Never pass encrypted bytes to ML models
"""

from typing import Union


class XORCipher:
    """
    Stateless XOR cipher for bytes-level encryption/decryption.
    """

    def __init__(self, key: Union[str, bytes]):
        if not key:
            raise ValueError("XOR key must not be empty")

        if isinstance(key, str):
            key = key.encode("utf-8")

        self._key = key
        self._key_len = len(key)

    def apply(self, data: bytes) -> bytes:
        """
        Apply XOR cipher to input bytes.

        The same method is used for encryption and decryption.

        Args:
            data: raw bytes (encrypted or plain)

        Returns:
            XOR-processed bytes
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("XORCipher expects bytes-like input")

        result = bytearray(len(data))

        for i, byte in enumerate(data):
            key_byte = self._key[i % self._key_len]
            result[i] = byte ^ key_byte

        return bytes(result)


def decrypt_audio_bytes(encrypted_bytes: bytes, key: str) -> bytes:
    """
    Decrypt XOR-encrypted audio bytes at API boundary.
    
    Args:
        encrypted_bytes: The encrypted audio bytes from frontend
        key: The XOR key (should match frontend key)
        
    Returns:
        Decrypted audio bytes
    """
    cipher = XORCipher(key)
    return cipher.apply(encrypted_bytes)
