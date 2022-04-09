Our high level approach was to keep crawling until we had found all of our secret flags. We implemented the basic HTTP functions GET and POST and stored cookies that the server gave us using the CSRF token and session ID. We also had to implement 2 subclasses of HTMLParser to handle getting the middleware token, URL to crawl, and flags. 

I think the biggest challenge in this project was implementing the GET and POST requests. We found it difficult to find the correct data given by the server, and also to format the requests. As a result, a lot of our time was spent trying to debug 400 errors. 

Most of our testing was done by just running the script and seeing the return requests/errors from the server. In the end, we knew that our program worked when we got our secret flags.