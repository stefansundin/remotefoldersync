'''
FTP Folder Sync
===============
Copyright 2010 James Yoneda
Licensed under the GPL v3.


This program connects to a remote FTP/SSH server.  It monitors a local folder, and automatically uploads any changed files.

Currently it only checks the file modification time.

Usage:

remotefoldersync.py --ftp -u [username] -p [password] -h [hostname] [local_folder] [remote_folder]

--ftp - specify the server as FTP instead of SSH.
-u [username] - optional, the username.
-p [password] - optional, the password.
-h [hostname] - optional, the hostname.
[local_folder] - the local folder to monitor for changes.
[remote_folder] - the remote folder that mirros the local_folder.  NOTE: You cannot currently use the ~ symbol.  Just use a relative path like "path/to/folder" or an absolute path like "/path/to/folder".

'''

import getopt
import sys
import os
import hashlib
import time
import subprocess

import ssh

files = {}

username = None
password = None
hostname = None
keyfile = None

class File:
	'Keeps track of the modification time of a file.'
	def __init__(self, filename):
		self.filename = filename
		self.date_modified = os.stat(self.filename).st_mtime
		self.size = os.stat(self.filename).st_size
		self.digest = None
		
		self.has_changed()
		
	
	def has_changed(self):
		# TODO: Check file hash.
		#sha1 = hashlib.sha1()
		#sha1.update(open(self.filename, 'r').read())
		#digest = sha1.hexdigest()
		#print 'digest: %s' % digest
		#if digest != self.digest:
		#	self.digest = digest
		#	return True
		#else:
		#	return False
		
		date_modified = os.stat(self.filename).st_mtime
		if date_modified != self.date_modified:
			self.date_modified = date_modified
			return True
		else:
			return False

def get_relative_path(root, path):
	'Returns the path of a file relative to the root.'
	root = os.path.abspath(root)
	path = os.path.abspath(path)
	
	if root[-1:] != os.sep:
		root += os.sep
	
	assert path.startswith(root)
	return path[len(root):]

def to_unix_path(path):
	return path.replace('\\', '/')

def to_win_path(path):
	return path.replace('/', '\\')

def unix_path_join(path1, path2):
	'Like os.path.join(), but not OS dependent (unix only).'
	if path1[-1:] != '/' and len(path1) > 0:
		path1 += '/'
	if path2[:1] == '/':
		path2 = path2[1:]
	return path1 + path2

first_update = True

def update_folder(con, local_folder, remote_folder):
	'Scan a local folder, upload any changed/new files.'
	global first_update
	
	for dirpath, dirnames, filenames in os.walk(local_folder):
		
		# By default ignore all '.svn' files/folders.
		for dirname in dirnames[:]:
			if dirname.find('.svn') != -1:
				dirnames.remove(dirname)
		
		for filename in filenames:
			# Check all files in the local folder.
			filename_full = os.path.join(dirpath, filename)
			
			def put_file(filename_full, local_folder, remote_folder):
				'Send a file to the remote SSH/FTP server.'
				filename_rel = get_relative_path(local_folder, filename_full)
				filename_rel = to_unix_path(filename_rel)
				remote_filename = unix_path_join(remote_folder, filename_rel)
				print 'Uploading "%s"...' % filename_full,
				con.put(filename_full, remote_filename)
				print 'Done.'
			
			if filename_full in files:
				# File has changed, keep sending until it has finished changing (in case it's currently be written to).
				while files[filename_full].has_changed():
					put_file(filename_full, local_folder, remote_folder)
			else:
				# New file, add it.
				files[filename_full] = File(filename_full)
				if not first_update:
					# A file has been created, send it.  If this were the first run, all files would be "new".
					put_file(filename_full, local_folder, remote_folder)
	
	if first_update:
		first_update = False
		

	
def usage():
	print 'Usage:'
	print 'remotefoldersync.py --ftp -u [username] -p [password] -h [hostname] [local_folder] [remote_folder]'
	print ''
	print 'If --ftp is specified, then FTP will be used.  Otherwise, SSH will be used.'
	print ''
	exit()

def main():
	global hostname, username, password, keyfile
	
	local_folder = None
	remote_folder = None
	use_ftp = False
	
	opts, args = getopt.getopt(sys.argv[1:], 'u:p:h:', ['key=', 'ftp'])
	for name, value in opts:
		if name == '-u':
			username = value
		elif name == '-p' and value.strip() != '':
			password = value
		elif name == '-h':
			hostname = value
		elif name == '--key' and value.strip() != '':
			keyfile = value
		elif name == '--ftp':
			use_ftp = True
	
	if len(args) < 2 or username is None or hostname is None or (password is None and keyfile is None):
		usage()
	
	local_folder = args[0]
	remote_folder = args[1]
	
	if use_ftp:
		from ftplib import FTP
		ftp_con = FTP()
		
		hostname, port = hostname.split(':')
		if port == '':
			port = None
		ftp_con.connect(hostname, port)
		
		if username is None:
			username = ''
		if password is None:
			password = ''
		ftp_con.login(username, password)
		
		# Simple wrapper so FTP looks more like the ssh.py class.
		class FTPWrapper:
			def __init__(self, con):
				self.con = con
			
			def put(self, filename_full, remote_filename):
				self.con.storbinary('STOR %s' % remote_filename, open(filename_full, 'rb'))
			
		con = FTPWrapper(ftp_con)
		
	else:
		con = ssh.Connection(host=hostname, username=username, password=password, private_key=keyfile)
	print ''
	print 'Monitoring "%s" for changes...' % local_folder
	while True:
		update_folder(con, local_folder, remote_folder)
		#print '.'
		time.sleep(1)
		
	con.close()

if __name__ == "__main__":
	main()

