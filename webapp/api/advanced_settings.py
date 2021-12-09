from loguru import logger
from flask import Blueprint, jsonify, make_response, request, send_from_directory

from webapp.configs import config, save_config
from webapp import video_feed_handler

bp = Blueprint("api_settings", __name__)

@bp.route("/set_input_voltage_control_signal", methods=["POST"])
def set_input_voltage_control_signal():
    value = request.get_json()["value"]
    logger.info(f"Set voltage signal to {value}")

    config["BeamControl"]["VoltageControlSignalVolts"] = str(value)
    save_config()

    high_voltage_control_handler.set_ultravolt_output_control_signal(value)

    return jsonify(success=True)


# These two functions aren't being used
@bp.route("/set_stage_fast_axis_scan_rate", methods=["POST"])
def set_stage_fast_axis_scan_rate():
    value = request.get_json()["value"]
    logger.info(f"Set fast axis scan rate to {value}")

    config["ScanningStage"]["FastAxisScanRateHz"] = str(value)
    save_config()
    
    return jsonify(success=True)

@bp.route("/set_stage_slow_axis_scan_rate", methods=["POST"])
def set_stage_slow_axis_scan_rate():
    value = request.get_json()["value"]
    logger.info(f"Set slow axis scan rate to {value}")

    config["ScanningStage"]["SlowAxisScanRateHz"] = str(value)
    save_config()

    return jsonify(success=True)

# Calculates sampling and slow axis frequencies to correspond to 1000 by 1000 pixel buffers
@bp.route("/set_stage_custom_fast_axis_scan_rate", methods=["POST"])
def set_stage_custom_fast_axis_scan_rate():
    value = request.get_json()["value"]
    # Changed this 1000 to 4 times the current resolution
    resolution = config["User.ScanSettings"].getfloat("Resolution")
    sampling = 2*(4*resolution)*value
    slow = (2.0*value) / (4*resolution)
    logger.info("AAHHHAHA")
    logger.info(f"Set custom fast axis scan rate to {value} and slow to {slow} at {sampling} hz")

    config["ScanningStage.Custom"]["FastAxisScanRateHz"] = str(value)
    config["ScanningStage.Custom"]["SlowAxisScanRateHz"] = str(slow)
    config["ScanningStage.Custom"]["SamplingFrequencyHz"] = str(sampling)
    save_config()

    return jsonify(success=True)

# This function is no longer going to be used
@bp.route("/set_stage_custom_slow_axis_scan_rate", methods=["POST"])
def set_stage_custom_slow_axis_scan_rate():
    value = request.get_json()["value"]
    logger.info(f"Set custom slow axis scan rate to {value}")

    config["ScanningStage.Custom"]["SlowAxisScanRateHz"] = str(value)
    save_config()

    return jsonify(success=True)

@bp.route("/set_beam_fast_axis_scan_rate", methods=["POST"])
def set_beam_fast_axis_scan_rate():
    value = request.get_json()["value"]
    logger.info(f"Set fast axis scan rate to {value}")

    config["BeamAlignment"]["FastAxisScanRateHz"] = str(value)
    save_config()

    return jsonify(success=True)

@bp.route("/set_beam_slow_axis_scan_rate", methods=["POST"])
def set_beam_slow_axis_scan_rate():
    value = request.get_json()["value"]
    logger.info(f"Set slow axis scan rate to {value}")

    config["BeamAlignment"]["SlowAxisScanRateHz"] = str(value)
    save_config()

    return jsonify(success=True)

@bp.route("/set_resolution", methods=["POST"])
def set_resolution():
    value = request.get_json()["value"]
    logger.info(f"Set the image resolution to: {value}")

    config["User.ScanSettings"]["Resolution"] = str(value)
    save_config()

    fast_axis_hz = config["ScanningStage"].getfloat("FastAxisScanRateHz")
    sampling_frequency_hz = 2*(4*value)*fast_axis_hz
    slow_axis_hz = (2.0*fast_axis_hz) / (4*value)

    logger.info(f"Set scan rate to {fast_axis_hz} Hz and {slow_axis_hz} Hz")

    video_feed_handler.set_axis_frequency("stage", slow_axis_hz, fast_axis_hz, sampling_frequency_hz)


    return jsonify(success=True)

@bp.route("/set_detector_bias", methods=["POST"])
def set_detector_bias():
    value = request.get_json()["value"]
    logger.info(f"Set detector bias to {value}")

    config["Detector"]["BiasVolts"] = str(value)
    save_config()

    detector_amplifier_handler.set_detector_bias(value)

    return jsonify(success=True)

@bp.route("/set_brightness_map", methods=["POST"])
def set_brightness_map():
    value = request.get_json()["value"]
    logger.info(f"Set brightness map to {value}")

    config["BeamAlignment"]["MapEnabled"] = str(value)
    save_config()

    return jsonify(success=True)
