import os
import io
import time
import threading
import numpy as np
from PIL import Image
from PIL.ImageOps import invert
from matplotlib.cm import get_cmap
from matplotlib.colors import Normalize

from loguru import logger

from awesem import is_machine_raspberry_pi
from awesem.image_scan_control import ImageScanControl
from webapp.utils.base_video_feed import BaseVideoFeed
from webapp.configs import config, WEBAPP_FILE_DIRECTORY

# Used to set log level
import sys
logger.remove()
logger.add(sys.stderr, level="DEBUG")

class VisualizeData(object):
    COLORMAP_MAX = 255
    COLORMAP_MIN = 0

    # Desired output image resolution (independent of data buffer resolution)

    IMAGE_RESOLUTION_X_PIXEL = 200
    IMAGE_RESOLUTION_Y_PIXEL = 200

    def __init__(self):
        self._colormap_max = self.COLORMAP_MAX
        self._colormap_min = self.COLORMAP_MIN

    def set_resolution(self):
        self.IMAGE_RESOLUTION_X_PIXEL = config["User.ScanSettings"].getfloat("Resolution")
        self.IMAGE_RESOLUTION_Y_PIXEL = config["User.ScanSettings"].getfloat("Resolution")

    def set_contrast(self, value:int):
        """Set the contrast of the displayed image. Can be updated live.

        Note: Currently only sets the max value to be normalized by the colormap. The min
        value also can be set, but this should provide enough to increase contrast of the
        pixels of interest.

        Args:
            value (int): 8-bit range from 0-255
        """
        self._colormap_max = self.COLORMAP_MAX - value
        logger.debug(f"Set contrast to {self._colormap_max} bits")

    def get_normalized(self, value:float)->float:
        """Returns a normalize value between the colormap's min/max values

        Args:
            value (float): Between 0.0-1.0

        Returns:
            float: Value between colormap's min/max corresponding to input
        """
        return (self._colormap_max - self._colormap_min)*value

    def generate_plot(self, img_array: np.ndarray, cmap='Greys', grid=False):
        """Plots a matrix to a heatmap

        Args:
            img_array (np.ndarray): 2D matrix of scanned frame
            cmap (str, optional): Colormap type. Defaults to 'Greys'.
            grid (bool, optional): Whether to show the grid. Defaults to False.

        Returns:
            bytes, Image: Byte object of image (for streaming) and figure handle (for saving)
        """
        logger.trace('----')

        start_time = time.time()
        buf = io.BytesIO()
        color_map = get_cmap(cmap)
        norm = Normalize(vmin=self._colormap_min, vmax=self._colormap_max)
        logger.trace(time.time() - start_time)

        start_time = time.time()
        # L mode indiciates the array values represent luminance, which creates a grayscale image
        img = Image.fromarray(img_array.astype('uint8'), 'L')
        img = invert(img)

        # Convert the grayscale image to the desired colormap. Requires casting back and forth
        # between PIL image and numpy array, but only takes ~0.015s on Raspberry Pi 4 (so
        # performance is still good)
        colored_img = color_map(norm(np.array(img)))
        img = Image.fromarray((colored_img[:, :, :3] * 255).astype(np.uint8))


        self.IMAGE_RESOLUTION_X_PIXEL = int(config["User.ScanSettings"].getfloat("Resolution"))
        self.IMAGE_RESOLUTION_Y_PIXEL = int(config["User.ScanSettings"].getfloat("Resolution"))


        # Stretch/squish the data buffer to the desired output image resolution
        img = img.resize((self.IMAGE_RESOLUTION_X_PIXEL, self.IMAGE_RESOLUTION_Y_PIXEL))

        logger.trace(time.time() - start_time)

        start_time = time.time()
        img.save(buf, format="png")
        logger.trace(time.time() - start_time)

        buf.seek(0)
        return buf.read(), img

