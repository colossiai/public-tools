# **When I login the website, fetch() automatically brings the login token for the request?**

Yes, fetch() will automatically include the login token (cookies, session ID, or other credentials) **if the website uses cookies for authentication** and you are making a request to the **same origin** (same domain as the website you are logged into).

### ✅ Default Behavior

By default, fetch() **includes cookies** for same-origin requests but **does NOT include cookies** for cross-origin requests.

### 🔥 To Ensure Cookies Are Sent for Cross-Origin Requests

If you're making a request to a different domain (cross-origin request), you **must** enable credentials explicitly:

fetch('https://example.com/api/data', {

credentials: 'include' // Ensures cookies and credentials are sent

})

.then(response =\> response.json())

.then(data =\> console.log(data))

.catch(error =\> console.error('Error:', error));

### 🔑 When Will the Token Not Be Included?

1.  **If the site uses local storage or session storage instead of cookies**, then fetch() won't automatically send the token. You’ll need to manually retrieve it:

> let token = localStorage.getItem('authToken'); // Example: stored in localStorage
>
> fetch('https://example.com/api/data', {
>
> headers: { 'Authorization': 'Bearer ' + token }
>
> })

2.  **If the website sets cookies with HttpOnly and Secure attributes**, they will be sent automatically but cannot be accessed via JavaScript for security reasons.

3.  **If the API requires custom headers**, you must include them manually.

Let me know if you're dealing with a specific case! 🚀
