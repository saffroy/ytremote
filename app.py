import json
import logging
from flask import Flask, render_template, request
from simple_websocket import Server, ConnectionClosed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

view_clients = set()
control_clients = set()

@app.route('/')
def index():
    """Serves the landing page."""
    return render_template('index.html')

@app.route('/view')
def view():
    """Serves the view page."""
    return render_template('view.html')

@app.route('/control')
def control():
    """Serves the control page."""
    return render_template('control.html')

@app.route('/ws')
def ws_socket():
    """Handles WebSocket connections."""
    client_address = request.environ.get('REMOTE_ADDR')
    logging.info(f"/ws request from {client_address}, headers: {request.headers}")

    ws = None
    client_type = None
    try:
        ws = Server(request.environ)
        reg_message = ws.receive()
        data = json.loads(reg_message)
        if data.get('type') == 'register':
            client_type = data.get('client')
            if client_type == 'viewer':
                view_clients.add(ws)
                logging.info(f"Viewer connected from {client_address}")
                # Keep connection open to listen for commands
                while True:
                    ws.receive()  # This will block until a message is received or the connection is closed
            elif client_type == 'controller':
                control_clients.add(ws)
                logging.info(f"Controller connected from {client_address}")
                # Listen for commands from the controller and broadcast them
                while True:
                    message = ws.receive()
                    # Broadcast to all viewers
                    disconnected_viewers = set()
                    for client in view_clients:
                        try:
                            client.send(message)
                        except ConnectionClosed:
                            disconnected_viewers.add(client)
                    # Clean up disconnected viewers
                    view_clients.difference_update(disconnected_viewers)

    except ConnectionClosed:
        logging.info(f"Client from {client_address} disconnected.")
    except Exception as e:
        logging.error(f"Error with client {client_address}: {e}")
    finally:
        # Cleanup on disconnect
        if client_type == 'viewer' and ws in view_clients:
            view_clients.remove(ws)
            logging.info(f"Viewer from {client_address} removed.")
        elif client_type == 'controller' and ws in control_clients:
            control_clients.remove(ws)
            logging.info(f"Controller from {client_address} removed.")
    return ''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