class VideoFeed(BaseVideoFeed):
    """A video feed implementation to serve a continually updating plotted image
    """
    IMAGE_FILENAME = "awesem-scan.png"
    BLANK_STARTUP_IMAGE_VALUE = 0.75   # show a grayish color (scale from 0-1.0, inverted)

    def __init__(self):
        self._show_startup_image = True
        self._is_paused = True
        self._figure = None
        self._run_calibration = False
        self._show_calibration = config["BeamAlignment"].getboolean("MapEnabled")
        self._ignore_data = False

        self.visualize = VisualizeData()

        self.scan_control_handler = ImageScanControl()

        self.scan_control_handler.set_sampling_frequency(
            config["General"].getfloat("SamplingFrequencyHz")
        )

        self.set_axis_frequency(
            "stage",
            config["ScanningStage.Normal"].getfloat("SlowAxisScanRateHz"),
            config["ScanningStage.Normal"].getfloat("FastAxisScanRateHz"),
            config["ScanningStage.Normal"].getfloat("SamplingFrequencyHz")
        )

        super().__init__()

        data_thread = threading.Thread(target=self._thread_read_data)
        data_thread.daemon = True
        data_thread.start()

    def start(self):
        """Allows the frames to update
        """
        self._show_startup_image = False
        self._is_paused = False

    def pause(self):
        """Stops the frames from updating
        """
        self._is_paused = True


    def stop(self):
        """Resets the frame buffer and shows the startup image
        """
        self._show_startup_image = True
        self._is_paused = True

    def save(self):
        """Saves the last frame to an image file

        Returns:
            str: File directory and filename of saved image
        """
        filepath = os.path.join(WEBAPP_FILE_DIRECTORY, self.IMAGE_FILENAME)

        self._figure.save(filepath)
        logger.info(f"Saved to {filepath}")

        return WEBAPP_FILE_DIRECTORY, self.IMAGE_FILENAME

    def run_calibration(self):
        logger.debug("Starting calibration")

        self.set_axis_frequency(
            "beam",
            config["BeamAlignment"].getfloat("SlowAxisScanRateHz"),
            config["BeamAlignment"].getfloat("FastAxisScanRateHz"),
            0.0 #no need to change the sampling frequency if we're just running the beam alignment
        )

        self._show_startup_image = False

        self._show_calibration = config["BeamAlignment"].getboolean("MapEnabled")
        self._run_calibration = True
        self._is_paused = False

    @property
    def is_calibrating(self):
        return self._run_calibration

    def stop_calibration(self):
        logger.debug("Stopping calibration")
        self._run_calibration = False
        self._is_paused = True

    def set_axis_frequency(self, component:str, slow_axis_hz:float, fast_axis_hz:float, sampling_frequency_hz:float):
        """Set mechanical stage scanning frequency and initialize data array based on
        the given parameters.
        """

        # This goes into image_scan_control.py and sends all info to the pi
        self.scan_control_handler.set_axis_frequency(component, slow_axis_hz, fast_axis_hz, sampling_frequency_hz)

        logger.info(f"Initializing with data buffer resolution {self.scan_control_handler.data_buffer_resolution_effective}")

        self.data = np.full(
            self.scan_control_handler.data_buffer_resolution_effective,
            self.visualize.get_normalized(self.BLANK_STARTUP_IMAGE_VALUE)
        )

    def _thread_read_data(self):
        """Main thread to populate the data matrix (ie. from UART)

        Populates the image data matrix from each serial read, where the number of bytes
        read correlates to the number of pixels per row in the scan. Row index is kept
        track here (ie. not the Teensy) since the Teensy only outputs ADC values (which
        would correlate with each element in the image data matrix)

        Once the image matrix has been populated, there still may be some data left in the
        buffer (but may not consist of a full row of data). In this case, data is still
        read but it's not added to the image matrix.
        """
        
        while True:
            if not self._is_paused:
                self._ignore_data = False
                self.scan_control_handler.start_scan(calibration_mode=self._run_calibration)

                total_bytes_read = 0
                start_time = time.time()

                index = 0
                scanning_forward = True


                while True:
                    if self._is_paused:
                        logger.info("Stopping scan control")
                        self.scan_control_handler.stop_scan()
                        break
                    buffer = self.scan_control_handler.read_data()
                    if buffer is None:
                        logger.debug(f"Breaking out of scan loop. Bytes received: {total_bytes_read}")
                        break

                    total_bytes_read += len(buffer)
                    logger.trace(f"Received {len(buffer)} bytes")

                    # Every even row is flipped since direction is reversed
                    # if index % 2 == 0:
                    #     buffer = np.flip(buffer)

                    # Data will be ignored if the image has been fully constructed. But we
                    # still need to read the data so the waveform completes fully
                    if not self._ignore_data:
                        if len(buffer) == self.scan_control_handler.data_buffer_resolution_effective[0]:
                            # Populate the image data with new row from data buffer
                            self.data[:,index] = buffer
                        else:
                            logger.warning(f"Received {len(buffer)}, but does not fill a row of size {self.scan_control_handler.data_buffer_resolution_effective[0]}")

                    # Switch directions halfway through buffer (since slow axis is triangle wave)
                    # Subtract 1 in case index is out of range due to integer casting truncation
                    if index >= (self.scan_control_handler.data_buffer_resolution_effective[1] - 1) and scanning_forward:
                        scanning_forward = False
                        logger.debug(f"Scan direction: reverse")

                    elif index <= 0 and not scanning_forward:
                        scanning_forward = True
                        self._ignore_data = True
                        logger.debug(f"End of scan reached. Ignoring subsequent data in buffer. Total bytes received: {total_bytes_read}")

                        # Break if webapp is being run locally (ie. no hardware plugged in),
                        # since the read_buffer command will never return None
                        if not is_machine_raspberry_pi():
                            break

                    if scanning_forward:
                        index += 1
                    else:
                        index -= 1

                if self._run_calibration:
                    if not self._show_calibration:
                        # Show blank when calibration is done, otherwise the calibration
                        # data buffer will be displayed
                        self.data[:,:] = self.visualize.get_normalized(self.BLANK_STARTUP_IMAGE_VALUE)   # show a grayish color

                    self.stop_calibration()

                elapsed_time = time.time() - start_time
                logger.info(f"Elapsed time for scan: {elapsed_time:.2f} sec")

            # Arbitrary delay
            time.sleep(0.02)

    def frames(self):
        """Main loop that creates an image plot from the data matrix
        """
        logger.debug("Starting frames")

        while True:
            if self._show_startup_image:
                self.data[:,:] = self.visualize.get_normalized(self.BLANK_STARTUP_IMAGE_VALUE)

                image_buffer, self._figure = self.visualize.generate_plot(self.data, cmap='Greys', grid=True)
                yield image_buffer

                # Add a small sleep to reduce burden on CPU when paused
                time.sleep(0.25)

            else:
                # Show live data. No need to sleep since frames should be displayed as
                # quickly as possible
                if self._run_calibration:
                    if self._show_calibration:
                        # Optional: Change color map for calibration (ie. to 'viridis')
                        image_buffer, self._figure = self.visualize.generate_plot(self.data, cmap="Greys")
                    else:
                        pass
                else:
                    image_buffer, self._figure = self.visualize.generate_plot(self.data)
                yield image_buffer
                
                if self._is_paused:
                    time.sleep(0.25)
