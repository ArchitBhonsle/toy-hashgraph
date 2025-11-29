"""Key generation and management utilities."""

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

def generate():
    """
    Generate Ed25519 key pair.

    Returns:
        tuple: (private_key, public_key)
    """
    key = ed25519.Ed25519PrivateKey.generate()

    private_key = key.private_bytes(
      encoding=serialization.Encoding.Raw,
      format=serialization.PrivateFormat.Raw,
      encryption_algorithm=serialization.NoEncryption()
    )

    public_key = key.public_key().public_bytes(
      encoding=serialization.Encoding.Raw,
      format=serialization.PublicFormat.Raw
    )

    # Validate key sizes
    assert len(private_key) == 32
    assert len(public_key) == 32

    return private_key, public_key
