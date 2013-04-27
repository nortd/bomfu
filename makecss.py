#!/usr/bin/python

# http://lesscss.org/
# install npm: sudo apt-get install npm
# install less: sudo npm install -g less

import subprocess

subprocess.call("lessc -x boilerplate/bootstrap_less/bootstrap.less > boilerplate/static/css/bootstrap.min.css", shell=True)