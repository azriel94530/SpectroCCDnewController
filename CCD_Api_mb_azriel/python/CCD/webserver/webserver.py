import flask

import os
os.sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import main 
import sys
from contextlib import contextmanager
import StringIO

SIMULATE = False

HIST_FILE = '/home/freddy/.ccdshellhistory'
FITS_LOCATION = '/home/freddy/test.fits'
#HIST_FILE = '/n/home00/wheeler.883/.ccdshellhist'
#FITS_LOCATION = '/n/des/wheeler.883/test.fits'

#delete the lockfile if it exits
try:
    os.remove('/tmp/lockfile')
    print('lockfile removed')
except OSError:
    pass


app = flask.Flask(__name__)

shell = main.CCDShell(simulate=SIMULATE)
shell.preloop()

@contextmanager
def redirect_stdout():
    old = os.dup(1)
    os.close(1)
    os.open(HIST_FILE, os.O_APPEND | os.O_CREAT | os.O_WRONLY)
    try:
        yield
    finally:
        sys.stdout.flush()
        os.close(1)
        os.dup(old)
        os.close(old)

hist = [""]

def rendered_page():
    with open(HIST_FILE, 'r') as f:
        output = ''.join(f.readlines())
        if output == '':
            output = None
        return flask.render_template('main.html', output=output, hist=hist)

@app.route('/ccd', methods=['GET', 'POST'])
def hw():
    if flask.request.method == 'GET':
        return rendered_page()
    else:
        if flask.request.form['action'] == "Clear Output":
            open(HIST_FILE, 'w').close()
            return flask.redirect('/ccd')
        elif flask.request.form['action'] == "Download FITS":
            flask.send_file(FITS_LOCATION)#, as_attachment=True)
            return rendered_page()
        else:
            command = flask.request.form['command']
            if command == '':
                return flask.redirect('/ccd')
            hist[:1] = ["", str(command)]
            with redirect_stdout():
                print('<span id="input">%s</span>' % command)
                shell.onecmd(command)
                print('<hr/>')
            return rendered_page()

@app.route("/download", methods=['GET'])
def download():
    return flask.send_file(FITS_LOCATION, as_attachment=True)
    #return rendered_page()


app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)



