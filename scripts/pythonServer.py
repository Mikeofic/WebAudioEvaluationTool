#!/usr/bin/python

import BaseHTTPServer
from os import walk
from os import path
from os import listdir
import inspect
import os
import urllib2
import urlparse
import pickle
import datetime

# Go to right folder. 
scriptdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory
os.chdir(scriptdir) # does this work?

PSEUDO_PATH = 'example_eval/'
pseudo_files = []
for filename in listdir(PSEUDO_PATH):
    if filename.endswith('.xml'):
        pseudo_files.append(filename)

curSaveIndex = 0;
curFileName = 'test-0.xml'
while(path.isfile('saves/'+curFileName)):
	curSaveIndex += 1;
	curFileName = 'test-'+str(curSaveIndex)+'.xml'

pseudo_index = curSaveIndex % len(pseudo_files)

print 'URL: http://localhost:8000/index.html'

def send404(s):
	s.send_response(404)
	s.send_header("Content-type", "text/html")
	s.end_headers()
	
def processFile(s):
	s.path = s.path.rsplit('?')
	s.path = s.path[0]
	s.path = s.path[1:len(s.path)]
	st = s.path.rsplit(',')
	lenSt = len(st)
	fmt = st[lenSt-1].rsplit('.')
	size = path.getsize(urllib2.unquote(s.path))
	fileDump = open(urllib2.unquote(s.path))
	s.send_response(200)
	
	if (fmt[1] == 'html'):
		s.send_header("Content-type", 'text/html')
	elif (fmt[1] == 'css'):
		s.send_header("Content-type", 'text/css')
	elif (fmt[1] == 'js'):
		s.send_header("Content-type", 'application/javascript')
	else:
		s.send_header("Content-type", 'application/octet-stream')
	s.send_header("Content-Length", size)
	s.end_headers()
	s.wfile.write(fileDump.read())
	fileDump.close()

def keygen(s):
	reply = ""
	options = s.path.rsplit('?')
	options = options[1].rsplit('=')
	key = options[1]
	print key
	if os.path.isfile("saves/save-"+key+".xml"):
		reply = "<response><state>NO</state><key>"+key+"</key></response>"
	else:
		reply = "<response><state>OK</state><key>"+key+"</key></response>"
	s.send_response(200)
	s.send_header("Content-type", "application/xml")
	s.end_headers()
	s.wfile.write(reply)
	file = open("saves/save-"+key+".xml",'w')
	file.write("<waetresult key="+key+"/>")
	file.close();

def saveFile(self):
	global curFileName
	global curSaveIndex
	options = self.path.rsplit('?')
        options = options[1].rsplit('=')
        key = options[1]
        print key
	varLen = int(self.headers['Content-Length'])
	postVars = self.rfile.read(varLen)
	print "Saving file key "+key
	file = open('saves/save-'+key+'.xml','w')
	file.write(postVars)
	file.close()
	try:
		wbytes = os.path.getsize('saves/save-'+key+'.xml')
	except OSError:
		self.send_response(200)
		self.send_header("Content-type", "text/xml")
		self.end_headers()
		self.wfile.write('<response state="error"><message>Could not open file</message></response>')
	self.send_response(200)
	self.send_header("Content-type", "text/xml")
	self.end_headers()
	self.wfile.write('<response state="OK"><message>OK</message><file bytes="'+str(wbytes)+'">"saves/'+curFileName+'"</file></response>')
	curSaveIndex += 1
	curFileName = 'test-'+str(curSaveIndex)+'.xml'

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_HEAD(s):
		s.send_response(200)
		s.send_header("Content-type", "text/html")
		s.end_headers()
	def do_GET(request):
		global pseudo_index
		global pseudo_files
		global PSEUDO_PATH
		if(request.client_address[0] == "127.0.0.1"):
			if (request.path == "/favicon.ico"):
				send404(request)
			elif (request.path.split('?',1)[0] == "/keygen.php"):
				keygen(request);
			else:
				if (request.path == '/'):
					request.path = '/index.html'
				elif (request.path == '/pseudo.xml'):
					request.path = '/'+PSEUDO_PATH + pseudo_files[pseudo_index]
					print request.path
					pseudo_index += 1
					pseudo_index %= len(pseudo_files)
				processFile(request)
		else:
			send404(request)

	def do_POST(request):
		if(request.client_address[0] == "127.0.0.1"):
			if (request.path.rsplit('?',1)[0] == "/save" or request.path.rsplit('?',1)[0] == "/save.php"):
				saveFile(request)
		else:
			send404(request)

def run(server_class=BaseHTTPServer.HTTPServer,
        handler_class=MyHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

run()