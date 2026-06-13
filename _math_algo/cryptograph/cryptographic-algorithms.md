# Cryptographic Algorithms — Up-to-Date Summary

A practical map of the main families of cryptographic algorithms, what they're used for, and which concrete algorithms to pick today (and which to avoid).

> **As of 2026.** Quantum-resistant standards have landed (NIST FIPS 203/204/205, published Aug 2024) and major TLS / messaging stacks are rolling them out in hybrid mode. Legacy primitives (DES, 3DES, MD5, SHA-1) are formally deprecated and should not appear in new designs.

---

## 1. Overview Table

| # | Family | Purpose | Modern Picks | Avoid / Deprecated |
|---|--------|---------|--------------|--------------------|
| 1 | **Symmetric encryption** | Encrypt/decrypt data fast with one shared key | AES-256-GCM, ChaCha20-Poly1305, AES-256-GCM-SIV | DES, 3DES, RC4, AES-CBC w/o MAC |
| 2 | **Asymmetric encryption** | Encrypt for a specific recipient / wrap a key | RSA-OAEP (≥3072-bit), ECIES (P-256 / X25519) | RSA-PKCS#1 v1.5 encryption, RSA <2048-bit |
| 3 | **Digital signatures** | Prove authenticity + integrity | Ed25519, ECDSA (P-256), RSA-PSS (≥3072-bit), **ML-DSA (Dilithium)**, **SLH-DSA (SPHINCS+)** | DSA, RSA-PKCS#1 v1.5 sign, RSA <2048-bit |
| 4 | **Key agreement / KEM** | Establish a shared secret over an insecure channel | X25519, ECDH (P-256), **ML-KEM (Kyber)**, **X25519+ML-KEM hybrid** | Finite-field DH <2048-bit, static DH without PFS |
| 5 | **Hash functions** | Produce a fixed-size, irreversible fingerprint | SHA-256, SHA-512, SHA-3, BLAKE3 | MD5, SHA-1 |
| 6 | **MAC / AEAD tag** | Integrity + authenticity with a shared key | HMAC-SHA-256, KMAC, Poly1305 (within AEAD) | CBC-MAC on variable-length input, MD5-HMAC |
| 7 | **Password hashing / KDF** | Derive keys / store passwords | Argon2id, scrypt, PBKDF2-SHA-256, HKDF (for key derivation) | Plain SHA-x of password, MD5-crypt |

---

## 2. Symmetric Cryptographic Algorithms

**Use case:** encrypt and decrypt data quickly with the same key for both operations — bulk data, files at rest, links inside a trusted boundary.

| Algorithm | Key Size | Status | Notes |
|-----------|----------|--------|-------|
| **AES-128 / AES-256** | 128 / 256 bits | Recommended | AES-256 chosen when long-term confidentiality matters (some quantum margin via Grover). |
| **ChaCha20-Poly1305** | 256 bits | Recommended | AEAD; faster than AES on platforms without AES-NI (mobile, IoT). |
| **AES-GCM / GCM-SIV** | 128/256 bits | Recommended | AEAD mode; GCM-SIV is nonce-misuse resistant. |
| DES | 56 bits | **Broken** | Brute-forceable. Do not use. |
| 3DES (TDEA) | 112/168 bits | **Deprecated** (NIST disallows after 2023) | Small block size → Sweet32. |
| RC4 | variable | **Broken** | Biased keystream. |

**Common uses:** file/disk encryption, database column encryption, TLS record layer, VPN payloads, message bodies in E2E messaging.

---

## 3. Asymmetric Cryptographic Algorithms

**Use case:** different keys for encrypt vs. decrypt — enables public-key encryption, key wrapping, and signature schemes.

| Algorithm | Typical Size | Status | Notes |
|-----------|--------------|--------|-------|
| **RSA-OAEP** | ≥3072-bit | OK (classical) | Use OAEP padding; PKCS#1 v1.5 encryption is vulnerable to padding-oracle attacks. |
| **ECC (P-256, P-384, X25519/Ed25519)** | 256–384 bits | Recommended | Much smaller keys/signatures than RSA at equivalent classical security. |
| RSA <2048-bit | — | **Deprecated** | Below NIST minimum. |

