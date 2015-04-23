#!/usr/bin/env python2
#-*- coding: utf-8 -*-

"""
Server component of the automatic data-transfer application.

This server listens on the specified socket on all available interfaces
and receives connections from clients. Each client connection is dispatched
to its own thread, where the client and server negotiate and transfer 
the desired dataset serially, with built-in error checking. Once this transfer
is completed, the server terminates the connection.
"""

import sys
import cPickle as pickle
import socket
import argparse
import logging
import os.path
import thread

# good balance for medium-to-large files
# todo: maybe make this a tweakable knob?
MSGLEN = 8192

# These lines are my typical involved logging setup.
log = logging.getLogger("Server")
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
strm = logging.StreamHandler()
strm.setFormatter(fmt)
log.addHandler(strm)
log.setLevel(20)

def handleConnection(sock, folderPath):
    """Thread function to handle the actual file transfer."""
    size = 0
    try:
        sock.settimeout(2000)
        # initial metadata transfer transaction
        data = sock.recv(MSGLEN)
        log.debug("received initial metadata")
        metadata = pickle.loads(data)
        size = int(metadata['size'])
        filename = metadata['filename']
    except pickle.UnpicklingError:
        log.error("Unpickling error occurred, life is hard")
        sock.send("Error, filename not received".encode('utf-8'))
        return

    # metadata transfer confirmation
    log.debug("sending metadata receive confirmation")
    sock.send("Filename received".encode('utf-8'))

    # Here we open the new file and begin writing to it
    path = os.path.join(folderPath, filename)
    log.debug("path is " + str(path))
    open(path, "a").close() # creates the new file so that we can write to it

    # ACHTUNG: This will not overwrite pre-existing files with the same name!
    # It will append. This is to help facilitate resuming of transfers.
    with open(path, "ab+") as f:
        log.debug("file opened for transfer, of length " + str(size))
        datalen = 0
        while True:
            data = ""
            while len(data) < MSGLEN:
                data += sock.recv(MSGLEN - len(data))
                log.debug("buffer size is now " + str(len(data)))
                log.debug("total data received is now " + str(datalen))
                if (datalen + len(data)) == size:
                    # We've received the full file (presumably)
                    log.debug("full file received, continuing")
                    datalen = 0
                    break
                if data == "Transfer done":
                    # This is to break the recv loop so processing can proceed
                    break
            log.debug("chunk received")
            if data == "Transfer done":
                log.info("Transfer complete")
                break
            datalen += len(data)
            log.debug("datalen is now " + str(datalen))
            f.write(bytearray(data))
            f.flush()
            sock.send("Received".encode('utf-8'))
            log.debug("Chunk receive confirmation sent")

    return
if __name__ == "__main__":
    # These lines set up our arg parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="the port you want your server to listen on")
    parser.add_argument("folder", help="the folder you wish to store the received files in. Will be created if it doesn't already exist.")
    parser.add_argument("--debug", help="enable debug output", action="store_true")
    args = parser.parse_args()

    if args.debug:
        log.setLevel(10)

    s = socket.socket()
    s.bind(('', int(args.port)))
    s.listen(5)
    log.info("Server started and listening")

    while True:
        # Wait on a connection to be established with the client
        (clientSock, addr) = s.accept()
        log.info("Received connection from " + addr[0])
        thread.start_new_thread(handleConnection, (clientSock, args.folder))

