from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/restaurants')
def restaurants():
    return jsonify(["Pizza Hub", "Biryani House"])

@app.route('/health')
def health():
    return "OK"

app.run(host='0.0.0.0', port=3002)
