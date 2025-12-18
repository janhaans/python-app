from flask import Flask
from datetime import datetime
import socket

app = Flask(__name__)

@app.route('/api/v1/details', methods=['GET'])
def details():
    return {
        'hostname': socket.gethostname(),
        'time': datetime.now().isoformat(),
        'message': 'hello'
    }

@app.route('/api/v1/healthz', methods=['GET'])
def healthz():
    return {'status': 'up'}

if __name__ == '__main__':
    app.run(debug=True)