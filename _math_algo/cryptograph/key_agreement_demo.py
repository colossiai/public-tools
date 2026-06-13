# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "cryptography>=43",
#   "kyber-py>=1.0",
# ]
# ///
"""
Key-Agreement Algorithms — runnable demo.

Covers the four practical paths from §5 of cryptographic-algorithms.md:

  1. X25519                 — modern classical ECDH (TLS 1.3 / WireGuard / Signal default)
  2. ECDH on P-256          — NIST-curve ECDH (FIPS-required environments)
  3. ML-KEM-768 (Kyber)     — NIST FIPS 203 post-quantum KEM
  4. X25519 + ML-KEM-768    — hybrid: defense-in-depth against "harvest-now, decrypt-later"

Run with uv (handles deps automatically):

    uv run key_agreement_demo.py
"""

from __future__ import annotations

import os
import secrets

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, x25519
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from kyber_py.ml_kem import ML_KEM_768


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hkdf_sha256(shared_secret: bytes, info: bytes, length: int = 32) -> bytes:
    """Derive a uniform symmetric key from a raw DH/KEM secret. Never use
    the raw shared secret as an AEAD key directly."""
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
    ).derive(shared_secret)


def short(b: bytes, n: int = 8) -> str:
    return b[:n].hex() + f"...({len(b)} B)"


def banner(title: str) -> None:
    print(f"\n{'=' * 72}\n  {title}\n{'=' * 72}")


# ---------------------------------------------------------------------------
# 1. X25519 — ECDH on Curve25519
# ---------------------------------------------------------------------------

def demo_x25519() -> None:
    banner("1. X25519 (Curve25519 ECDH) — classical, modern default")

    # Each side generates an ephemeral keypair.
    alice_sk = x25519.X25519PrivateKey.generate()
    bob_sk = x25519.X25519PrivateKey.generate()

    alice_pk = alice_sk.public_key()
    bob_pk = bob_sk.public_key()

    # Wire format = raw 32-byte public key (RFC 7748).
    alice_pk_bytes = alice_pk.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    bob_pk_bytes = bob_pk.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    print(f"  Alice pub : {short(alice_pk_bytes)}")
    print(f"  Bob   pub : {short(bob_pk_bytes)}")

    # Each side computes the same shared secret from their own SK + peer's PK.
    alice_shared = alice_sk.exchange(bob_pk)
    bob_shared = bob_sk.exchange(alice_pk)

    assert alice_shared == bob_shared, "ECDH disagreement!"
    print(f"  Raw secret: {short(alice_shared)}")

    key = hkdf_sha256(alice_shared, info=b"demo-x25519-aead")
    print(f"  AEAD key  : {short(key)}  (HKDF-SHA256)")


# ---------------------------------------------------------------------------
# 2. ECDH on NIST P-256
# ---------------------------------------------------------------------------

def demo_ecdh_p256() -> None:
    banner("2. ECDH on P-256 — required by FIPS / compliance regimes")

    alice_sk = ec.generate_private_key(ec.SECP256R1())
    bob_sk = ec.generate_private_key(ec.SECP256R1())

    alice_shared = alice_sk.exchange(ec.ECDH(), bob_sk.public_key())
    bob_shared = bob_sk.exchange(ec.ECDH(), alice_sk.public_key())

    assert alice_shared == bob_shared
    print(f"  Raw secret: {short(alice_shared)}")
    print(f"  AEAD key  : {short(hkdf_sha256(alice_shared, b'demo-p256-aead'))}")


# ---------------------------------------------------------------------------
# 3. ML-KEM-768 — NIST FIPS 203 post-quantum KEM
# ---------------------------------------------------------------------------

def demo_ml_kem_768() -> None:
    banner("3. ML-KEM-768 (Kyber) — NIST FIPS 203, post-quantum")
    print("  Note: KEM != DH. Roles are asymmetric:")
    print("    - Receiver publishes a public key.")
    print("    - Sender 'encapsulates' a fresh secret against it,")
    print("      producing (ciphertext, shared_secret).")
    print("    - Receiver 'decapsulates' the ciphertext to recover the same secret.\n")

    # Bob = receiver. Publishes ek (encapsulation key, ~1184 B for ML-KEM-768).
    bob_ek, bob_dk = ML_KEM_768.keygen()
    print(f"  Bob pub key (ek)  : {short(bytes(bob_ek))}")

    # Alice = sender. Encapsulates → gets (ciphertext, shared_secret).
    alice_secret, ciphertext = ML_KEM_768.encaps(bob_ek)
    print(f"  Ciphertext        : {short(bytes(ciphertext))}")
    print(f"  Alice's secret    : {short(bytes(alice_secret))}")

    # Bob decapsulates the ciphertext to recover the same secret.
    bob_secret = ML_KEM_768.decaps(bob_dk, ciphertext)
    print(f"  Bob's   secret    : {short(bytes(bob_secret))}")

    assert alice_secret == bob_secret, "ML-KEM disagreement!"
    key = hkdf_sha256(bytes(alice_secret), info=b"demo-mlkem768-aead")
    print(f"  AEAD key          : {short(key)}  (HKDF-SHA256)")


