# **I start a httpserver on port 9123, I want to capture the request send to the port**

To capture HTTP requests sent to your server running on **port 9123**, use tcpdump as follows:

### **1. Basic Capture on Port 9123**

sudo tcpdump -i any port 9123 -nn

- -i any → Captures on all interfaces (use -i eth0 if needed).

- port 9123 → Filters traffic only for this port.

- -nn → Disables hostname and service name resolution (shows raw IPs and ports).

### **2. Capture HTTP Request Details**

If you want to see raw HTTP request content:

sudo tcpdump -i any port 9123 -A

- -A → Prints ASCII output, making HTTP request headers readable.

Example Output:

GET /index.html HTTP/1.1

Host: 192.168.1.100:9123

User-Agent: curl/7.68.0

Accept: \*/\*

### **3. Save Requests to a File for Later Analysis**

sudo tcpdump -i any port 9123 -w capture.pcap

You can later analyze the file using Wireshark:  
  
wireshark capture.pcap

- 

### **4. Capture Only Incoming HTTP Requests**

To filter only **incoming** traffic to your server:

sudo tcpdump -i any dst port 9123

- Captures packets with destination **port 9123** (incoming requests).

### **5. Capture Only GET or POST Requests**

Since tcpdump doesn’t have built-in HTTP filtering, you can use grep to filter requests:

sudo tcpdump -i any port 9123 -A \| grep "GET\\POST"

- This filters only HTTP GET and POST requests.

Would you like help analyzing captured packets? 🚀

# **Analyze the captured packets.**

Great! Let's analyze the captured HTTP requests. Here’s a step-by-step breakdown:

## **1. Capture HTTP Requests to Port 9123**

If you haven't already captured traffic, run:

sudo tcpdump -i any port 9123 -w http_capture.pcap

Then, make an HTTP request to your server:

curl http://localhost:9123/

After a few requests, stop capturing with Ctrl + C.

## **2. Read Captured Packets in Human-Readable Format**

Once you've captured traffic, analyze it:

sudo tcpdump -r http_capture.pcap -A

This prints packet data in ASCII, making HTTP headers visible.

Example output:

GET /index.html HTTP/1.1

Host: localhost:9123

User-Agent: curl/7.68.0

Accept: \*/\*

This shows:

- **GET /index.html** → The requested resource.

- **Host: localhost:9123** → The destination server.

- **User-Agent: curl/7.68.0** → The client making the request.

## **3. Extract Only HTTP Requests**

Filter for only GET or POST requests:

sudo tcpdump -r http_capture.pcap -A \| grep "GET\\POST"

## **4. Analyze with Wireshark**

For deeper inspection, open the capture file in **Wireshark**:

wireshark http_capture.pcap

In Wireshark:

Apply a **filter**:  
  
tcp.port == 9123

1.  

2.  Click on a packet to inspect:

    - **Request method (GET, POST, etc.)  **

    - **Headers (Host, User-Agent, Cookies, etc.)  **

    - **Request payload (if any, like JSON in POST requests)  **

### **5. Check for Errors or Suspicious Activity**

- Look for **400, 403, 404, 500 errors** in response headers.

- If you see repeated requests from the same IP, it could be a scanner or an attack attempt.

Would you like help interpreting specific logs? 🚀