> **Quantum note:** all of the above are broken by Shor's algorithm on a sufficiently large quantum computer. For long-lived confidentiality (data that must remain secret beyond ~2035), pair classical asymmetric with a post-quantum KEM (see §5).

**Common uses:** TLS handshake (key transport / signatures), code signing, S/MIME, JWT signing.

---

## 4. Digital Signature Algorithms

**Use case:** verify the **authenticity and integrity** of a message, document, binary, or certificate.

| Algorithm | Status | Notes |
|-----------|--------|-------|
| **Ed25519 / Ed448** | Recommended | Deterministic, fast, simple API, no nonce-reuse footgun. Default choice for new systems. |
| **ECDSA (P-256, P-384)** | OK | Widely supported; requires high-quality nonces (RFC 6979 deterministic variant preferred). |
| **RSA-PSS** | OK (≥3072-bit) | Preferred over PKCS#1 v1.5 for signatures. |
| **ML-DSA (Dilithium)** — FIPS 204 | Recommended (PQ) | NIST-standardized lattice signature. Larger keys/signatures (~2–4 KB). |
| **SLH-DSA (SPHINCS+)** — FIPS 205 | Niche (PQ) | Hash-based, conservative; very large signatures (~8–50 KB) but minimal assumptions. |
| DSA (FIPS 186-4) | **Deprecated** | Removed in FIPS 186-5 (2023). |
| RSA-PKCS#1 v1.5 sign | Discouraged | Use only for legacy compatibility. |

**Common uses:** software/firmware signing, TLS certificate signatures, package managers (apt, npm provenance), blockchain transactions, JWTs.

---

## 5. Key-Agreement Algorithms / KEMs

**Use case:** two parties establish a shared secret over an insecure channel without ever transmitting the secret itself.

### Classical
| Algorithm | Status | Notes |
|-----------|--------|-------|
| **X25519 / X448** (ECDH on Curve25519/448) | Recommended | Default in modern TLS 1.3, Signal, WireGuard. |
| **ECDH (P-256, P-384)** | OK | Required by some compliance regimes (FIPS). |
| Finite-field DH (≥2048-bit MODP groups) | Legacy | Larger and slower than ECDH. |
| DH < 2048-bit | **Broken** (Logjam) | — |

### Post-Quantum (NEW)
| Algorithm | Status | Notes |
|-----------|--------|-------|
| **ML-KEM (Kyber)** — FIPS 203 | Recommended (PQ) | NIST-standardized lattice KEM. ML-KEM-768 is the common pick. |
| **X25519 + ML-KEM-768 hybrid** | Recommended (transitional) | Already deployed in Chrome, Cloudflare, AWS KMS, OpenSSH ≥9.9. Defense-in-depth against both classical and "harvest-now, decrypt-later" attacks. |

> **Why a KEM and not "PQ Diffie-Hellman"?** Lattice-based primitives don't naturally form a symmetric group operation, so the PQ replacement for ECDH is a **Key Encapsulation Mechanism**: one party generates a ciphertext + shared secret using the other's public key. Operationally it slots into the same place in a protocol.

**Common uses:** TLS 1.3 handshake, SSH, Signal/Noise protocols, IPsec/IKEv2.

---

## 6. One-Way Hash Functions

**Use case:** produce a fixed-size, deterministic, irreversible fingerprint of arbitrary input — for integrity checks, content addressing, and as a building block inside other primitives.

| Algorithm | Output Size | Status | Notes |
|-----------|-------------|--------|-------|
| **SHA-256 / SHA-512** | 256 / 512 bits | Recommended | SHA-2 family; ubiquitous, FIPS-approved. |
| **SHA-3 (Keccak)** | 224–512 bits | Recommended | Different construction (sponge) than SHA-2 — useful diversification. |
| **BLAKE3** | variable | Recommended | Fastest mainstream hash; parallelizable. |
| SHA-1 | 160 bits | **Broken** (SHAttered, 2017) | Collision attacks practical. |
| MD5 | 128 bits | **Broken** | Collisions trivial; do not use for any security purpose. |

> **Never use a plain hash to store passwords.** Hashes are designed to be fast; password storage requires intentionally slow / memory-hard schemes (see §8).

