# Chunked Client/Server Transfer Application

This project provides a basic implementation of a chunked file-transfer system that essentially tries to guarantee that a folder can be transferred safely from one computer to another, even if the client computer is experiencing a lot of changes in network availability and state.


## Installation and Running the Application.

We recommend to use a virtualenv with this application. It is built to run with Python 2.7, but should be portable to Python 3 with minimal difficulty. To install, download the archive or clone from the git repository, and simply run the client or server files with the appropriate arguments.

Both the server and client come with built-in help, accessibly by passing the `-h` flag to the programs when invoking them.

## Communication Flow

1) Run server.py on the remote computer where you wish the files to be transferred to. Make sure that you have Python2 installed on the server, the script won't work out of the box with Python3. 

2) Run the client on wherever you want to be sending data from. 

3) Cross your fingers and hope (nah not really it'll work).
