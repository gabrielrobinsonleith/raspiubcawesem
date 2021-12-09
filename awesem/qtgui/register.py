"""
Register
------------------------------

Authors: Brion Ye, Erick Blankenberg
Date: 10/10/2018

Description:
  This thread continuously assigns intensity data acquired from the
  teensy to integer coordinates based on the given reconstruction
  method. The internal methods of this class are also exposed so that you can
  process data outside of the main display pipeline.

Edits:
 - Erick Blankenberg, adapted to use teensy 3.6, moved temp image here. Switched to mpipe
 - Was originally the display thread, divided point assignment and display assignment into two threads

TODO:
 - How to cleanly handle output so that it is easy to save to file,
 - might be better ways to use NUMPY arrays to work faster
 - might be better
"""

import threading
import numpy
import numpy_indexed
from   math             import ceil
import numpy            as np
import awesem.qtgui.constants as Const
import awesem.qtgui.data      as Data
#from   time             import perf_counter

class Register(threading.Thread):
    __DataTranslateX              = None
    __DataTranslateY              = None
    __DataFilterX                 = None
    __DataFilterY                 = None
    __InputBuffer                 = None
    __StandardCallback            = None
    __xOffset                     = 0.0
    __yOffset                     = 0.0
    __MCUInterface                = None
    __DoSample                    = False

    def __init__(self, outputCallback, MCUInterface):
        threading.Thread.__init__(self)
        self.__OutputCallback = outputCallback
        self.__MCUInterface   = MCUInterface

    def run(self):
        while True:
            if self.__DoSample:
                value = self.__MCUInterface.getDataBuffer()
                if value is not None:
                    self.__OutputCallback(self.registerPoints(value))

    def halt(self):
        """Stops acquiring sample blocks for continous streaming.
        """
        self.__DoSample = False

    def commence(self):
        """Starts acquiring sample blocks for continuous streaming.
        """
        self.__DoSample = True

    def registerPoints(self, newestBuffer, functionX = None, functionY = None, filterX = None, filterY = None):
        """
        Description:
          Assigns screen coordinate locations to the given sample data block.

        Parameters:
          'newestBuffer'  Buffer of the format: (aTimestamp, bTimestamp, value (byte); ... ; ...)
          'functionX'     Callback to translate timestamps in microseconds to position, if specified overrides internal function
          'functionY'     Callback to translate timestamps in microseconds to position, if specified overrides internal function
          'filterX'       Callback to filter timestamps, if specified overrides internal function
          'filtery'       Callback to filter timestamps, if specified overrides internal function
        """
        # Checks defaults
        if functionX is None:
            functionX = self.__DataTranslateX
        if functionY is None:
            functionY = self.__DataTranslateY
        if filterX is None:
            filterX = self.__DataFilterX
        if filterY is None:
            filterY = self.__DataFilterY

        # Applies offsets
        newestBuffer[:, 0] = newestBuffer[:, 0] + self.__xOffset;
        newestBuffer[:, 1] = newestBuffer[:, 1] + self.__yOffset;

        # Applies filter function
        boolX = numpy.ones(len(newestBuffer), dtype = bool)
        if filterX is not None:
            boolX = filterX(newestBuffer[:, 0])
        boolY = numpy.ones(len(newestBuffer), dtype = bool)
        if filterY is not None:
            boolY = filterY(newestBuffer[:, 1])
        boolTotal = numpy.logical_and(boolX, boolY)
        newestBuffer = newestBuffer[boolTotal, :]

        if(newestBuffer.size > 0):
            # Applies translation function
            assignedPositionVals = numpy.stack((functionX(newestBuffer[:, 0]), functionY(newestBuffer[:, 1]), newestBuffer[:, 2]), 1).astype(int)
            # Merges duplicate coordinates
            numpy_indexed.group_by(assignedPositionVals[:, [0, 1]]).mean(assignedPositionVals)
            return assignedPositionVals
        print("Threw Buffer")
        return None

    def setDataFilterX(self, filterFunction):
        """
        Description:
          Filters the given data buffer by timestamps for the given access.

        Parameters:
          'filterFunction' Callback to filter a column array of timestamps in
                           milliseconds. Should return a boolean array.
                           Set to None to disable filtering.
        """
        if(callable(filterFunction) or filterFunction is None):
            self.__DataFilterX = filterFunction
            return True
        return False
    def setDataFilterY(self, filterFunction):
        if(callable(filterFunction) or filterFunction is None):
            self.__DataFilterY = filterFunction
            return True
        return False

    def setDataOffsetX(self, offsetTime):
        """
        Description:
          Adds the given value to the timestamp of the given axis in seconds.

        Parameters:
          'offsetTime' Value to add to the timestamp in seconds.
        """
        self.__xOffset = offsetTime
        return True

    def setDataOffsetY(self, offsetTime):
        self.__yOffset = offsetTime
        return True

    def setDataTranslateX(self, translationFunction):
        """
        Desccription:
          Sets the function used to translate the data times to position
          along the specified axis..

        Parameters:
          'translationFunction' Function that takes in a floating point time in seconds
                                and returns a floating point normalized value, 1.0 is maximum.
        """
        if(callable(translationFunction)):
            self.__DataTranslateX = translationFunction
            return True
    def setDataTranslateY(self, translationFunction):
        if(callable(translationFunction)):
            self.__DataTranslateY = translationFunction
            return True
        return False
