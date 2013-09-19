remotefoldersync
================

Fork of rocketmonkeys' project on Google Code, with Python3 support.

## Windows instructions 
1. Install Python3.
2. Install [pycrypto](http://www.voidspace.org.uk/python/modules.shtml#pycrypto).
3. You need a custom paramiko since the normal doesn't have Python3 support.
   `git clone https://github.com/nischu7/paramiko.git`
4. `python setup.py build`
5. Copy `build\lib\paramiko` to `C:\Python33\Lib\paramiko`.
