#!/usr/bin/env python3
import sys
import argparse
import daemon

VERSION = "0.1-beta"

arg_parser = argparse.ArgumentParser(
        prog = "cli",
        formatter_class=argparse.RawTextHelpFormatter,
        description = "cli of simple file server/client",
        epilog = "LZZZ in OSH"
)

mutual_group = arg_parser.add_mutually_exclusive_group(required=True)

mutual_group.add_argument("-d", "--daemon", type=str, metavar="workdir", help="run as a daemon at workdir")
arg_parser.add_argument("-a", "--addr", type=str, help="which address to connect/listen\nempty string with -d means listen to all available address", required=True)
arg_parser.add_argument("-p", "--port", type=int, help="which port to connect/listen", required=True)
mutual_group.add_argument("-u", "--upload", action="append", type=str, metavar="file_to_upload", help="upload a file to server")
mutual_group.add_argument("-s", "--save", action="append", type=str, metavar="file_to_download", help="download a file from server")

args = arg_parser.parse_args()

if args.daemon:
    server = daemon.Daemon(args.daemon)
    server.run(args.addr, args.port)
else:
    client = daemon.Client(args.addr, args.port)
    if args.upload:
        for file_to_upload in args.upload:
            client.upload_file(file_to_upload)
    elif args.save:
        for file_to_download in args.save:
            client.download_file(file_to_download)
    client.finish()