**Common uses:** file integrity (checksums, content-addressed storage like Git/IPFS), digital signature input, HMAC base, commitment schemes, proof-of-work.

---

## 7. Message Authentication Codes (MAC)

**Use case:** ensure both **integrity and authenticity** of a message using a shared secret key.

| Algorithm | Status | Notes |
|-----------|--------|-------|
| **HMAC-SHA-256 / HMAC-SHA-512** | Recommended | Classical, well-analyzed, FIPS-approved. |
| **KMAC** (SHA-3 based) | Recommended | Native MAC built on Keccak. |
| **Poly1305** | Recommended *within AEAD* | Used inside ChaCha20-Poly1305 / AES-GCM; do not use stand-alone with key reuse. |
| CBC-MAC on variable-length input | Avoid | Vulnerable unless length-prefixed (CMAC fixes this). |

> **Prefer AEAD (e.g. AES-GCM, ChaCha20-Poly1305) over Encrypt-then-MAC composition** in new designs — the AEAD construction handles both confidentiality and integrity in one verified construction.

**Common uses:** API request signing (AWS SigV4, webhooks), session token integrity, cookie signing, TLS record MAC (in non-AEAD ciphersuites).

---

## 8. Password Hashing & Key Derivation

Not in the original table, but essential — and the area where people most commonly misuse the primitives above.

| Algorithm | Use | Notes |
|-----------|-----|-------|
| **Argon2id** | Password storage | OWASP/IETF current recommendation. Memory-hard, side-channel resistant. |
| **scrypt** | Password storage | Memory-hard; older but solid. |
| **PBKDF2-SHA-256** | Password storage (compliance) | Allowed by FIPS; prefer ≥600,000 iterations (OWASP 2023+). |
| **HKDF** | Deriving keys *from already-strong secrets* | Don't use for passwords — it's fast on purpose. |
| Plain SHA-256(password) | — | **Never**. |

---

## 9. Quick Decision Guide

- **Encrypting a file or message body?** → ChaCha20-Poly1305 or AES-256-GCM (AEAD).
- **Two services need a shared secret?** → X25519 (today) or X25519+ML-KEM-768 hybrid (for long-lived secrecy).
- **Signing a release artifact, JWT, or transaction?** → Ed25519; add ML-DSA in parallel if PQ matters.
- **Checking a file hasn't changed?** → SHA-256 or BLAKE3.
- **Storing user passwords?** → Argon2id.
- **Signing an API request with a shared secret?** → HMAC-SHA-256.
- **Encrypting data that must stay secret past 2035?** → Use a PQ hybrid for key establishment **now** (harvest-now-decrypt-later threat).

---

## 10. Post-Quantum Migration Status (2026 snapshot)

| Layer | PQ Status |
|-------|-----------|
| TLS 1.3 (browsers, CDNs) | Hybrid `X25519MLKEM768` widely enabled (Chrome, Firefox, Cloudflare, AWS). |
| SSH | OpenSSH ≥9.9 defaults to hybrid `mlkem768x25519-sha256`. |
| VPNs (WireGuard / IPsec) | Hybrid drafts in progress; some commercial deployments shipping. |
| Code signing | Industry moving toward dual signatures (classical + ML-DSA / SLH-DSA). |
| Long-lived data at rest | Re-wrap data keys under PQ-protected KEKs; rotate as standards mature. |

The general migration pattern is **hybrid first** (classical ⊕ PQ in parallel), then pure PQ once confidence in implementations grows.

---

## References

- NIST FIPS 197 — AES
- NIST FIPS 180-4 / 202 — SHA-2 / SHA-3
- NIST FIPS 186-5 — Digital Signature Standard (ECDSA, EdDSA, RSA)
- NIST FIPS 203 — ML-KEM (Module-Lattice KEM, formerly Kyber)
- NIST FIPS 204 — ML-DSA (Module-Lattice DSA, formerly Dilithium)
- NIST FIPS 205 — SLH-DSA (Stateless Hash-Based DSA, formerly SPHINCS+)
- NIST SP 800-131A — Transitioning the Use of Cryptographic Algorithms and Key Lengths
- RFC 7748 — X25519/X448
- RFC 8032 — Ed25519/Ed448
- RFC 9106 — Argon2
- OWASP Password Storage Cheat Sheet
