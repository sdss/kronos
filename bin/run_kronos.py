#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
This script is used to launch petunia.

Application initialization should go here.

'''

import argparse

from flask import Flask
from werkzeug.contrib.profiler import ProfilerMiddleware

# --------------------------
# Parse command line options
# --------------------------
parser = argparse.ArgumentParser(description='Script to start the Petunia plate info server.')
parser.add_argument('-d','--debug',
                    help='Launch app in debug mode.',
                    action="store_true",
                    required=False)
parser.add_argument('--profile',
                    help='Launch app in debug mode.',
                    action="store_true",
                    required=False)
parser.add_argument('-p','--port',
                    help='Port to use in debug mode.',
                    default=5000,
                    type=int,
                    required=False)
parser.add_argument('-r','--rules',
                    help='List registered rules.',
                    action="store_true",
                    default=False,
                    required=False)
parser.add_argument('-s','--safe',
                    help='connect app to dev db.',
                    action="store_true",
                    required=False)

args = parser.parse_args()

# -------------------
# Create app instance
# -------------------
from kronos import create_app

app = create_app(debug=args.debug, dev=args.safe)

if __name__ == "__main__":
    '''
    This is called when this script is directly run.
    uWSGI gets the "app" object (the "callable") and runs it itself.
    '''
    if args.debug:
        # Safari blocks some high ports (e.g.port 6000)
        # Ref: http://support.apple.com/kb/TS4639
        # import sdss
        # print("petunia sdss location: %s"%sdss.__file__)
        if args.profile:
            app.config["PROFILE"] = True
            app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30], stream=None)
        app.run(debug=args.debug, port=args.port)
    else:
        app.run()

# PLACE NO CODE BELOW THIS LINE - it won't get called. "app.run" is the main event loop.
