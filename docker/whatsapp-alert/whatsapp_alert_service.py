from flask import Flask, request, jsonify

app = Flask(__name__)

# store recipient globally
recipient_number = None

@app.route('/set_recipient', methods=['POST'])
def set_recipient():
    global recipient_number
    data = request.json
    number = data.get("number")
    if not number:
        return jsonify({"status": "error", "message": "No number provided"}), 400
    recipient_number = number
    return jsonify({"status": "success", "number": recipient_number})

@app.route('/test_alert', methods=['GET'])
def test_alert():
    if recipient_number:
        return jsonify({"status": "success", "message": f"Would send alert to {recipient_number}"})
    else:
        return jsonify({"status": "error", "message": "No recipient set"}), 400

if __name__ == "__main__":
    # host=0.0.0.0 makes it accessible from Docker
    app.run(host="0.0.0.0", port=5000)
