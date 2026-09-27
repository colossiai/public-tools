# Cryptographic algorithm table

## Sheet1

| Technique | Use Case | Examples | Common Use Cases |
|---|---|---|---|
| Symmetric Cryptographic Algorithms | Encrypt and decrypt data quickly with the same key for both operations. | AES, DES, 3DES | Encrypting files, data at rest, or communication within a trusted network. |
| Asymmetric Cryptographic Algorithms | Secure key exchange, digital signatures, or encryption/decryption with different keys. | RSA, ECC | Secure key exchange (e.g., SSL/TLS), digital signatures, encrypting data for a specific recipient. |
| Digital Signature | Verify the authenticity and integrity of a message or document. | RSA, DSA, ECC | Signing software, contracts, or documents to ensure authenticity and integrity. |
| Key-Agreement Algorithms | Securely establish a shared secret between parties over an insecure channel. | Diffie-Hellman, ECDH | Establishing a shared key in secure communication protocols like TLS. |
| One-Way Hash Functions | Ensure data integrity by generating a unique, irreversible hash value. | SHA-256, MD5 | Verifying file integrity, password storage (with salting), digital forensics. |
| Message Authentication Code (MAC) | Ensure both integrity and authenticity of a message using a secret key. | HMAC | Secure communication where message integrity and sender authenticity are crucial. |
| NEW |  |  |  |
| Key-Agreement Algorithms<br>(Key exchange Algos) |  | ML-KEM<br>( post-quantum algorithm) |  |
