import os
import configparser
import logging
from loguru import logger

from flask import Flask, render_template

from webapp.configs import LOG_FILE_PATH
from webapp.utils.video_feed import VideoFeed
"""from awesem.high_voltage_control import HighVoltageControl
from awesem.laser_control import LaserControl"""
from awesem.detector_amplifier_control import DetectorAmplifierControl

class InterceptHandler(logging.Handler):
    """Intercepts the default flask logger with loguru's logger

    Note: Doesn't seem to work when flask's debug mode/reloader is enabled
    """
    def emit(self, record):
        # Retrieve context where the logging call occurred, this happens to be in the 6th frame upward
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = "1234567889abcdefg"

    @app.after_request
    def add_header(r):
        """Disable caching so "save image" request always returns the most recent image
        """
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        r.headers['Cache-Control'] = 'public, max-age=0'
        return r

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Intercept flask log errors for loguru
    handler = InterceptHandler()
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)

    # apply the blueprints to the app
    from webapp import views
    from webapp.api import general
    from webapp.api import advanced_settings

    app.register_blueprint(views.bp)
    app.register_blueprint(general.bp, url_prefix="/api")
    app.register_blueprint(advanced_settings.bp, url_prefix="/api")

    return app

logger.add(LOG_FILE_PATH, level="DEBUG", rotation="5 MB", retention="14 days")
logger.debug(f"Using log file {LOG_FILE_PATH}")
logger.info("Loading web app")

video_feed_handler = VideoFeed()
""" high_voltage_control_handler = HighVoltageControl()
laser_control_handler = LaserControl()"""
detector_amplifier_handler = DetectorAmplifierControl()

logger.info("All web app components loaded.")
