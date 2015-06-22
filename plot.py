from mate import MateController
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
from threading import Thread, Lock
from collections import deque

N = 1000 # History length, in samples

class DynamicAxes:
    def __init__(self, axes, windowSize):
        self.mate = mate
        self.windowSize = windowSize
        self.i = 0
        self.x = np.arange(windowSize)
        self.yi = []
        self.axes = axes
        for ai in axes:
            self.yi.append(deque([0.0]*windowSize))

        self.fig = None
        self.ax = None
        self.mutex = Lock()

    def _addToBuf(self, buf, val):
        if len(buf) < self.windowSize:
            buf.append(val)
        else:
            buf.pop()
            buf.appendleft(val)

    def update(self, data):
        """
        Call this in a separate thread to add new samples
        to the internal buffers. By keeping this separate
        from the animation function, the GUI is not blocked.
        """
        assert len(data) == len(self.axes)
        with self.mutex:
            for i in range(len(self.axes)):
                self._addToBuf(self.yi[i], data[i])

    def anim(self, *args):
        """ Used by matplotlib's FuncAnimation controller """
        # Update the plot data, even if it hasn't changed
        with self.mutex:
            for i, ai in enumerate(self.axes):
                ai.set_data(self.x, self.yi[i])




if __name__ == "__main__":
    mate = MateController('COM19')

    # Set up plot
    fig = plt.figure()
    ax = plt.axes(xlim=(0, N), ylim=(0, 30))
    a1, = ax.plot([],[])
    a2, = ax.plot([],[])

    plt.legend([a1, a2], ["Battery V", "PV V"])

    data = DynamicAxes([a1, a2])

    # Set up acquisition thread
    def acquire():
        while True:
            status = mate.read_status()
            print "BV:%s, PV:%s" % (status.bat_voltage, status.pv_voltage)
            data.update([status.bat_voltage, status.pv_voltage])
    thread = Thread(target=acquire)
    thread.start()

    # Show plot
    anim = animation.FuncAnimation(fig, data.anim, interval=1000/25)
    plt.show()

