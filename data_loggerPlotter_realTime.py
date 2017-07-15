#!/usr/bin/env python

# read redis keys and dump them to a file
import redis, time, signal, sys
import os
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

runloop = True
counter = 0

# handle ctrl-C and close the files
def signal_handler(signal, frame):
	global runloop
	runloop = False
	print('  Exiting data logger')

signal.signal(signal.SIGINT, signal_handler)

# data files
folder = 'debug_robot'
if not os.path.exists(folder):
    os.makedirs(folder)

# date and time
header = time.strftime("%x").replace('/','-') + '_' + time.strftime("%X").replace(':','-')

file_sensed_force = open(folder + '/' + header + '_force.txt','w')

file_sensed_force.write('Sensed force\n')

# open redis server
r_server = redis.StrictRedis(host='localhost', port=6379, db=0)

# redis keys used in SAI2
EE_FORCE_SENSOR_FORCE_KEY = "sai2::optoforceSensor::6Dsensor::force"; #originally commented out

# data logging frequency
logger_frequency = 1000.0  # 1000Hz
logger_period = 1.0/logger_frequency


t_init = time.time()
SIZE_WINDOW = 100
forces = np.zeros((6,SIZE_WINDOW))

labels = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]

print 'Start Logging Data\n'

fig = plt.figure(1)
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)

def animate(idx):
	global t_init
	global forces
	global r_server
	global ax1
	global ax2
	global labelss

	t = time.time() - t_init
	print(t)

	force = json.loads(r_server.get(EE_FORCE_SENSOR_FORCE_KEY))
	forces[:,idx % SIZE_WINDOW] = force

	ax1.clear()
	for i in range(3):
		ax1.plot(range(SIZE_WINDOW), forces[i], label=labels[i])
	ax1.legend()

	ax2.clear()
	for i in range(3,6):
		ax2.plot(range(SIZE_WINDOW), forces[i], label=labels[i])
	ax2.legend()

ani = animation.FuncAnimation(fig, animate, interval=1)
plt.show()

elapsed_time = time.time() - t_init
print "Elapsed time : ", elapsed_time, " seconds"
print "Loop cycles  : ", counter
print "Frequency    : ", counter/elapsed_time, " Hz"