# **Give a concrete HSM MPC signing example.**

Sure! Here's a **concrete example** of how **HSM + MPC signing** might work in practice using **threshold ECDSA signing** across multiple HSMs.

## **🔐 Example: Threshold ECDSA Signing with 2-out-of-3 HSM MPC**

### **🧩 Scenario**

You want to sign a transaction using a private key managed in a **2-of-3 threshold MPC setup** using HSMs. The full private key is **never constructed**. Instead, it's split across three HSMs (HSM-A, HSM-B, HSM-C). Any two can jointly sign.

## **📦 Step-by-Step: Signing a Message**

Let’s say we want to sign the message m = "Send 1 BTC to Alice".

### **1. Key Generation (1-time setup)**

- A distributed key generation (DKG) protocol is run across HSM-A, HSM-B, and HSM-C.

- Each HSM ends up with a **share** of the private key: sk_A, sk_B, and sk_C.

- The corresponding public key pk is derived jointly and shared externally.

> 🔐 No single HSM ever sees or reconstructs the full sk.

### **2. Signing Request Initiated**

- A client or application sends a request to sign the message m using pk.

### **3. Partial Signatures Generated**

Let’s say HSM-A and HSM-B are chosen to sign.

- HSM-A computes a partial signature σ_A using sk_A and ephemeral values (e.g., k_A) as per the threshold ECDSA protocol.

- HSM-B computes another partial signature σ_B using its own share sk_B and k_B.

Both use a consistent nonce k (but split into shares as well), which is critical for ECDSA security.

### **4. Combining Partial Signatures**

A trusted signer coordinator (or another MPC node) gathers σ_A and σ_B, and **combines** them to produce the final signature σ:

σ = Combine(σ_A, σ_B)

This final signature is a valid ECDSA signature under the public key pk.

### **5. Verification**

Anyone can verify σ against the public key pk and message m:

ECDSA_Verify(pk, m, σ) → ✅ valid

## **🧠 Behind the Scenes**

- This uses **threshold cryptography** protocols, like:

  - **GG18 / GG20**: Secure threshold ECDSA (e.g., from Gennaro and Goldfeder)

  - Based on **zero-knowledge proofs**, **commitments**, and **homomorphic operations  **

- HSMs implement MPC operations using secure APIs or inside confidential enclaves (e.g., via secure multi-party libraries like MP-SPDZ, or proprietary vendor SDKs).

## **🛡️ Security Benefits**

- **Key never reconstructed** – no single point of compromise

- **Redundancy** – any 2 of 3 HSMs can operate, enabling high availability

- **Tamper resistance** – HSM ensures each key share is securely stored and used

Would you like to see pseudocode or a diagram of this process?

# Implementation details

Here’s a simplified yet **concrete implementation breakdown** of **threshold ECDSA signing using MPC between two HSMs**, using ideas from the **GG20 protocol** (widely used in MPC ECDSA). Note that real implementations are much more complex and involve ZK proofs, verifiable secret sharing, and careful nonce handling — but this will give you a solid understanding.

## **⚙️ Assumptions**

- ECDSA over secp256k1.

- 2-of-3 threshold setup (sk = sk_A + sk_B mod n)

- Shared nonce: k = k_A + k_B mod n

- Each HSM has:

  - Key share sk_i

  - Nonce share k_i (ephemeral, regenerated per signature)

## **🧠 High-Level Formula (ECDSA)**

ECDSA signature:

r = (k \* G).x

s = k⁻¹ (H(m) + r \* sk) mod n

We compute this in a **distributed way**.

## **🔧 Step-by-Step: MPC Threshold Signing**

### **1. Distributed Key Generation (once)**

Each HSM participates in a **DKG** protocol to:

- Generate a shared private key sk, split as sk_A + sk_B + sk_C = sk mod n

- Derive the public key: pk = sk \* G

### **2. Nonce Generation (per signature)**

Each signer HSM (e.g. A and B) locally generates a **random nonce share**:

k_A ∈R ℤ_n

k_B ∈R ℤ_n

Then compute:

R_A = k_A \* G

R_B = k_B \* G

They exchange R_A and R_B, and compute:

R = R_A + R_B \# point addition

r = R.x mod n \# x-coordinate becomes r

### **3. Compute Partial s Terms**

Each signer computes its partial s_i:

z = H(m)

s_A = k_A⁻¹ \* (z + r \* sk_A) mod n

s_B = k_B⁻¹ \* (z + r \* sk_B) mod n

(Note: For GG20, these operations are done using homomorphic operations and ZK proofs to keep sk_i and k_i secret.)

### **4. Combine Partial Signatures**

A coordinator or one HSM combines the partial s_i values:

s = s_A + s_B mod n

The final signature is:

σ = (r, s)

## **🧪 Verification**

Anyone can verify:

ecdsa_verify(pk, m, σ) == True

## **🧱 Pseudocode Summary (Python-like)**

def threshold_sign(HSM_A, HSM_B, message):

z = hash_to_int(message)

\# Step 1: Nonce generation

kA, RA = HSM_A.generate_nonce()

kB, RB = HSM_B.generate_nonce()

R = point_add(RA, RB)

r = R.x % n

\# Step 2: Partial signature

sA = HSM_A.compute_partial_s(z, r, kA)

sB = HSM_B.compute_partial_s(z, r, kB)

\# Step 3: Combine

s = (sA + sB) % n

return (r, s)

Each HSM.compute_partial_s(z, r, k_i) internally does:

def compute_partial_s(z, r, k_i, sk_i):

return inverse(k_i) \* (z + r \* sk_i) % n

(In a real protocol, this must be done with zero-knowledge range proofs and masked multiplication to ensure security.)

## **🛡️ Real-World Enhancements**

In real-world systems (like Fireblocks, Zengo, or Gnosis Safe MPC):

- The above math is done inside secure HSMs or TEEs

- Nonce reuse is prevented using FROST, GG20, or Lindell’21

- All operations are **verifiable**, using ZK proofs

- Communication is authenticated and encrypted between HSMs

Would you like:

- A real code sample using an open-source library (like [<u>ZenGo’s</u> <u>multi-party-ecdsa</u>](https://github.com/ZenGo-X/multi-party-ecdsa))?

- A diagram showing key flows (for integration with your backend)?

- Implementation in Rust or Go?

Let me know how deep you'd like to go.
