from flask import render_template, Blueprint, Response

from webapp.configs import config, LOG_FILE_PATH
from webapp import video_feed_handler

bp = Blueprint("views", __name__)

@bp.route('/')
@bp.route('/index')
def index():
    return render_template("index.html", config=config)

@bp.route("/internal_server_error")
def internal_server_error():
    return render_template('500.html')

@bp.route('/advanced.html')
def advanced():
    return render_template("advanced.html", config=config)

@bp.route('/logs.html')
def logs():
    with open(LOG_FILE_PATH, 'r') as f:
        data = f.readlines()

    # Only show the last hundred or so lines of the file
    logs = data[-250:]
    logs = "".join(logs)

    return render_template("logs.html", logfile=LOG_FILE_PATH, logs=logs)

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@bp.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(video_feed_handler),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
