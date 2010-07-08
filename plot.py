#!/usr/bin/python
#######################################################################################################################################
# 
# Code to display the information accumulated by bthomehub.py
#
#######################################################################################################################################
#
# Credentials stored in ~/.bthomehubmonitor/credentials
# Options stored in     ~/.bthomehubmonitor/options
# 
#######################################################################################################################################

#######################################################################################################################################
# Load options and credentials

import os.path 
path = os.path.expanduser('~') + '/.bthomehubmonitor/'

optionsdict = dict()
h = open(path + 'options', 'r')
for line in h.readlines(): optionsdict[line.split('=')[0].strip()] = line.split('=')[1].strip()
h.close()

try:
	outputfile = optionsdict['outputfile']
except KeyError:
	print('Output file not specified.  Defaulting to ~/.bthomehubmonitor/log.txt')
	outputfile = 'log.txt'

#####################################################################################################################################

h = open(path + outputfile, 'r')
text = h.read()
h.close()

cols = {'stamp': [], 'uptime': [], 'dataTX': [], 'dataRX': [], 'dataTOTAL': [], 'publicIP': [], 'gateway': [], 'primaryDNS': [], 'secondaryDNS': []}
keys = ['stamp', 'uptime', 'dataTX', 'dataRX', 'dataTOTAL', 'publicIP', 'gateway', 'primaryDNS', 'secondaryDNS']
for line in text.split('\n')[:-1]:
	items = [i.split()[0] for i in line.split(',')]
	for n in range(len(items)):
		cols[keys[n]].append(items[n])

for key in ['stamp', 'uptime', 'dataTX', 'dataRX', 'dataTOTAL']:
	cols[key] = [float(i) for i in cols[key]]

from pylab import *

x = array(cols['stamp'])
y = array(cols['dataTOTAL'])
dy = y[1:] - y[:-1]
dypos = dy * (dy > 0)
ypos = zeros(len(y))
ypos[0] = y[0]
ypos[1:len(y)] = cumsum(dypos) + y[0]
y = ypos[:]

from datetime import datetime, date
#start_of_month = 1272668400	# currently hard-coded for 2010 May
start_of_month = int(datetime.strptime(datetime.now().strftime('%Y-%m-01'), '%Y-%m-%d').strftime('%s'))

import time
now = time.time()

yesterday = now - 24*60*60
quota = 10000.

import calendar
seconds_in_the_month = calendar.mdays[date.today().month]*24*60*60

quota_rate = quota/seconds_in_the_month
Nlimit = sum(x < start_of_month)-1

#dydx = (y[-Nlimit+1]-y[-Nlimit])/(x[-Nlimit+1]-x[-Nlimit])
dydx = (y[Nlimit+1]-y[Nlimit])/(x[Nlimit+1]-x[Nlimit])
use_at_start_of_month = y[Nlimit+1] - (x[Nlimit+1]-start_of_month)*dydx

limit = use_at_start_of_month + (x - start_of_month) * quota/seconds_in_the_month

# All available data
#figure()
#title('All available data')
#plot(x, y, '.')
#plot(x[-Nlimit:], limit[-Nlimit:])

# Current month
#~ N = sum(x > start_of_month)
#~ print 'Readings since start of month: %u' % N
#~ figure()
#~ title('Current month')
#~ plot(x[:]-start_of_month, y[:]-use_at_start_of_month, '.-b', alpha='0.1')
#~ plot(x[-N:]-start_of_month, y[-N:]-use_at_start_of_month, '.-b')
#~ plot([0,seconds_in_the_month], [0, quota], 'r')
#~ xlim([0,seconds_in_the_month])
#~ ylim([0, quota])

# So far this month
xunit = {'name': 'Hours', 'seconds': 60*60}
#xunit = {'name': 'Days', 'seconds': 24*60*60}
yunit = {'name': 'MB', 'MBs': 1}
N = sum(x > start_of_month)
print 'Readings since start of month: %u' % N
figure()
title('So far this month')
plot((x[:]-start_of_month)  /xunit['seconds'], (y[:]-use_at_start_of_month)  /yunit['MBs'], '.-b', alpha='0.1')
plot((x[-N:]-start_of_month)/xunit['seconds'], (y[-N:]-use_at_start_of_month)/yunit['MBs'], '.-b')

plot([0, seconds_in_the_month/xunit['seconds']], [0, quota/yunit['MBs']], 'r')

xlim([0, 1.1*(x[-1]-start_of_month)/xunit['seconds']])
ylim([0, 1.1*max([quota_rate*(x[-1]-start_of_month), y[-1]-use_at_start_of_month])/yunit['MBs']])

#ylim([0, y[-1]-use_at_start_of_month])

xlabel('Time/%s' % xunit['name'])
ylabel('Data/%s' % yunit['name'])

# Last 24 hours
#~ N = sum(x > yesterday)
#~ print 'Readings in last 24 hours: %u' % N
#~ figure()
#~ title('Last 24 hours')
#~ plot(x[:]-x[-N], y[:]-use_at_start_of_month, '.-b', alpha='0.1')
#~ plot(x[-N:]-x[-N], y[-N:]-use_at_start_of_month, '.-')
#~ plot([0,seconds_in_the_month], [0, quota], 'r')
#~ xlim([min(x[-N:]-x[-N]), max(x[-N:]-x[-N])])
#~ #ylim([min(y[-N:]-use_at_start_of_month), max(y[-N:]-use_at_start_of_month)])
#~ ylim([0, 1.1*quota_rate*max(x[-N:]-x[-N])])

# Differential
#dx = x[1:] - x[:-1]
#dy = y[1:] - y[:-1]
#x0 = (x[1:] + x[:-1])/2
#figure()
#plot(x0, dy/dx)
#ylim([0, 1.1*max(dy/dx)])

MBs_over_quota_so_far = (y[-1]-use_at_start_of_month)-(quota_rate*(x[-1]-start_of_month))
seconds_to_wait = MBs_over_quota_so_far/quota_rate
if MBs_over_quota_so_far > 0:
	print 'You are %u %s over your quota so far this month' % (MBs_over_quota_so_far/yunit['MBs'], yunit['name'])
	print 'If you use no data for %u %s, you will be within your quota' % (seconds_to_wait/xunit['seconds'], xunit['name'])
else:
	print 'You are %u %s below your quota so far this month' % (MBs_over_quota_so_far/yunit['MBs'], yunit['name'])
	print 'You are %u %s behind your quota' % (seconds_to_wait/xunit['seconds'], xunit['name'])

show()

