<p>This script works by first using argparse to read the terminal command. 
It then initiates a socket according to these arguments, and wraps the socket using SSL if necessary. 
Next, after connecting to the port, the socket will send the first HELLO message, and convert the response into a list of arguments in the format: ['ex_string', 'FIND', 'character to search for', 'string to search in']. This process repeats 
until the socket encounters a statement that is not a FIND statement. If the new message is a BYE message, the 
socket will print the following secret flag. Otherwise, it will print 'Could not find secret flag' to the terminal.<p> 
<p>The biggest challenge that I faced during this project was using argparse and the command line. This was the first time that I used the library and the first time that I ssh-ed into a different server, and was very unfamiliar with functions like add_argument. However, I actually using and connecting the socket was much easier than I anticipated, and I definitely have a better understanding of how the connection works after this project.<p>

