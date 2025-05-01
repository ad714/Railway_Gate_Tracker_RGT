import os
import json
import logging
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from pprint import pformat
import concurrent.futures
from NTES_scraper import fetch_live_train_data

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('railway_gate.log'),
        logging.StreamHandler()
    ]
)

STATIONS_JSON_PATH = r"H:\RGTApp\RGT\backend\kerala_railway_stations.json"

try:
    with open(STATIONS_JSON_PATH, 'r', encoding='utf-8') as f:
        all_stations = json.load(f)
    logging.info(f"Loaded {len(all_stations)} stations")
except Exception as e:
    logging.error(f"Failed to load station data: {str(e)}")
    exit(1)

route_sequences = {}
for station in all_stations:
    routes = station['route'] if isinstance(station['route'], list) else [station['route']]
    for route in routes:
        if route not in route_sequences:
            route_sequences[route] = []
        route_sequences[route].append(station)

junctions = {
    "TVC": {"name": "Thiruvananthapuram Central", "code": "TVC", "lat": 8.5241391, "lon": 76.9366376},
    "QLN": {"name": "Kollam Jn", "code": "QLN", "lat": 8.8932118, "lon": 76.6141396},
    "KYJ": {"name": "Kayamkulam Jn", "code": "KYJ", "lat": 9.1748422, "lon": 76.5013352},
    "ERS": {"name": "Ernakulam Jn", "code": "ERS", "lat": 9.9816358, "lon": 76.2998842},
    "NCJ": {"name": "Nagercoil Jn", "code": "NCJ", "lat": 8.1744, "lon": 77.4332},
    "SCT": {"name": "Sengottai", "code": "SCT", "lat": 8.9755, "lon": 77.2498}
}

route_junctions = {
    "Trivandrum to Kollam": {"J1": junctions["NCJ"], "J2": junctions["QLN"]},
    "Kollam to Kayamkulam": {"J1": junctions["QLN"], "J2": junctions["KYJ"]},
    "Kayamkulam - Ernakulam via Alappuzha": {"J1": junctions["KYJ"], "J2": junctions["ERS"]},
    "Kayamkulam via Kottayam to Ernakulam": {"J1": junctions["KYJ"], "J2": junctions["ERS"]},
    "Kollam - Aryankavu": {"J1": junctions["QLN"], "J2": junctions["SCT"]}
}

def haversine(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def detect_route_near_junction(gate_lat, gate_lon, route_coordinates):
    min_dist = float('inf')
    closest_coord = None
    for coord in route_coordinates:
        dist = haversine(gate_lat, gate_lon, coord['latitude'], coord['longitude'])
        if dist < min_dist:
            min_dist = dist
            closest_coord = coord

    closest_station = min(all_stations,
                         key=lambda s: haversine(closest_coord['latitude'], closest_coord['longitude'], s['lat'], s['lon']))

    routes = closest_station['route'] if isinstance(closest_station['route'], list) else [closest_station['route']]
    return routes[0] if routes else None

def find_nearest_station_and_adjacents(gate_lat, gate_lon, route):
    if route not in route_sequences:
        return None, None, None

    stations = route_sequences[route]
    closest_idx = min(range(len(stations)),
                     key=lambda i: haversine(gate_lat, gate_lon, stations[i]['lat'], stations[i]['lon']))

    N = stations[closest_idx]
    O1 = stations[closest_idx - 1] if closest_idx > 0 else None
    O2 = stations[closest_idx + 1] if closest_idx < len(stations) - 1 else None

    return N, O1, O2

def find_controlling_junctions(route):
    if route not in route_junctions:
        app.logger.warning(f"Route '{route}' not found in route_junctions mapping")
        return None, None
    junction_data = route_junctions[route]
    return junction_data["J1"], junction_data["J2"]

def format_station(station):
    if not station:
        return None
    name = station.get('station_name') or station.get('name')
    code = station.get('station_code') or station.get('code')
    lat = station.get('lat')
    lon = station.get('lon')
    return {
        'name': name,
        'code': code,
        'position': {'latitude': lat, 'longitude': lon}
    }

@app.route('/railway_data', methods=['POST'])
def process_gates():
    try:
        data = request.get_json()
        app.logger.info(f"New request from {request.remote_addr}")
        app.logger.debug(f"Raw request data:\n{pformat(data, indent=2)}")

        gates = data.get('gates', [])
        route_coordinates = data.get('routeCoordinates', [])
        selected_gate_id = data.get('selectedGateId') # Extract selectedGateId

        if not isinstance(gates, list) or not isinstance(route_coordinates, list):
            app.logger.error("Invalid data format")
            return jsonify({"error": "Expected 'gates' and 'routeCoordinates' as arrays"}), 400

        app.logger.info(f"Processing {len(gates)} gates with {len(route_coordinates)} route coordinates. Selected Gate ID: {selected_gate_id}")

        # Prepare the gate data with all required information
        gate_data_for_scraping = []
        for gate in gates:
            gate_lat = gate.get('crossingCenter', {}).get('latitude', gate['latitude'])
            gate_lon = gate.get('crossingCenter', {}).get('longitude', gate['longitude'])

            route = detect_route_near_junction(gate_lat, gate_lon, route_coordinates)
            N, O1, O2 = find_nearest_station_and_adjacents(gate_lat, gate_lon, route)
            J1, J2 = find_controlling_junctions(route)

            gate_info = {
                'gate_id': gate['gateNumber'],
                'position': {'latitude': gate_lat, 'longitude': gate_lon},
                'route': route,
                'nearest_station': format_station(N),
                'adjacent_stations': {'before': format_station(O1), 'after': format_station(O2)},
                'junctions': {'before': format_station(J1), 'after': format_station(J2)}
            }
            gate_data_for_scraping.append(gate_info)

        app.logger.info("Fetching live train data for all gates...")
        # Execute scraping *once* for all gates
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                all_live_trains_data = loop.run_in_executor(
                    pool,
                    lambda: asyncio.run(fetch_live_train_data({"gates": gate_data_for_scraping, "selected_gate_id": selected_gate_id}))
                )
                all_live_trains_data = loop.run_until_complete(all_live_trains_data) # This will have been processed.
        finally:
            loop.close()

        # Combine the scraped data with the original gate data
        results = []
        for gate_info, live_trains in zip(gate_data_for_scraping, all_live_trains_data):
            gate_info["live_trains"] = live_trains["live_trains"]
            gate_info["gate_status"] = live_trains["gate_status"]
            results.append(gate_info)

        app.logger.debug(f"Final response:\n{pformat({'gates': results}, indent=2)}")
        return jsonify({"gates": results}), 200

    except Exception as e:
        app.logger.error(f"Error processing gates: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)