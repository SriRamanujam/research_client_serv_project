#!/usr/bin/env python2
#-*- coding: utf-8 -*-

"""
Client component of our chunked network file transfer system.

The client connects to the specified server, and transfers every file in the folder
passed as an argument. It will negotiate with the server to transfer each file
in chunks of a certain length, typically a really small number so each chunk
fits in one packet. This is to ensure atomicity of each segment's transfer.

If something goes wrong, the client will wait a length of time before
attempting to resume the transfer. Upon successful completion, the client 
will exit with a status code of 0.
"""

import sys
import cPickle as pickle
import socket
import argparse
import logging
import os
import time
import thread

MSGLEN = 8192 
TIMEOUT_LEN = 3000

# These lines are my typical involved logging setup.
log = logging.getLogger("Client")
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
strm = logging.StreamHandler(sys.stdout)
strm.setFormatter(fmt)
log.addHandler(strm)
log.setLevel(20)

def send_file(filename):
    """
    Sends an individual file, with all the associated error handling and
    try/except statements such a monumental undertaking should require.
    """
    # todo: deal with socket timeouts
    # todo: deal with os.error
    try:
        addr = (args.server_host, int(args.server_port))
        conn = socket.socket()
        conn.settimeout(2000)
        conn.connect(addr)

        # Initial metadata transfer transaction
        f = open(filename)
        metadata_dict = {}
        metadata_dict['filename'] = os.path.basename(filename)
        metadata_dict['size'] = os.path.getsize(filename)
        log.debug(metadata_dict)
        metadata = pickle.dumps(metadata_dict, -1)
        conn.send(metadata)

        # metadata transaction confirmation
        ret_data = conn.recv(MSGLEN)
        if ret_data != "Filename received":
            log.error("Filename not received, aborting send to retry in five seconds")
            conn.close()
            return False

        def send_chunk(chunk):
            try:
                conn.send(bytearray(chunk))
                res = conn.recv(MSGLEN)
                log.debug(res)
                if res == "Received":
                    return True
                return False
            except socket.timeout:
                log.error("Socket timed out")
                return False
            except socket.error, e:
                log.error(e)
                return False

        # And now we start the file transfer!
        chunk = f.read(MSGLEN)
        while True:
            if chunk == "":
                log.info("File transfer complete")
                conn.send("Transfer done")
                break
            if not send_chunk(chunk):
                log.error("Chunk transfer failed, retrying in 500 ms")
                time.sleep(0.5)
                continue
            chunk = f.read(MSGLEN)

        # at this point we're done! return from the thread
        return True
    except OSError, e:
        log.error(e)
        return False
    except Exception, e:
        log.error(e)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("server_host", help="IP address or hostname of server")
    parser.add_argument("server_port", help="Port server is listening on")
    parser.add_argument("file_path", help="path to files you want to transfer")
    parser.add_argument("--debug", help="enable debug output", action="store_true")

    log.info("Starting up client...")
    args = parser.parse_args()

    if args.debug:
        log.setLevel(10)

    if not os.path.exists(args.file_path):
        log.error("Folder path does not exist, exiting")
        sys.exit(1)

    path = os.path.abspath(args.file_path)
    for f in os.listdir(path):
        log.debug(path)
        # for now, we skip anything that isn't a file for simplicity's sake
        filename = os.path.join(path, f)
        log.debug(filename)
        if not os.path.isfile(filename):
            log.debug("not a file")
            continue

        while not send_file(filename):
            time.sleep(5)
