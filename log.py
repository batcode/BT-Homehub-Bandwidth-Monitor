#!/usr/bin/python
#######################################################################################################################################
# 
# Simple, linear code to log-in to the BT Homehub, go to the page with the relevant information, and write this information to a file
#
#######################################################################################################################################
#
# Credentials stored in ~/.bthomehubmonitor/credentials
# Options stored in     ~/.bthomehubmonitor/options
# 
#######################################################################################################################################

# Import the relevant libraries
import urllib, urllib2		# necessary for talking to the webserver on the BT Homehub
from hashlib import md5		# necessary for emulating the password obsfucation which would normally be carried out in JavaScript by the browser
import time			# necessary for time-stamping the data


#######################################################################################################################################
# Load options and credentials

import os.path 
path = os.path.expanduser('~') + '/.bthomehubmonitor/'

optionsdict = dict()
h = open(path + 'options', 'r')
for line in h.readlines(): optionsdict[line.split('=')[0].strip()] = line.split('=')[1].strip()
h.close()

try:
	address = optionsdict['address']
except KeyError:
	print('IP address not specified.  Defaulting to 192.168.1.254')
	address = '192.168.1.254'

try:
	outputfile = optionsdict['outputfile']
except KeyError:
	print('Output file not specified.  Defaulting to ~/.bthomehubmonitor/log.txt')
	outputfile = 'log.txt'
	
try:
	passwordfile = optionsdict['passwordfile']
except KeyError:
	print('Password file not specified.  Defaulting to ~/.bthomehubmonitor/password')
	passwordfile = 'password'

h = open(path + passwordfile)
password = h.read().strip()
h.close()

#######################################################################################################################################
# Create the object which will talk to the webserver
#######################################################################################################################################

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor()) # this includes cookie handling

# Headers, grabed from whatsmyuseragent.com with a real browser, to fool the webserver into thinking we're a real browser
# Drop leading HTTP_ and REFERER and COOKIE entries
headerstring = '''CONNECTION:keep-alive
KEEP_ALIVE:300
ACCEPT:text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
ACCEPT_CHARSET:ISO-8859-1,utf-8;q=0.7,*;q=0.7
ACCEPT_ENCODING:gzip,deflate
ACCEPT_LANGUAGE:en-gb
HOST:192.168.1.254
USER_AGENT:Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.4) Gecko/2008111319 Ubuntu/8.10 (intrepid) Firefox/3.0.4'''

# Add the headers specified in headerstring
for header in headerstring.split('\n'): opener.addheaders.append((header.split(':')[0], header.split(':')[1]))
urllib2.install_opener(opener)

#######################################################################################################################################
# Login and get the data
#######################################################################################################################################
# Go to the log-in page
action="http://%s/login.lp" % address
html = opener.open(action).read()
# and extract the variables, created by the server and presented to the browser in javascript, for use in obsfucation of the password
jsvals = dict()
jsvars = ['realm', 'nonce', 'qop', 'uri']
for line in html.split('\n'):
	for jsvar in jsvars:
		string = 'var %s = ' % jsvar
		if line[:len(string)] == string:
			jsvals[jsvar] = line[len(string)+1:].split(';')[0][:-1]

# Obsfucate the password
# (Original Javascript code below)
#  var user = "admin";
#  var pwd  = document.getElementById("password").value;
#  document.getElementById("password").disabled=true;
#  var HA1 = MD5(user + ":" + realm + ":" + pwd);
#  var HA2 = MD5("GET" + ":" + "/login.lp");
#  document.getElementById("hidepw").value = MD5(HA1 + ":" + nonce + 
#                          ":" + "00000001" + ":" + "xyz" + ":" + qop + ":" + HA2);
#  document.getElementById("authform").submit();
user = 'admin'
pwd = password
HA1 = md5(user + ':' + jsvals['realm'] + ':' + pwd).hexdigest()
HA2 = md5("GET" + ":" + "/login.lp").hexdigest()
hidepw = md5(HA1 + ":" + jsvals['nonce'] + ":" + "00000001" + ":" + "xyz" + ":" + jsvals['qop'] + ":" + HA2).hexdigest()

c = opener.handlers[-2] # should correspond to an urllib2.HTTPCookieProcessor instance; this is a fragile way to extract this object from the opener
rn = c.cookiejar._cookies[address]['/']['xAuth_SESSION_ID'].value

# Simulate submitting the form with this mangled data
data = urllib.urlencode({'hidepw': hidepw, 'rn': rn}) # what about 'rn'?
opener.open(action, data).close()

# Now go to the page with the information we want
url = 'http://%s/bb_internet.lp?be=1&l2=0&l0=2&l1=2' % address
r = opener.open(url)
html = r.read()
r.close()

# and extract the interesting values
# '    var trClass = ["odd", "even"];',
# '        var td1 = ["w3", "Connection time", "Data transmitted/received (MB)", "Broadband user name", "Password"];',
# '        var td3 = ["w3", "Broadband network IP address", "Default gateway", "Primary DNS", "Secondary DNS"];',
# '    ',
# '    ',
# '        var td2 = ["", "14 days, 10:44:24", "244.83 / 5604.16", "bthomehub@btbroadband.com", "********"];',
# '        var td4 = ["", "86.138.104.118", "217.47.112.58", "194.72.0.98", "194.72.9.38"];',

jsvals = dict()
jsvars = ['td2', 'td4']
for line in html.split('\n'):
	tmp = line.strip()
	for jsvar in jsvars:
		string = 'var %s = ' % jsvar
		if tmp[:len(string)] == string:
			jsvals[jsvar] = tmp[len(string)+1:].split(';')[0][:-1]

[w3, uptime,   data_transmitted, username, password] = [a.strip()[1:] for a in jsvals['td2'].split('",')]; password = password[:-1]
[w3, publicIP, gateway,  primaryDNS, secondaryDNS]   = [a.strip()[1:] for a in jsvals['td4'].split('",')]; secondaryDNS = secondaryDNS[:-1]

#######################################################################################################################################
# Now format this data
#######################################################################################################################################

# remove the possible comma from uptime
uptime = uptime.replace(',', '')

# calculate the total data transferred
[dataTX, dataRX] = [d.strip() for d in data_transmitted.split('/')]
dataTOTAL = '%.2f' % (float(dataTX) + float(dataRX))

# mark the time (UNIX epoch)
stamp = '%u' % time.time()

#######################################################################################################################################
# and ouput
#######################################################################################################################################
report = [stamp, uptime, dataTX, dataRX, dataTOTAL, publicIP, gateway, primaryDNS, secondaryDNS]
outputstring = ', '.join(report)
h = open(path + outputfile, 'a')
h.write(outputstring + '\n')
h.close()

#print path + outputfile
