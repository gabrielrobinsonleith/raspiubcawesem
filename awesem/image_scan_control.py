import time
import numpy as np
from serial import Serial
from enum import Enum
from aenum import Constant

from loguru import logger

from awesem import is_machine_raspberry_pi
from awesem.drivers.digital_potentiometers import DigitalPotentiometers

class Commands(Constant):
    """Serial commands used to communicate with the Teensy
    """
    START_SCAN = b"r"
    RUN_CALIBRATION = b"c"
    STOP_SCAN = b"k"

class ImageScanControl(object):
    """Controls the input image scan parameters and reads the image scan output
    """
    if is_machine_raspberry_pi():
        DATA_DEVICE_NAME = "/dev/ttyS0"
    else:
        DATA_DEVICE_NAME = "/dev/ttyUSB0"

    DATA_BAUDRATE = 2e6
    DATA_TIMEOUT_SEC = 0.5

    CONTROL_DEVICE_NAME = "/dev/ttyACM0"
    CONTROL_BAUDRATE = 115200

    def __init__(self):
        try:
            self._serial_data = Serial(self.DATA_DEVICE_NAME, self.DATA_BAUDRATE, timeout=self.DATA_TIMEOUT_SEC)
            logger.debug(f"Connected to {self.DATA_DEVICE_NAME}")
        except:
            self._serial_data = None
            logger.exception(f"Could not connect to {self.DATA_DEVICE_NAME}. Is the UART pin connected?")
        try:
            self._serial_control = Serial(self.CONTROL_DEVICE_NAME, self.CONTROL_BAUDRATE)
            logger.debug(f"Connected to {self.CONTROL_DEVICE_NAME}")
        except:
            self._serial_control = None
            logger.exception(f"Could not connect to {self.CONTROL_DEVICE_NAME}. Is the USB connected?")

        self._digital_pots = DigitalPotentiometers()

        self._slow_axis_frequency_hz = None
        self._fast_axis_frequency_hz = None
        self._sampling_frequency_hz = None

        self._expected_bytes_per_row = None

        # Keep track of frequencies since one command is used to set all 4 channels
        self._beam_slow_axis_freq_hz = 0
        self._beam_fast_axis_freq_hz = 0
        self._stage_slow_axis_freq_hz = 0
        self._stage_fast_axis_freq_hz = 0
        self._sampling_frequency_hz = 0

    def _are_params_set(self) -> bool:
        """Check if parameters are set by the user. These are required to calculate things
        like image resolution and the expected bytes per full image scan.
        """
        is_valid = True

        if not self._fast_axis_frequency_hz:
            logger.error("Please set the fast axis frequency")
            is_valid = False
        if not self._slow_axis_frequency_hz:
            logger.error("Please set the slow axis frequency")
            is_valid = False
        if not self._sampling_frequency_hz:
            logger.error("Please set the sampling frequency")
            is_valid = False

        return is_valid

    @property
    def expected_bytes(self) -> int:
        """Returns the expected bytes per full scan. Depends on slow axis frequency
        and scan rate.
        """
        if not self._are_params_set():
            logger.error("Could not calculated expected bytes with missing information.")
            return None

        b = (1/self._slow_axis_frequency_hz) * self._sampling_frequency_hz

        return int(b)

    @property
    def expected_bytes_per_row(self) -> int:
        """Returns the expected bytes per row
        """
        return self._expected_bytes_per_row

    @property
    def data_buffer_resolution(self) -> int:
        """Returns the current image resolution. Depends on the slow and fast axis
        frequencies and scan rate.
        """
        if not self._are_params_set():
            logger.error("Could not calculated image resolution with missing information.")
            return None

        y = (1/(self._fast_axis_frequency_hz*2)) / (1/self._sampling_frequency_hz)
        x = self.expected_bytes / y

        return (int(x), int(y))

    @property
    def data_buffer_resolution_effective(self) -> int:
        """Returns the effective data buffer resolution.

        This is different than data_buffer_resolution since this returns the dimensions of
        one frame of data. The other returns two frames (where the second frame is
        mirrored at the halfway point) due to the use of a triangle wave (instead of
        something like a sawtooth wave).
        """
        return (self.data_buffer_resolution[0], int(self.data_buffer_resolution[1]/2))

    def set_axis_frequency(self, component:str, slow_axis:float, fast_axis:float, sampling_frequency_hz:float):
        if component == "stage":
            self._stage_fast_axis_freq_hz = fast_axis
            self._stage_slow_axis_freq_hz = slow_axis
            # Only change the sampling_frequency if we are sending a stage command
            self._sampling_frequency_hz = sampling_frequency_hz
        elif component == "beam":
            self._beam_fast_axis_freq_hz = fast_axis
            self._beam_slow_axis_freq_hz = slow_axis
        else:
            logger.error(f"{component} not allowed. Please select 'beam' or 'stage'.")
            return None

        cmd = f"s {self._stage_fast_axis_freq_hz}, {self._stage_slow_axis_freq_hz}, {self._beam_fast_axis_freq_hz}, {self._beam_slow_axis_freq_hz}, {self._sampling_frequency_hz}"
        logger.debug(f"Sending command: '{cmd}'")

        if self._serial_control:
            self._serial_control.write(str.encode(cmd))
        else:
            logger.info(f"Mock: Axis frequency set")

        self._slow_axis_frequency_hz = slow_axis
        self._fast_axis_frequency_hz = fast_axis

        logger.info(f"Stage axis frequency set to {slow_axis} Hz and {fast_axis} Hz")

        # Wait for config to settle
        #time.sleep(1)

    def set_sampling_frequency(self, sampling_freq_hz:float):
        self._sampling_frequency_hz = sampling_freq_hz

        logger.info(f"Sampling frequency set to {sampling_freq_hz} Hz")

    def set_scan_amplitude(self, value:float):
        # Fast axis amplitude
        self._digital_pots.set_device1_amplitude(self._digital_pots.RDAC2, value)
        # Slow axis amplitude
        self._digital_pots.set_device1_amplitude(self._digital_pots.RDAC4, value)

        logger.info(f"Set fast and slow axis amplitudes to {value} V")

    def stop_scan(self):
        """Stops the image Scan
        """

        self._serial_control.write(Commands.STOP_SCAN)
        logger.debug("Stopped Teensy")


    def start_scan(self, calibration_mode=False):
        """Starts the image scan. Exits if required parameters are not set.
        """
        if not self._are_params_set():
            logger.error("Scan not started.")
            return None

        logger.trace("Requesting scan to start")

        if self._serial_control:
            if calibration_mode:
                self._serial_control.write(Commands.RUN_CALIBRATION)
                logger.debug("Started calibration")
            else:
                self._serial_control.write(Commands.START_SCAN)
                logger.debug("Started scan")
        else:
            logger.info("Mock: Starting scan")

        self._expected_bytes_per_row = self.data_buffer_resolution[0]
        bytes_per_image_rounded = int(self.data_buffer_resolution[0] * self.data_buffer_resolution[1])

        logger.debug(f"Expected bytes per image (rounded): {bytes_per_image_rounded} bytes")
        logger.debug(f"Expected bytes per image (full): {self.expected_bytes} bytes")
        logger.debug(f"Resulting buffer resolution: {self.data_buffer_resolution} pixels")
        logger.debug(f"Bytes per row: {self._expected_bytes_per_row} bytes")

    def read_data(self) -> np.ndarray:
        """Read a row of data from serial. Requires calling this multiple times to get
        data for a full image scan.

        Returns:
            np.ndarray: Numpy array of fast axis length, casted from bytes to uint8
        """

        if self._serial_data:
            buf = self._serial_data.read(self._expected_bytes_per_row)
        else:
            # Generate random noise
            time.sleep(0.01)
            return np.random.randint(255, size=(self._expected_bytes_per_row))

        if len(buf) == 0:
            logger.warning(f"No bytes received.")
            return None
        else:
            if len(buf) != self._expected_bytes_per_row:
                logger.warning(f"Only received {len(buf)} bytes, but expected {self._expected_bytes_per_row} bytes")
            return np.frombuffer(buf, dtype=np.uint8)

if __name__ == "__main__":
    scan_control = ImageScanControl()

    # Frequency, in hertz
    xfreq = .1
    yfreq = 30
    sf = 20e3

    scan_control.set_axis_frequency("stage", xfreq, yfreq)
    scan_control.set_sampling_frequency(sf)

    while True:
        logger.info("Starting scan")
        scan_control.start_scan()
        total_bytes_read = 0
        start_time = time.time()

        while True:
            buf = scan_control.read_data()

            # Break if no more data is received
            if buf is None:
                logger.info(f"Bytes received: {total_bytes_read}")
                break
            else:
                total_bytes_read += len(buf)
                logger.trace(f"Received {len(buf)} bytes")

        elapsed_time = time.time() - start_time
        logger.info(f"Elapsed time: {elapsed_time:.2f} sec")

        if total_bytes_read == 0:
            logger.warning("No bytes received. Is the device connected?")
            break
