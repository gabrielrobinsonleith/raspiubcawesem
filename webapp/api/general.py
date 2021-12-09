import time

from loguru import logger
from flask import Blueprint, jsonify, make_response, request, send_from_directory

# from awesem.drivers.relays import State

from webapp import video_feed_handler, detector_amplifier_handler
from webapp.configs import config, save_config

bp = Blueprint("api_general", __name__)

def apply_slider_settings():
    """Applies slider settings to relevant hardware controls
    """
    logger.debug("Applying slider settings")

    magnify  = config["User.ScanSettings"].getfloat("Magnify")
    video_feed_handler.scan_control_handler.set_scan_amplitude(magnify)
    logger.debug(f"Magnify slider: {magnify} V")

    brightness = config["User.ScanSettings"].getfloat("Brightness")
    detector_amplifier_handler.set_output_gain(brightness)
    logger.debug(f"Brightness slider: {brightness} V")

    contrast = config["User.ScanSettings"].getfloat("Contrast")
    video_feed_handler.visualize.set_contrast(contrast)
    logger.debug(f"Contrast slider: {contrast} bits")

@bp.route("/electron_beam_on", methods=["POST"])
def electron_beam_on():
    logger.debug("Turning system on")

#     high_voltage_control_handler.switch_ultravolt_output_signal(State.ON)
#     high_voltage_control_handler.switch_enable_signal(State.ON)
#     high_voltage_control_handler.switch_ultravolt_power(State.ON)
#     high_voltage_control_handler.set_ultravolt_output_control_signal(
#         config["BeamControl"].getfloat("VoltageControlSignalVolts")
#     )
#     laser_control_handler.power(State.ON)
    config["General"]["IsPoweredOn"] = str(True)
    save_config()

    logger.info("All systems powered on")

    return jsonify(success=True)

@bp.route("/electron_beam_off", methods=["POST"])
def electron_beam_off():
    logger.debug("Turning system off")

    # Must set output control signal to 0V before turning it off with the relay
#     high_voltage_control_handler.set_ultravolt_output_control_signal(0)
    time.sleep(2)

#     high_voltage_control_handler.switch_ultravolt_output_signal(State.OFF)
#     high_voltage_control_handler.switch_enable_signal(State.OFF)
#     high_voltage_control_handler.switch_ultravolt_power(State.OFF)
#     laser_control_handler.power(State.OFF)

    video_feed_handler.stop()

    config["General"]["IsPoweredOn"] = str(False)
    save_config()

    logger.info("All systems powered off")

    return jsonify(success=True)

@bp.route("/electron_beam_align", methods=["POST"])
def electron_beam_align():
    apply_slider_settings()

    logger.info("Calibrating electron beam...")
    video_feed_handler.run_calibration()

    # Don't reply until calibration is complete
    while True:
        if not video_feed_handler.is_calibrating:
            break
        time.sleep(0.5)

    logger.info("Calibration complete")

    return jsonify(success=True)

@bp.route("/get_beam_control_output", methods=["GET"])
def get_beam_control_output():
     voltage = 1
     current = 1

    # Format as string to consistently show decimals
     return jsonify(voltage="%.2f"%voltage, current="%.2f"%current)

@bp.route("/start_stream", methods=["POST"])
def start_stream():
    apply_slider_settings()
    video_feed_handler.start()

    return jsonify(success=True)

@bp.route("/pause_stream", methods=["POST"])
def pause_stream():
    video_feed_handler.pause()
    return jsonify(success=True)

@bp.route("/save_scan", methods=["GET"])
def save_scan():
    image_directory, image_filename = video_feed_handler.save()
    return send_from_directory(image_directory, image_filename, as_attachment=True, mimetype='application/png')

@bp.route("/set_image_setting_magnify", methods=["POST"])
def set_image_setting_magnify():
    # Divide by 100 since slider value is 330 for 3.3V
    # Also invert the value since farthest right corresponds to 0V
    value = 3.3 - request.get_json()["value"] / 100
    logger.info(f"Set magnify to {value}")

    config["User.ScanSettings"]["Magnify"] = str(value)
    save_config()

    video_feed_handler.scan_control_handler.set_scan_amplitude(value)

    return jsonify(success=True)

@bp.route("/set_image_setting_brightness", methods=["POST"])
def set_image_setting_brightness():
    # Divide by 100 since slider value is 330 for 3.3V
    value = request.get_json()["value"] / 100
    logger.info(f"Set brightness to {value}")

    config["User.ScanSettings"]["Brightness"] = str(value)
    save_config()

    detector_amplifier_handler.set_output_gain(value)

    return jsonify(success=True)

@bp.route("/set_image_setting_contrast", methods=["POST"])
def set_image_setting_contrast():
    value = request.get_json()["value"]
    logger.info(f"Set contrast to {value}")

    config["User.ScanSettings"]["Contrast"] = str(value)
    save_config()

    video_feed_handler.visualize.set_contrast(value)

    return jsonify(success=True)

@bp.route("/set_scan_rate", methods=["POST"])
def set_scan_rate():
    key = request.get_json()["key"]

    fast_axis_hz = config[f"ScanningStage.{key}"].getfloat("FastAxisScanRateHz")
    config["ScanningStage"]["FastAxisScanRateHz"] = str(fast_axis_hz) #to be referenced globally
    save_config()

    resolution = config["User.ScanSettings"].getfloat("Resolution")
    sampling_frequency_hz = 2*(4*resolution)*fast_axis_hz
    slow_axis_hz = (2.0*fast_axis_hz) / (4*resolution)



    logger.info(f"Set scan rate to {fast_axis_hz} Hz and {slow_axis_hz} Hz")

    video_feed_handler.set_axis_frequency("stage", slow_axis_hz, fast_axis_hz, sampling_frequency_hz)

    return jsonify(success=True)
