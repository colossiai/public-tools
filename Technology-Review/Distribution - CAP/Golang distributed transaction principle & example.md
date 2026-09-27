# golang distributed transaction principle and example

### Distributed Transactions in Go (Golang) - Principle and Example

#### **Overview of Distributed Transactions**

A **distributed transaction** involves multiple services or databases, where each participant must complete its part of the transaction to ensure global consistency. Distributed transactions are necessary in systems like microservices architecture, where data is often distributed across multiple services. The two primary protocols for distributed transactions are:

1.  **Two-Phase Commit (2PC)**: This protocol ensures all participants either commit or rollback changes.

2.  **SAGA pattern**: A long-running transaction where each step has a compensating action in case of failure.

#### **Two-Phase Commit (2PC)**

- **Phase 1 (Prepare)**: The coordinator asks each participant if they can commit. Each participant performs local checks and votes to either commit or abort.

- **Phase 2 (Commit/Abort)**: If all participants vote to commit, the coordinator sends a commit request. Otherwise, it sends an abort request.

##### Key Characteristics:

- Strict consistency, but it can lead to blocking if a participant crashes.

- Complex to implement in highly available and distributed systems.

#### **SAGA Pattern**

- SAGA breaks a distributed transaction into smaller, local transactions across services.

- If any transaction fails, a set of compensating transactions are invoked to undo previous actions.

**SAGA stands for Simple Aggregated Gateway Application**. In the context of distributed systems, however, it doesn't represent an acronym but is rather a design pattern used to manage long-running transactions across multiple services.

In a SAGA, a series of distributed transactions are executed in a sequence, where each step is a local transaction in a different service. If any of the steps fail, compensating transactions (undo operations) are executed to roll back the previous successful steps, ensuring eventual consistency.

##### Key Characteristics:

- More flexible than 2PC.

- No locking required.

- Can handle long-running processes.

### **Example: Implementing SAGA Pattern in Golang**

Let's create a simple example using the **SAGA** pattern, where we simulate a booking system with services for booking a flight, hotel, and car.

#### **Basic Structure**

We'll use HTTP services to represent microservices and a coordinator to manage the saga flow.

package main

import (

"fmt"

"log"

"net/http"

)

// Service response structure

type ServiceResponse struct {

Success bool

}

// Simulate the booking process for flight, hotel, and car

func bookFlight(w http.ResponseWriter, r \*http.Request) {

fmt.Fprintf(w, "Flight booked successfully")

}

func cancelFlight(w http.ResponseWriter, r \*http.Request) {

fmt.Fprintf(w, "Flight booking canceled")

}

func bookHotel(w http.ResponseWriter, r \*http.Request) {

fmt.Fprintf(w, "Hotel booked successfully")

}

func cancelHotel(w http.ResponseWriter, r \*http.Request) {

fmt.Fprintf(w, "Hotel booking canceled")

}

func bookCar(w http.ResponseWriter, r \*http.Request) {

fmt.Fprintf(w, "Car booked successfully")

}

func cancelCar(w http.ResponseWriter, r \*http.Request) {

fmt.Fprintf(w, "Car booking canceled")

}

func main() {

http.HandleFunc("/book/flight", bookFlight)

http.HandleFunc("/cancel/flight", cancelFlight)

http.HandleFunc("/book/hotel", bookHotel)

http.HandleFunc("/cancel/hotel", cancelHotel)

http.HandleFunc("/book/car", bookCar)

http.HandleFunc("/cancel/car", cancelCar)

fmt.Println("Booking service is running on port 8080")

log.Fatal(http.ListenAndServe(":8080", nil))

}

#### **Coordinator (Orchestrator)**

The coordinator manages the flow of the SAGA, ensuring that if any step fails, it rolls back the previous steps.

package main

import (

"fmt"

"net/http"

"log"

)

// A simple helper function to handle requests

func sendRequest(url string) bool {

resp, err := http.Get(url)

if err != nil \|\| resp.StatusCode != http.StatusOK {

return false

}

return true

}

func bookSaga() {

// Step 1: Book flight

flightSuccess := sendRequest("http://localhost:8080/book/flight")

if !flightSuccess {

fmt.Println("Failed to book flight")

return

}

fmt.Println("Flight booked")

// Step 2: Book hotel

hotelSuccess := sendRequest("http://localhost:8080/book/hotel")

if !hotelSuccess {

fmt.Println("Failed to book hotel. Rolling back flight booking...")

sendRequest("http://localhost:8080/cancel/flight")

return

}

fmt.Println("Hotel booked")

// Step 3: Book car

carSuccess := sendRequest("http://localhost:8080/book/car")

if !carSuccess {

fmt.Println("Failed to book car. Rolling back flight and hotel bookings...")

sendRequest("http://localhost:8080/cancel/flight")

sendRequest("http://localhost:8080/cancel/hotel")

return

}

fmt.Println("Car booked successfully, transaction complete!")

}

func main() {

fmt.Println("Starting SAGA orchestrator...")

// Start the SAGA process

bookSaga()

}

#### **How the Example Works:**

1.  The orchestrator starts by attempting to book a flight.

2.  If successful, it proceeds to book a hotel. If the hotel booking fails, it cancels the flight.

3.  If both the flight and hotel bookings are successful, it proceeds to book a car.

4.  If the car booking fails, it rolls back the flight and hotel bookings.

5.  If all services are successfully booked, the transaction is considered complete.

### **Handling Failures**

In a real-world scenario, each service should provide proper error handling, retries, and compensation actions (e.g., refund or rollback).

### **Key Considerations:**

- **Compensation Logic**: Each service should define a compensating action to undo the previous successful actions in case of failure.

- **Distributed Logging**: Proper logging of each step is crucial to monitor the SAGA's progress and detect failures.

- **Idempotency**: All services should be idempotent, meaning repeating the same request should not have adverse side effects.

### **Conclusion**

Distributed transactions in Go can be efficiently handled using patterns like SAGA to achieve a balance between consistency and availability. While this example demonstrates a basic implementation, production systems often incorporate additional complexities such as message queues, retries, and error handling to ensure robustness in distributed environments.
