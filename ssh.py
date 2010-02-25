"""
Friendly Python SSH2 interface.
Copied from http://media.commandline.org.uk//code/ssh.txt
Modified by James Yoneda to include command-line arguments.
"""

import getopt
import os
import paramiko
import sys
import tempfile

class Connection(object):
	"""Connects and logs into the specified hostname. 
	Arguments that are not given are guessed from the environment.""" 

	def __init__(self,
				 host,
				 username = None,
				 private_key = None,
				 password = None,
				 port = 22,
				 ):
		self._sftp_live = False
		self._sftp = None
		if not username:
			username = os.environ['LOGNAME']

		# Log to a temporary file.
		templog = tempfile.mkstemp('.txt', 'con-')[1]
		paramiko.util.log_to_file(templog)

		# Begin the SSH transport.
		self._transport = paramiko.Transport((host, port))
		self._tranport_live = True
		# Authenticate the transport.
		
		if password:
			# Using Password.
			self._transport.connect(username = username, password = password)
		else:
			## Use Private Key.
			#if not private_key:
			#	# Try to use default key.
			#	if os.path.exists(os.path.expanduser('~/.con/id_rsa')):
			#		private_key = '~/.con/id_rsa'
			#	elif os.path.exists(os.path.expanduser('~/.con/id_dsa')):
			#		private_key = '~/.con/id_dsa'
			#	else:
			#		raise TypeError, "You have not specified a password or key."

			private_key_file = os.path.expanduser(private_key)
			rsa_key = paramiko.RSAKey.from_private_key_file(private_key_file)
			self._transport.connect(username = username, pkey = rsa_key)
	
	def _sftp_connect(self):
		"""Establish the SFTP connection."""
		if not self._sftp_live:
			self._sftp = paramiko.SFTPClient.from_transport(self._transport)
			self._sftp_live = True

	def get(self, remotepath, localpath = None):
		"""Copies a file between the remote host and the local host."""
		if not localpath:
			localpath = os.path.split(remotepath)[1]
		self._sftp_connect()
		self._sftp.get(remotepath, localpath)

	def put(self, localpath, remotepath = None):
		"""Copies a file between the local host and the remote host."""
		if not remotepath:
			remotepath = os.path.split(localpath)[1]
		self._sftp_connect()
		self._sftp.put(localpath, remotepath)

	def execute(self, command):
		"""Execute the given commands on a remote machine."""
		channel = self._transport.open_session()
		channel.exec_command(command)
		output = channel.makefile('rb', -1).readlines()
		if output:
			return output
		else:
			return channel.makefile_stderr('rb', -1).readlines()

	def close(self):
		"""Closes the connection and cleans up."""
		# Close SFTP Connection.
		if self._sftp_live:
			self._sftp.close()
			self._sftp_live = False
		# Close the SSH Transport.
		if self._tranport_live:
			self._transport.close()
			self._tranport_live = False

	def __del__(self):
		"""Attempt to clean up if not explicitly closed."""
		self.close()

def usage():
	print 'Usage:'
	print 'ssh.py -u [username] -p [password] -h [hostname] --key [key_filename] [local_filename] [remote_filename]'
	print ''
	exit()

def main():
	username = None
	password = None
	hostname = None
	keyfile = None
	local_filename = None
	remote_filename = None
	
	opts, args = getopt.getopt(sys.argv[1:], 'u:p:h:', ['key='])
	for name, value in opts:
		if name == '-u':
			username = value
		elif name == '-p' and value.strip() != '':
			password = value
		elif name == '-h':
			hostname = value
		elif name == '--key' and value.strip() != '':
			keyfile = value
	
	if len(args) < 2 or username is None or hostname is None or (password is None and keyfile is None):
		usage()
	
	local_filename = args[0]
	remote_filename = args[1]
	
	#print 'host: %s' % hostname
	#print 'username: %s' % username
	#print 'password: %s' % password
	#print 'keyfile: %s' % keyfile
	#print 'local_filename: %s' % local_filename
	#print 'remote_filename: %s' % remote_filename
		
	con = Connection(host=hostname, username=username, password=password, private_key=keyfile)
	#print 'Putting file "%s" to "%s"' % (local_filename, remote_filename)
	con.put(local_filename, remote_filename)
	
	#results = con.execute('pwd')
	#print 'results: %r' % results
	#
	#results = con.execute('ls')
	#print 'results: %r' % results
	
	con.close()

if __name__ == "__main__":
	main()
