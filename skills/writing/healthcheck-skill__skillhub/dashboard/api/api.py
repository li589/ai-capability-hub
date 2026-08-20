#!/usr/bin/env python3
import sys
import json
import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)

# 启用CORS
CORS(app, resources={r'/*'})

# 路由定义
@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        return jsonify({'status': 'running', 'version': '4.0.0'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    try:
        return jsonify(json.load(open(f'{API_DIR}/metrics.json')), 200)
    except FileNotFoundError:
        return jsonify({'error': 'Metrics not found', 'code': 404})

@app.route('/api/anomalies', methods=['GET'])
def get_anomalies():
    try:
        return jsonify(json.load(open(f'{API_DIR}/anomalies.json')), 200)
    except FileNotFoundError:
        return jsonify({'error': 'No anomalies found', 'code': 404})

@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        return jsonify(json.load(open(f'{API_DIR}/events.json'))), 200)
    except FileNotFoundError:
        return jsonify({'error': 'No events found', 'code': 404})

@app.route('/api/system', methods=['GET'])
def get_system_info():
    try:
        return jsonify(json.load(open(f'{API_DIR}/system.json')), 200)
    except FileNotFoundError:
        return jsonify({'error': 'System info not found', 'code': '404})

@app.route('/api/cve', methods=['GET'])
def get_cve_status():
    try:
        return jsonify(json.load(open(f'{API_DIR}/cve.json'))), 200)
    except FileNotFoundError:
        return jsonify({'error': 'CVE status not found', 'code': 404})

@app.route('/api/alert', methods=['POST'])
def create_alert():
    try:
        data = flask.request.get_json()
        # 保存告警
        alerts = json.load(open(f'{API_DIR}/alerts.json'))
        alerts.append(data)
        json.dump(alerts, open(f'{API_DIR}/alerts.json'), indent=2)
        return jsonify({'success': true, 'id': len(alerts)}), 201
    except Exception as e:
        return jsonify({'success': false, 'error': str(e)}), 500)

if __name__ == '__main__':
    port = 8888
    host = '0.0.0.0'
    app.run(host, port)