# ---------------------------------------------------------------------------
# 4. Hybrid X25519 + ML-KEM-768
#    Wire format and KDF mirror the IETF draft used by TLS 1.3 / SSH today.
# ---------------------------------------------------------------------------

def demo_hybrid() -> None:
    banner("4. X25519 + ML-KEM-768 hybrid — what TLS 1.3 / OpenSSH ship today")
    print("  Combine two independent shared secrets so the session is safe")
    print("  if EITHER primitive holds. Catches both classical breaks AND")
    print("  the 'record-now, decrypt-after-quantum-computer' threat.\n")

    # --- X25519 leg ---
    a_x_sk = x25519.X25519PrivateKey.generate()
    b_x_sk = x25519.X25519PrivateKey.generate()
    ss_x25519 = a_x_sk.exchange(b_x_sk.public_key())
    assert ss_x25519 == b_x_sk.exchange(a_x_sk.public_key())

    # --- ML-KEM-768 leg ---
    bob_ek, bob_dk = ML_KEM_768.keygen()
    ss_kem_alice, kem_ct = ML_KEM_768.encaps(bob_ek)
    ss_kem_bob = ML_KEM_768.decaps(bob_dk, kem_ct)
    assert ss_kem_alice == ss_kem_bob

    # Combine: concat then KDF. Order matters and must be agreed by the protocol.
    combined = ss_x25519 + bytes(ss_kem_alice)
    session_key = hkdf_sha256(combined, info=b"tls13-hybrid-x25519-mlkem768")

    print(f"  X25519     secret : {short(ss_x25519)}")
    print(f"  ML-KEM-768 secret : {short(bytes(ss_kem_alice))}")
    print(f"  Combined input    : {short(combined)}")
    print(f"  Session key       : {short(session_key)}  (HKDF-SHA256)")

    # Show it actually works: encrypt a message with the derived key.
    aead = ChaCha20Poly1305(session_key)
    nonce = secrets.token_bytes(12)
    plaintext = b"hello from the post-quantum side"
    ciphertext = aead.encrypt(nonce, plaintext, associated_data=b"demo-aad")
    recovered = aead.decrypt(nonce, ciphertext, associated_data=b"demo-aad")
    assert recovered == plaintext
    print(f"  AEAD round-trip OK: {recovered!r}")


# ---------------------------------------------------------------------------
# Sanity / negative test: tampered ML-KEM ciphertext still produces a key on
# the receiver side (implicit rejection), but it WILL NOT MATCH the sender's
# key — so the AEAD will fail to authenticate. This is the protocol-level
# detection mechanism; KEMs are IND-CCA2, not "decap fails loudly".
# ---------------------------------------------------------------------------

def demo_tamper_detection() -> None:
    banner("5. Tamper check — ML-KEM uses implicit rejection")

    ek, dk = ML_KEM_768.keygen()
    ss_sender, ct = ML_KEM_768.encaps(ek)

    # Flip one byte in the ciphertext.
    ct_bytes = bytearray(bytes(ct))
    ct_bytes[0] ^= 0x01
    ss_recv = ML_KEM_768.decaps(dk, bytes(ct_bytes))

    print(f"  Sender   secret  : {short(bytes(ss_sender))}")
    print(f"  Receiver secret  : {short(bytes(ss_recv))}  (after 1-bit flip)")
    print(f"  Match?           : {bytes(ss_sender) == bytes(ss_recv)}")
    print("  → Receiver returns *some* secret (no oracle leak),")
    print("    but the AEAD tag check downstream will fail. Protocol-level catch.")


# ---------------------------------------------------------------------------

def main() -> None:
    print("Key-Agreement Algorithms Demo")
    print(f"OS random source: {os.urandom(8).hex()} (sanity check)")

    demo_x25519()
    demo_ecdh_p256()
    demo_ml_kem_768()
    demo_hybrid()
    demo_tamper_detection()

    print("\nAll demos completed.\n")


if __name__ == "__main__":
    main()
