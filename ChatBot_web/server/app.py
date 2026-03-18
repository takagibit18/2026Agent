import sys, os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify, Response, send_from_directory, stream_with_context
from chatbot.llm_connector import get_qwen_response
import asyncio
import time

app = Flask(__name__, static_folder='../client', static_url_path='/')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data['message']
    response_message = get_qwen_response(message)
    return jsonify({'response': response_message})

@app.route('/stream')
def stream():
    def generate():
        while True:
            yield f"data: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n\n"
            time.sleep(1)
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/sse')
async def sse():
    async def event_stream():
        while True:
            await asyncio.sleep(1)
            yield f"data: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n\n"
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True)