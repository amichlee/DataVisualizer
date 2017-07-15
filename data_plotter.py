#!/usr/bin/env python

# read text files and plot them

import matplotlib.pyplot as plt
import numpy as np
import sys

# data file to read given as argument
if len(sys.argv) < 2:
	print "Give the name of the file to read as an argument\n"
	exit()

file = np.loadtxt(sys.argv[1] ,skiprows=1)

print(file)
time = file[:,0];
forces = file[:,1:4]
moments = file[:,4:]

plt.figure(1)
plt.subplot(2,1,1)
plt.plot(time, forces[:,0],label="Fx")
plt.plot(time, forces[:,1],label="Fy")
plt.plot(time, forces[:,2],label="Fz")
plt.legend()

plt.subplot(2,1,2)
plt.plot(time, moments[:,0],label="Mx")
plt.plot(time, moments[:,1],label="My")
plt.plot(time, moments[:,2],label="Mz")

plt.legend()

plt.show()