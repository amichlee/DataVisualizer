#!/usr/bin/env python

from argparse import ArgumentParser
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import redis

import threading
import time
import json

# Constants
REDIS_KEY = "sai2::optoforceSensor::6Dsensor::force"
SIZE_WINDOW = 5000
X_LIM = [0, 10]
Y_LIM = [-1, 1]
LABELS = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]
STYLES = ["r", "g", "b", "r", "g", "b"]
SUBPLOT_START = [0, 3]

# Global variables
g_runloop = True

class RealtimePlotter:
    def __init__(self):
        self.idx  = 0
        self.idx_lock = threading.Lock()
        self.channel = 0
        self.channel_lock = threading.Lock()
        self.time = [np.zeros((SIZE_WINDOW,)) for _ in range(2)]
        self.data = [np.zeros((len(LABELS), SIZE_WINDOW)) for _ in range(2)]

    def redis_thread(self, logfile="output.log", host="localhost", port=6379):
        # Connect to Redis
        redis_client = redis.StrictRedis(host=host, port=port)

        # Open log file
        with open(logfile, "w") as f:
            t_init = time.time()
            t_loop = t_init
            while g_runloop:
                # Get Redis key
                str_data = redis_client.get(REDIS_KEY)
                t_curr = time.time()

                # TODO: remove
                str_data = " ".join(str(x) for x in np.sin(np.array(range(6)) + t_curr).tolist())

                # Parse Redis string
                try:
                    if str_data[0] == "[":
                        data = json.loads(str_data)
                    else:
                        data = [float(el.strip()) for el in str_data.split(" ")]
                except:
                    print("Invalid Redis key: {0} = {1}".format(REDIS_KEY, str_data))
                    time.sleep(0.1)
                    continue

                # Write to log
                f.write("{0}\t{1}\n".format(t_curr - t_init, str_data))

                # Update loop time
                if self.idx == 0:
                    t_loop = t_curr
                    self.channel_lock.acquire()
                    self.channel = 1 - self.channel
                    self.channel_lock.release()

                # Update data
                self.time[self.channel][self.idx] = t_curr - t_loop
                self.data[self.channel][:,self.idx] = data

                # Increment loop index
                self.idx_lock.acquire()
                self.idx += 1
                if self.idx >= SIZE_WINDOW:
                    self.idx = 0
                self.idx_lock.release()

    def plot_thread(self):
        # Set up plot
        subplots = SUBPLOT_START + [len(LABELS)]
        num_subplots = len(SUBPLOT_START)
        fig, axes = plt.subplots(nrows=num_subplots)
        if num_subplots == 1:
            axes = [axes]
        lines = []
        # Add lines for current channel
        for i in range(num_subplots):
            lines += [axes[i].plot([], [], STYLES[j], label=LABELS[j], animated=True)[0] for j in range(subplots[i],subplots[i+1])]
        # Add lines for old channel
        for i in range(num_subplots):
            lines += [axes[i].plot([], [], STYLES[j] + ":", animated=True)[0] for j in range(subplots[i],subplots[i+1])]
        for ax in axes:
            ax.legend()
            ax.set_xlim(X_LIM)
            ax.set_ylim(Y_LIM)

        # Set up animation
        t_init = time.time()
        def animate(idx):
            # Prevent redis_thread from changing channels during this function
            self.channel_lock.acquire()

            # Find the current timestamp in the old channel
            self.idx_lock.acquire()
            idx_curr = self.idx
            self.idx_lock.release()
            t_curr = self.time[self.channel][idx_curr-1]
            idx_old = np.searchsorted(self.time[1-self.channel], t_curr, side="right")

            for i, line in enumerate(lines):
                if i < 6:
                    # Plot the current channel up to the current timestamp
                    line.set_data(self.time[self.channel][:idx_curr], self.data[self.channel][i,:idx_curr])
                else:
                    # Plot the old channel from the current timestamp
                    line.set_data(self.time[1-self.channel][idx_old:], self.data[1-self.channel][i-6,idx_old:])

            self.channel_lock.release()
            return lines

        # Plot
        ani = FuncAnimation(fig, animate, range(SIZE_WINDOW), interval=1, blit=True)
        plt.show(block=False)

        # Close on <enter>. Throws an exception on empty input()
        try:
            input("Hit <enter> to close.")
        except:
            pass
        g_runloop = False
        plt.close()

if __name__ == "__main__":
    # Parse arguments
    parser = ArgumentParser(description=(
        "Plot Optoforce sensor readings in real time."
    ))
    parser.add_argument("-rh", "--redis_host", help="Redis hostname (default: localhost)", default="localhost")
    parser.add_argument("-rp", "--redis_port", help="Redis port (default: 6379)", default=6379, type=int)
    parser.add_argument("-o", "--output", help="Output log (default: output.log)", default="output.log")
    args = parser.parse_args()

    # Initialize class
    rp = RealtimePlotter()

    # Start Redis thread
    t1 = threading.Thread(target=rp.redis_thread, args=(args.output, args.redis_host, args.redis_port))
    t1.daemon = True
    t1.start()

    # Start plotting thread
    rp.plot_thread()
