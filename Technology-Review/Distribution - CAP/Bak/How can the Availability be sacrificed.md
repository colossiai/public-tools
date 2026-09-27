In the context of the CAP theorem, when we say that availability is sacrificed, <span class="mark">it doesn't mean that the system becomes completely unavailable or that users cannot use it at all. Instead, it means that during a network partition, the system may not be able to guarantee that every request receives a response.</span>

Let's refine Case 1 to better illustrate how availability can be sacrificed for consistency and partition tolerance:

### **Case 1: Consistency and Partition Tolerance (CP)**

- **Consistency**:

  - The system ensures that all nodes see the same data at the same time. This means that if a write is acknowledged, any subsequent reads will reflect that write, even if it requires waiting for communication between nodes.

- **Partition Tolerance**:

  - The system continues to operate despite the network partition. It can handle a situation where the network is unreliable, and some nodes cannot communicate with each other.

#### **Example:**

1.  **Network Partition**:

    - The data center in Tokyo becomes isolated and cannot communicate with the data centers in New York and London.

2.  **Sacrificing Availability for Consistency**:

    - In order to ensure consistency, the system might deny requests that cannot be reliably processed. For example:

      - **Writes**: If a user in Tokyo tries to write data (e.g., update a product price), <span class="mark">the system might reject this write because it cannot ensure that the write will be propagated to New York and London immediately.</span>

      - **Reads**: If a user in Tokyo tries to read data, the system might either provide an error or a stale version of the data, indicating that it cannot confirm the latest state due to the partition.

3.  **Result**:

    - Users in Tokyo may experience errors or delays when trying to perform write operations or read the most up-to-date data. The system sacrifices availability by potentially denying some requests to maintain consistency across all data centers.

In practical terms, this means that during a network partition, the system prioritizes ensuring that any read or write operation is consistent across the entire system, even if it means that some operations may fail or be delayed. This can lead to a reduced level of availability, where the system might not be able to respond to every request successfully, but it avoids inconsistencies.

### **Summary**

In a CP system (Consistency and Partition Tolerance):

- The system will ensure that data is consistent across all nodes, even during network partitions.

- To achieve this, it may need to deny some operations, leading to temporary unavailability for certain types of requests.

- This approach ensures that the system does not provide outdated or conflicting data, maintaining overall consistency.
