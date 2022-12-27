"""
PiPion_Interface
------------------------------

Author: Erick Blankenberg
Date: 8/25/2018

TODO:
  - Connection validation and updating is bad, revisit this module
  - b and a offsets where switched the whole time! Revisit what is defined as
    a and b.
  - Currently internal timing jumps around a bit which causes jumps. Probably rollover on the micros
    used inside of the MCU. Should tie an interrupt to the audio output library
    to handle the timing.
"""
# ----------------------- Imported Libraries ------------------------------------

from   threading import Lock
import struct
import serial
import numpy
from serial.tools import list_ports


# ------------------------ Class Definition -------------------------------------

class AWESEM_PiPion_Interface:
    """
    This class enables communication with the PiPion SEM
    control system.

    Transmission based off of:
        https://folk.uio.no/jeanra/Microelectronics/TransmitStructArduinoPython.html
    You could also use CmdMessenger but currently does not do structs. Getting
    the data back may be difficult and/or inefficient.

    Note:
        See the AWESEM_PiPion.ino file for command details and a comprehensive list.
    """

    # Variables
    _verbose = False # Debugging
    _currentlyConnected = False
    _currentlyScanning  = False
    _serialPort = None # Object for serial communication
    _lastPacketID = 0 # How many sample packets have been recieved
    _guardLock    = Lock() # Had crashes when attempting to set parameters during reads

    # Current values

    _dacFrequencies = None
    _dacWaveforms   = None
    _dacMagnitudes  = None
    _adcFrequency   = None
    _adcAverages    = None

    # Constants
    _SERIAL_RECONNECTIONATTEMPTS = 1 # Number of times to try all ports once.
    _SERIAL_TIMEOUT = 0.1 # Timeout in seconds
    _SERIAL_DATASTRUCT_BUFFERSIZE = 1024 # Make sure that this is the same as specified in the MCU code

    # -------------------- Public Members ---------------

    def __init__(self):
        """Initializes communications over serial to the PiPion
        """
        self.reconnectToPion()
        self._lastBlock = 0 # Tracks buffer count
        self.pauseEvents()  # Not trusting default state of PiPion
        # Updates client-side history to reflect default values in firmware
        self.getDacFrequency(1)
        self.getDacMagnitude(1)
        self.getDacWaveform(1)
        self.getAdcFrequency()
        self.getAdcAverages()

    def __del__(self):
        """Safely closes the connection
        """
        self.pauseEvents()
        self.close()

    def setVerbose(self, enableVerbose):
        """Prints information for debugging
        """
        self._verbose = enableVerbose

    def connectedToPion(self):
        return self._currentlyConnected

    def reconnectToPion(self):
        """Attempts to reestablish connection with the PiPion
        """
        if self._findPort():
            self._currentlyConnected = True;
            return True
        return False

    def close(self):
        """Safely closes the connection to the PiPion.
        """
        self._serialPort.close()

    def isScanning(self):
        return self._currentlyScanning

    def ping(self):
        """
         Description:
           Pings the MCU to see if it is still alive.

         Returns:
           True if the MCU responds well, false otherwise.
        """
        self._sendBytes(b'p')
        return self._readBytes(1) == b'A'

    def getBufferSize(self):
        return self._SERIAL_DATASTRUCT_BUFFERSIZE;

    def getDacFrequency(self, dacChannel, forceDirect = False):
        """
        Description:
          Returns the DAC frequency of the given channel.

        Parameters:
          'dacChannel'     The target channel, either 1 or 0.
          'forceDirect'    Asks from MCU rather than trust client-side record
        """
        # Frequencies loaded in first time or if requested
        if self._dacFrequencies is None or forceDirect:
            with self._guardLock:
                if self._currentlyConnected:
                    if self._dacFrequencies is None:
                        self._dacFrequencies = dict()
                    for index in range(0, 2): # 0, 1
                        self._sendBytes(struct.pack('<cb', b'f', dacChannel))
                        response = self._readBytes(1)
                        if response == b'A':
                            self._dacFrequencies[index] = struct.unpack('<f', self._readBytes(4))
                        else:
                            if self._verbose:
                                print("Error: McuInterface_getDacFrequency, ackowledgement failure '%s'" % response.hex())
                            return None
                else:
                    if self._verbose:
                        print("Error: McuInterface_getDacFrequency, unit disconnected")
                    return None
        # Returns from prior history
        return self._dacFrequencies[dacChannel]

    def setDacFrequency(self, dacChannel, dacFrequency):
        """
        Description:
        Sets the waveform frequency of the given DAC dac channel

        Parameters:
        'dacChannel' The target channel, either 1 or 0.

        Returns:
        True if succesful, false otherwise.

        Note:
        Updated DAC channel frequency will not take effect until
        the beginEvents() and pauseEvents() commands are called.
        """
        with self._guardLock:
            if self._currentlyConnected:
                self._sendBytes(struct.pack('<cbf', b'F', dacChannel, dacFrequency))
                response = self._readBytes(1)
                if response == b'A':
                    if self._dacFrequencies is None: # No history exists
                        self.getDacFrequency(0) # Forces loading of history from MCU
                    self._dacFrequencies[dacChannel] = dacFrequency
                    return True
                elif response == b'F':
                    if self._verbose:
                        print("Error, McuInterface_setDacFrequency, bad arguments")
                else:
                    if self._verbose:
                        print("Error: McuInterface_setDacFrequency, ackowledgement failure '%s'" % response.hex())
            else:
                if self._verbose:
                    print("Error: McuInterface_getDacFrequency, unit disconnected")
        return False

    def getDacMagnitude(self, dacChannel, forceDirect = False):
        """
        Description:
          Returns the magnitude of the DAC waveform in volts.

        Parameters:
          'dacChannel'  The target channel, either 1 or 0.
          'forceDirect' True to request values from the MCU, false uses client-side history.
        Magnitudes loaded in first time or if requested
        """
        if self._dacMagnitudes is None or forceDirect:
            with self._guardLock:
                if self._currentlyConnected:
                    if self._dacMagnitudes is None:
                        self._dacMagnitudes = dict()
                    for index in range(0, 2):
                        self._sendBytes(struct.pack('<cb', b'm', dacChannel))
                        response = self._readBytes(1)
                        if response == b'A':
                            self._dacMagnitudes[index] = struct.unpack('<f', self._readBytes(4))
                        else:
                            if self._verbose:
                                print("Error: McuInterface_getDacMagnitude, acknowledgement failure '%s'" % response.hex())
                            return None
                else:
                    if self._verbose:
                        print("Error: McuInterface_getDacMagnitude, unit disconnected")
                    return None
        return self._dacMagnitudes[dacChannel]

    def setDacMagnitude(self, dacChannel, dacMagnitude):
        """
        Description:
          Sets the magnitude of the DAC waveform in volts
          of the given channel.

        Parameters:
          'dacChannel'   The target channel, either 1 or 0.
          'dacMagnitude' The magnitude of the dac channel in volts.
                         Typically 3.3v max and centered at vref/2 (check MCU settings).

        Note:
          Updated DAC magnitude will not take effect until
          the beginEvents() and pauseEvents() commands are called.
        """
        with self._guardLock:
            if self._currentlyConnected:
                self._sendBytes(struct.pack('<cbf', b'M', dacChannel, dacMagnitude))
                response = self._readBytes(1)
                if response == b'A':
                    if self._dacMagnitudes is None: # No history exists
                        self.getDacMagnitude(0) # Forces loading of history from MCU
                    self._dacMagnitudes[dacChannel] = dacMagnitude
                    return True
                elif response == b'F':
                    if self._verbose:
                        print("Error, McuInterface_setDacMagnitude, bad arguments")
                else:
                    if self._verbose:
                        print("Error: McuInterface_setDacMagnitude, acknowledgement failure '%s'" % response.hex())
            else:
                if self._verbose:
                    print("Error: McuInterface_setDacMagnitude, unit disconnected")
        return False

    def getDacWaveform(self, dacChannel, forceDirect = False):
        """
        Description:
          Returns the waveform assigned to the given dac channel.

        Parameters:
          'dacChannel'  The target channel, either 1 or 0.
          'forceDirect' Load waveforms from the MCU rather than trust client-side history
          0 = Sine, 1 = Sawtooth, 3 = Triangle.
        """
        # Magnitudes loaded in first time or if requested
        if self._dacWaveforms is None or forceDirect:
            with self._guardLock:
                if self._currentlyConnected:
                    if self._dacWaveforms is None: # No prior history
                        self._dacWaveforms = dict() # Creates history structure
                    for index in range(0, 2): # 0, 1
                        self._sendBytes(struct.pack('<cb', b'w', dacChannel))
                        response = self._readBytes(1)
                        if response == b'A':
                            self._dacWaveforms[index] = struct.unpack('<b', self._readBytes(1))
                        else:
                            if self._verbose:
                                print("Error: McuInterface_getDacWaveform, ackowledgement failure '%s'" % response.hex())
                            return None
                else:
                    if self._verbose:
                        print("Error: McuInterface_getDacWaveform, unit disconnected")
                    return None
        return self._dacWaveforms[dacChannel]

    def setDacWaveform(self, dacChannel, dacWaveform):
        """
        Description:
          Sets the waveform associated with the given dac channel.

        Parameters:
          'dacChannel'  The target channel, either 1 or 0.
          'dacWaveform' The waveform associated with the channel,
                        0 = Sine, 1 = Sawtooth, 3 = Triangle.

        Note:
          Updated DAC waveform settings will not take effect until
          the beginEvents() and pauseEvents() commands are called.
        """
        with self._guardLock:
            if self._currentlyConnected:
                self._sendBytes(struct.pack('<cbb', b'W', dacChannel, dacWaveform))
                response = self._readBytes(1)
                if response == b'A':
                    if self._dacWaveforms is None: # No client-side history
                        self.getDacWaveform(0) # Creates client-side history structure
                    self._dacWaveforms[dacChannel] = dacWaveform
                    return True
                elif response == b'F':
                    if self._verbose:
                        print("Error: McuInterface_setDacWaveform, bad arguments")
                else:
                    if self._verbose:
                        print("Error: McuInterface_setDacWaveform, ackowledgement failure '%s'" % response.hex())
            else:
                if self._verbose:
                    print("Error: McuInterface_setDacWaveform, unit disconnected")
        return False

    def getAdcFrequency(self, forceDirect = False):
        """
        Description:
          Returns the frequency in hertz that the ADC samples at.

        Parameters:
          'forceDirect' If true, reloads record from MCU rather than use client-side history
        """
        if self._adcFrequency is None or forceDirect:
            with self._guardLock:
                if self._currentlyConnected:
                    self._sendBytes(struct.pack('<c', b's'))
                    response = self._readBytes(1)
                    if response == b'A':
                        self._adcFrequency = struct.unpack('<f', self._readBytes(4))
                    else:
                        if self._verbose:
                            print("Error: McuInterface_getAdcFrequency, acknowledgement failure '%s'" % response.hex())
                        return None
                else:
                    if self._verbose:
                        print("Error: McuInterface_getAdcFrequency, unit disconnected")
                    return None
        return self._adcFrequency

    def setAdcFrequency(self, adcFrequency):
        """
        Description:
        Sets the frequency of ADC sampling in hertz.

        Parameters:
        'adcFrequency' (float) The sampling frequency in hertz.

        Note:
        Updated ADC frequency will not take effect until
        the beginEvents() and pauseEvents() commands are called.
        """
        with self._guardLock:
            if self._currentlyConnected:
                self._sendBytes(struct.pack('<cf', b'S', adcFrequency))
                response = self._readBytes(1)
                if response == b'A':
                    self._adcFrequency = adcFrequency
                    return True
                elif response == b'F':
                    if self._verbose:
                        print("Error: McuInterface_setAdcFrequency, bad arguments")
                else:
                    if self._verbose:
                        print("Error: McuInterface_setAdcFrequency, acknowledgement failure  '%s'" % response.hex())
            else:
                if self._verbose:
                    print("Error: McuInterface_setAdcFrequency, unit disconnected")
        return False

    def getAdcAverages(self, forceDirect = False):
        """
        Description:
          Returns the number of averages per ADC result, none
          if the device is disconnected.

        Parameters:
          'forceDirect' If true, reloads record from MCU rather than use client-side history

        Returns:
          None if disconnected, integer number of averages per ADC result
          if connected.
        """
        if self._adcAverages is None or forceDirect:
            with self._guardLock:
                if self._currentlyConnected:
                    self._sendBytes(struct.pack('<c', b'u'))
                    response = self._readBytes(1)
                    if response == b'A':
                        self._adcAverages = struct.unpack('<b', self._readBytes(1))
                    else:
                        if self._verbose:
                            print("Error: McuInterface_getAdcAverages, ackowledgement failure '%s'" % response.hex())
                else:
                    if self._verbose:
                        print("Error: McuInterface_getAdcAverages, unit disconnected")
        return self._adcAverages


    def setAdcAverages(self, adcAverages):
        """
        Description:
          Sets the number of averaged samples per ADC result.

        Parameters:
          'adcAverages' The number of times to average per sample, must be 0, 4, 8, 16, or 32

        Returns:
          True if succesful, false otherwise.

        Note:
          Updated ADC frequency will not take effect until
          the beginEvents() and pauseEvents() commands are called.
        """
        with self._guardLock:
            if self._currentlyConnected:
                self._sendBytes(struct.pack('<cb', b'U', adcAverages))
                response = self._readBytes(1)
                if response == b'A':
                    self._adcAverages = adcAverages
                    return True
                elif response == b'F':
                    if self._verbose:
                        print("Error: McuInterface_setAdcAverages, bad arguments")
                else:
                    if self._verbose:
                        print("Error: McuInterface_setAdcAverages, ackowledgement failure '%s'" % response.hex())
            else:
                if self._verbose:
                    print("Error: McuInterface_setAdcAverages, unit disconnected")
        return False

    def getDataBuffer(self):
        """
        Description:
            Acquires a data buffer from the MCU.
        Returns:
            Returns an array of the form [dac 0 offset in uS, dac 1 offset in uS, byteValues]
        """
        with self._guardLock:
            if self._currentlyConnected:
                self._sendBytes(struct.pack('<c', b'A'))
                response = self._readBytes(1)
                if response == b'A':
                    currentNumber = struct.unpack('<I', self._readBytes(4))
                    if(currentNumber[0] - self._lastPacketID - 1 > 0):
                        print("Error, McuInterface_getDataBuffer, missed %d packets" % (currentNumber[0] - self._lastPacketID - 1))
                    self._lastPacketID = currentNumber[0]
                    # Result consists of three 32 bit integers and then an
                    # array of bytes.
                    aOffset  = (struct.unpack('<I', self._readBytes(4)))[0] # In milliseconds
                    bOffset  = (struct.unpack('<I', self._readBytes(4)))[0] # In milliseconds
                    duration = (struct.unpack('<I', self._readBytes(4)))[0]
                    byteList = self._readBytes(self._SERIAL_DATASTRUCT_BUFFERSIZE)
                    byteArray = numpy.frombuffer(byteList, numpy.uint8)
                    value = numpy.stack((numpy.linspace(bOffset, bOffset + duration, self._SERIAL_DATASTRUCT_BUFFERSIZE) / 1000000.0, numpy.linspace(aOffset, aOffset + duration, self._SERIAL_DATASTRUCT_BUFFERSIZE) / 1000000.0, byteArray), 1) # format is [data, aTimes, bTimes] as column vectors
                    return value
                #elif response == b'F':
                    #if self._verbose:
                        #print("Error: AWSEM_getDataBuffer, no buffer ready")
                    #return None
                else:
                    if self._verbose:
                        print("Error: McuInterface_getDataBuffer, ackowledgement failure '%s'" % response.hex())
                    return None
            else:
                if self._verbose:
                    print("Error: McuInterface_getDataBuffer, unit disconnected")
                return None
        return None

    def beginEvents(self):
        """Starts sampling and analog driving behavior.
        """
        with self._guardLock:
            if self._currentlyConnected:
                outMessage = struct.pack('<c', b'B')
                self._sendBytes(outMessage)
                response = self._readBytes(1)
                if response == b'A':
                    self._currentlyScanning = True
                    return True
                else:
                    if self._verbose:
                        print("Error, McuInterface_beginEvents, ackowledgement failure '%s'" % response.hex())
            else:
                if self._verbose:
                    print("Error, McuInterface_beginEvents, unit disconnected")
        return False

    def pauseEvents(self):
        """Ends sampling and analog driving behavior, also updates settings.
        """
        with self._guardLock:
            if self._currentlyConnected:
                outMessage = struct.pack('<c', b'H')
                self._sendBytes(outMessage)
                self._currentlyScanning = False
                response = self._readBytes(1)
                if response == b'A':
                    return True
                else:
                    if self._verbose:
                        print("Error, McuInterface_beginEvents, ackowledgement failure")
                    return False
            else:
                if self._verbose:
                    print("Error, McuInterface_pauseEvents, unit disconnected")
                return False
        return False

    #------------------- Private Members ---------------

    def _sendBytes(self, command):
        """Sends a serial command to the PiPion in the form of a byte array
        """
        self._serialPort.write(command)

    def _readBytes(self, numBytes):
        """Reads values from the PiPion
        """
        value = self._serialPort.read(numBytes)
        return value

    def _findPort(self):
        portList = list_ports.comports()
        if self._verbose:
            print("McuInterface, Searching for the PiPion:")
        for index in range(0, self._SERIAL_RECONNECTIONATTEMPTS):
            for currentPort in portList:
                try:
                    self._serialPort = serial.Serial(currentPort.device)
                    self._serialPort.close()
                    self._serialPort.open()
                    if self._verbose:
                        print("  -> Port: %s, %s, %s" % (currentPort.device, currentPort.name, currentPort.description))
                except:
                    continue
                self._serialPort.timeout = self._SERIAL_TIMEOUT
                if self.ping():
                    self._currentlyConnected = True
                    if self._verbose:
                        print('McuInterface, Connection established with the PiPion.')
                    return True
                else:
                    self._serialPort.close()
        if self._verbose:
            print('McuInterface, No serial ports found for the PiPion.')
        return False
