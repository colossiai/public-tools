### **<span class="mark">Hashing vs Encryption</span>**

### 

### **Key Differences**

- **Purpose**: Hashing is for integrity, while encryption is for confidentiality.

- **Reversibility**: Hashing is one-way, encryption is two-way.

- **Output Size**: Hashing produces a fixed-size output regardless of input size, while encryption output size depends on the input size.

Both techniques are essential for different aspects of data security. Hashing is used where data integrity and verification are critical, whereas encryption is used where data privacy and confidentiality are paramount.

### **Hashing**

1.  **Purpose**: Hashing is used to verify data integrity. It ensures that the data has not been altered.

2.  **Function**: Hashing converts data of any size into a fixed-size string of characters, which is typically a hash code.

3.  **Output**: The output of a hashing function is called a hash value or hash digest.

4.  **Reversibility**: Hashing is a one-way function, meaning you cannot revert the hash value back to the original data.

5.  **Use Cases**:

    - Storing passwords securely (e.g., in a database).

    - Verifying the integrity of files and data (e.g., checksums).

    - Digital signatures.

6.  **Examples**: MD5, SHA-1, SHA-256.

### **Encryption (NEED to reverse)**

1.  **Purpose**: Encryption is used to protect the confidentiality of data. It ensures that only authorized parties can read the data.

2.  **Function**: Encryption converts plaintext (readable data) into ciphertext (unreadable data) using an encryption algorithm and a key.

3.  **Output**: The output of an encryption process is called ciphertext.

4.  **Reversibility**: Encryption is a two-way function, meaning you can decrypt the ciphertext back to the original plaintext using the correct key.

5.  **Use Cases**:

    - Securing data transmission over the internet (e.g., HTTPS).

    - Protecting sensitive data (e.g., files, emails).

    - Encrypted communications (e.g., messaging apps).

6.  **Examples**: AES, RSA, DES.

**<span class="mark">Signing</span>**

### **Signing (Digital Signatures)**

1.  **Purpose**: Digital signing ensures data authenticity and integrity. It verifies that the data comes from a trusted source and has not been tampered with.

2.  **Function**: Digital signing involves creating a digital signature using a private key. This process includes hashing the data and then encrypting the hash value with the private key.

3.  **Output**: The output is a digital signature, which is a combination of the hash value and the private key encryption.

4.  **Reversibility**: The signature can be verified by anyone with the corresponding public key, which decrypts the signature to retrieve the hash value and compare it to a newly computed hash of the data.

5.  **Use Cases**:

    - Authenticating software and firmware updates.

    - Securing email communications.

    - Verifying digital documents.

6.  **Examples**: RSA, DSA, ECDSA.

### **Key Differences**

- **Purpose**: Hashing is for verifying data integrity, while signing is for verifying data authenticity and integrity.

- **Output**: Hashing produces a hash value, while signing produces a digital signature.

- **Reversibility**: Hashing is one-way, whereas digital signatures involve a reversible process where the signature can be verified with a public key.

- **Security**: Hashing alone does not provide information about the origin of the data, whereas digital signatures provide assurance about the data's origin and integrity.

### **Combined Use**

In many security protocols, hashing and signing are used together. For example, in digital signatures, data is first hashed, and then the hash is signed with a private key. This combination ensures both the integrity and authenticity of the data.

example:

Signing a Document: with PRIVATE key

document = "This is a confidential document."

hash_value = hash_function(document)

digital_signature = encrypt_with_private_key(hash_value, <span class="mark">sender_private_key</span>)

Verifying a Document: ONLY WIth Public Key

received_document = "This is a confidential document."

received_signature = digital_signature

hash_value = hash_function(received_document)

decrypted_hash_value = decrypt_with_public_key(received_signature, <span class="mark">sender_public_key</span>)

if hash_value == decrypted_hash_value:

print("The document is authentic and has not been altered.")

else:

print("The document is not authentic or has been altered.")
