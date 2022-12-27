"""
Analysis
=========

Author: Erick Blankenberg
Date: 9/11/2018

Description:
------------

  This class has methods for an image analysis and distortion
  correction pipeline.
  The general approach is as follows:
      1). Assign rough location by using driving waveform w/ phase shift
          a). Build "Modern Art" image by stacking fast waveforms from
              travel along both directions of fast and slow axis
          b). The resulting image has four quadrants, upper/lower is back/fourth
              of vertical slow axis, left/right is back/fourth of fast axis. However,
              there is probably a phase offset. Identify this phase offset by checking
              for mirror symmetry vertically and horizonally. The program assumes that this
              phase offset will be less than half of the full period and so will
              check close to the middle and edges of the image from a).
          c). Return phase offsets for use with a periodic mapping function.
      2). If imaging a grid, find a distortion correction map using splines.
          a). Retrieve an image generated from step 1, one that is already
              roughly aligned.
          b). Segment this image and identify the lines between the grid squares,
              sort these lines into two perpendicular camps
          c). Find the average distance between parralel lines, build a r
TODO:
  -> Could implement basic LUT's better: https://shocksolution.com/2009/01/09/optimizing-python-code-for-fast-math/
                                         https://shocksolution.com/2008/12/11/a-lookup-table-for-fast-python-math/
  -> Profile if/else versus trig triangle and mods
"""

import numpy as np

# ------------------- Image Processing Methods --------------

#
def preformCalibration():
    """
    Acquires a full pane of imaging data for the given parameters
    and builds a calibrated mapping file. Assumes that the target under
    the microscope is a grid.
    """

    print("Not Implemented")
    """
    baseImage           = acquireModernArt()
    lutCorrectedData    = retrievePhases(baseImage)
    imageDistortionMaps = retrieveRefinement(lutCorrectedData)
    """
#
# Description:
#   Finds the phase offsets associated with the given base "modern art"
#   image. Values are percentage of period of function of each axis.
#
#
#def retrievePhases(fastPeriod, slowPeriod, sampleData):

#
# Description:
#   Finds distortion maps for each of four iamges (rising falling vertical,
#   rising falling horizontal) seperated and given initial values using data
#   from the retrievePhases method.
#

# ------------------- Image Mapping Functions --------------

def cos(inputTime, amplitude, frequency, phase, baseOffset = None):
    """
    Description
        Returns the value of a cose function for the given parameters,
        migrated from WaveGen.

    Parameters:
        inputTime The time to evaluate in seconds
        amplitude  Amplitude of wave
        frequency Frequency of the sine in hz
        phase     Phase of the sine wave as a percentage of 2pi
        baseOffset Shift upwards applied to all points. By default set to amplitude (so that base is 0)
    """
    if inputTime is None: # Filtering can send "None" as input data occasionally
        return None
    if baseOffset is None:
        baseOffset = amplitude
    return amplitude * np.cos((inputTime * frequency - phase + 0.5) * 2.0 * np.pi) + baseOffset

def triangle(inputTime, amplitude, frequency, phase, baseOffset = None):
    """
    Description
      Returns the value of a triangle function for the given parameters,
      migrated from WaveGen. Ranges from [0, 1.0].

    Parameters:
      inputTime The time to evaluate in seconds
      amplitude  Amplitude of wave
      frequency Frequency of the triangle wave in hz
      phase     Phase delay of the function as a fraction of the full period.
      baseOffset Shift upwards applied to all point, by default shifted up by none (so that base is 0)
    """
    if inputTime is None: # Filtering can send "None" as input data occasionally
        return None
    if baseOffset is None:
        baseOffset = amplitude
    return ((2.0 * amplitude) / np.pi) * (np.arcsin(np.sin(((inputTime * frequency) - phase - 0.25) * 2.0 * np.pi))) + baseOffset

#
#
def sawTooth(inputTime, amplitude, frequency, phase, baseOffset = None):
    """
    Description
      Returns the value of a sawTooth function for the given parameters,
      migrated from WaveGen. Note that the triangular wave is offset so that it is centered
      at zero.

    Parameters:
      'inputTime'  The time to evaluate in seconds
      'amplitude'  Amplitude of wave
      'frequency'  Frequency of the sawTooth wave in hz
      'phase'      Phase delay of the function as a fraction of the full period.
      'baseOffset' Shift upwards applied to all points, by default shifted up by amplitude (so that base is 0)
    """
    if inputTime is None: # Filtering can send "None" as input data occasionally
        return None
    if baseOffset is None:
        baseOffset = amplitude
    return (2 * amplitude * np.mod((inputTime - phase / frequency), 1.0/frequency) * frequency) + baseOffset - amplitude
