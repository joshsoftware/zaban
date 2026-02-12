"""Simple XOR cipher for audio data protection during transmission."""

import base64


def xor_cipher(data: bytes, key: str) -> bytes:
    """
    Apply XOR cipher to bytes with a repeating key.
    
    Args:
        data: Input bytes
        key: Encryption key
        
    Returns:
        XORed bytes
    """
    key_bytes = key.encode()
    key_len = len(key_bytes)
    return bytes(b ^ key_bytes[i % key_len] for i, b in enumerate(data))


def decrypt_audio_base64(encoded_data: str, key: str) -> bytes:
    """
    Decrypt base64 encoded XORed audio.
    
    Args:
        encoded_data: Base64 string of encrypted data
        key: XOR key
        
    Returns:
        Decrypted audio bytes
    """
    encrypted_data = base64.b64decode(encoded_data)
    return xor_cipher(encrypted_data, key)
