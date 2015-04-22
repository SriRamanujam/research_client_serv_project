#!/usr/bin/env python2
#-*- coding: utf-8 -*-

import sys
import cPickle as pickle
import socket
import argparse
import logging
import os.path
import thread

MSGLEN = 4096

# These lines are my typical involved logging setup.
log = logging.getLogger("Server")
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
strm = logging.StreamHandler()
strm.setFormatter(fmt)
log.addHandler(strm)
log.setLevel(20)

def handleConnection(sock, folderPath):
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

    with open(path, "ab+") as f:
        log.debug("file opened for transfer")
        while True:
            data = sock.recv(MSGLEN)
            log.debug("data received")
            if data == "Transfer done":
                log.info("Transfer complete")
                break
            f.write(bytearray(data))
            f.flush()
            sock.send("Received".encode('utf-8'))

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

