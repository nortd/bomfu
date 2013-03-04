#!/usr/bin/python

import subprocess

subprocess.call("lessc -x boilerplate/bootstrap_less/bootstrap.less > boilerplate/static/css/bootstrap.min.css", shell=True)