# Real example of CSRF

A real-world example of a **Cross-Site Request Forgery (CSRF)** attack happened to **Netflix** in 2006. Here's how it worked:

### **Netflix CSRF Attack (2006)**

#### **What Happened?**

A security researcher discovered that Netflix's website was vulnerable to CSRF. The attack could change the victim's account details without their consent.

#### **How Did It Work?**

1.  **User Logged into Netflix**:  
    The victim logs into their Netflix account, and the browser stores an **authentication cookie**.

2.  **Attacker Sends a Malicious Link**:  
    The attacker tricks the victim into clicking a malicious link (e.g., via email or a malicious website).

3.  **The Malicious Request is Sent**:

    - The attacker's link contains a request to change the victim’s Netflix plan.

    - Since the victim is already logged in, the browser automatically sends the Netflix authentication cookie along with the request.

4.  **Netflix Processes the Request**:

    - Netflix’s server thinks the request is legitimate and processes it.

    - The victim's account settings (e.g., subscription plan) get modified without their knowledge.

#### **Why Did It Happen?**

- Netflix did **not** use CSRF protection, such as requiring **CSRF tokens** or validating the request’s origin.

#### **How Was It Fixed?**

- Netflix later implemented **CSRF tokens** to ensure that sensitive actions required a legitimate request from their website.

### **Lesson from This Attack**

To prevent CSRF attacks:

- **Use CSRF tokens** (hidden, unique values for each form submission).

- **Check the Referer header** to verify requests come from the same domain.

- **Use SameSite cookies** to prevent browsers from sending cookies on cross-site requests.

Let me know if you need a code example of CSRF protection! 🚀

# I have a JQuery web app, how to prevent CSRF

Since you're using **jQuery** in your web app, you need to implement **CSRF protection** to prevent unauthorized actions from malicious sites. Here’s how you can do it:

### **1. Use CSRF Tokens**

A **CSRF token** is a unique, random string that is sent with every request and validated by the server.

#### **Step 1: Generate CSRF Token (Backend)**

In your backend (PHP, Node.js, Django, etc.), generate a CSRF token and store it in the session.

**Example in PHP:**

session_start();

if (!isset(\$\_SESSION\['csrf_token'\])) {

\$\_SESSION\['csrf_token'\] = bin2hex(random_bytes(32));

}

Then, include the CSRF token in your responses:

\<input type="hidden" name="csrf_token" value="\<?php echo \$\_SESSION\['csrf_token'\]; ?\>"\>

#### **Step 2: Attach CSRF Token in jQuery AJAX Requests**

You can send the CSRF token automatically in every AJAX request by adding it to the headers.

\$.ajaxSetup({

beforeSend: function(xhr, settings) {

let csrfToken = \$('meta\[name="csrf-token"\]').attr('content');

if (csrfToken) {

xhr.setRequestHeader("X-CSRF-Token", csrfToken);

}

}

});

Make sure to include the CSRF token in your HTML:

\<meta name="csrf-token" content="YOUR_CSRF_TOKEN_HERE"\>

#### **Step 3: Verify CSRF Token on the Server**

When processing AJAX requests, validate the CSRF token.

**Example in PHP:**

session_start();

if (\$\_SERVER\['REQUEST_METHOD'\] === 'POST') {

if (!isset(\$\_POST\['csrf_token'\]) \|\| \$\_POST\['csrf_token'\] !== \$\_SESSION\['csrf_token'\]) {

die("CSRF token validation failed");

}

}

### **2. Use the SameSite Cookie Attribute**

Modern browsers support the **SameSite** attribute for cookies, which prevents them from being sent with cross-site requests.

Set your session cookies to SameSite=Strict or SameSite=Lax in your backend.

**Example in PHP:**

session_set_cookie_params(\[

'SameSite' =\> 'Strict',

'Secure' =\> true,

'HttpOnly' =\> true

\]);

session_start();

### **3. Validate the Origin Header**

For extra security, check the Origin or Referer header in your backend.

**Example in PHP:**

if (!isset(\$\_SERVER\['HTTP_ORIGIN'\]) \|\| \$\_SERVER\['HTTP_ORIGIN'\] !== 'https://yourwebsite.com') {

die("Invalid request origin");

}

### **Summary**

✅ Use **CSRF tokens** in forms and AJAX requests.  
✅ **Validate tokens** in the backend.  
✅ Set **SameSite cookies** to prevent cross-site requests.  
✅ Check the **Origin/Referer headers** for extra security.

This will effectively prevent CSRF attacks in your jQuery web app. Let me know if you need help implementing it! 🚀
