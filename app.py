from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

# Route to query serverlist and return it as JSON
@app.route('/servers', methods=['GET'])
def get_servers():
    response = requests.get("https://api.nordvpn.com/v1/servers?limit=0")
    servers = response.json()

    seen_countries = set()
    server_list = []

    for server in servers:
        if (server.get("status") == "online" and
                server["locations"] and
                server["locations"][0].get("country") and
                server["locations"][0]["country"].get("code")):

            country_code = server["locations"][0]["country"]["code"]

            if country_code not in seen_countries:
                seen_countries.add(country_code)

                # Remove the hashtag und everything after from the name
                server_name = server["name"].split('#')[0].strip()

                server_list.append({"name": server_name, "code": country_code})

    return jsonify(server_list)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status', methods=['GET'])
def vpn_status():
    status_output = os.popen('nordvpn status').read()
    connected_server_code = None
    if "Status: Connected" in status_output:
        for line in status_output.splitlines():
            if "Hostname" in line:
                connected_server_code = line.split(":")[1].strip().split(".")[0]  # Extract code from hostname
                break
        return jsonify({"status": "Connected", "details": status_output, "server": connected_server_code})
    else:
        return jsonify({"status": "Disconnected", "details": status_output, "server": None})

@app.route('/connect', methods=['POST'])
def connect_vpn():
    server_code = request.form.get('server')
    result = os.popen(f"nordvpn connect {server_code}").read()

    if "The specified server does not exist" in result:
        return 'Fehler: Der angegebene Server existiert nicht.', 400
    elif "You are connected to" in result:
        return 'VPN verbunden!', 200
    else:
        return f'Fehler: {result}', 400

@app.route('/disconnect', methods=['POST'])
def disconnect_vpn():
    result = os.popen(f"nordvpn disconnect").read()

    if "You are not connected" in result:
        return 'Es bestand keine VPN Verbindung.', 200
    elif "You are disconnected" in result:
        return 'VPN getrennt!', 200
    else:
        return f'Fehler: {result}', 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)