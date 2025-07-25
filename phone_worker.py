import os
import json
import requests
import threading
from flask import Flask, request, jsonify, render_template_string
from transformers import AutoTokenizer, AutoConfig, AutoModelForCausalLM
import torch

# Set Hugging Face cache to E drive
os.environ['HF_HOME'] = 'E:/huggingface_cache'

app = Flask(__name__)

# Global state
workers = {}  # {worker_id: {ip, port, layers, status}}
model_config = None
tokenizer = None
total_layers = 0

# Web UI Template
WEB_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>Phone Cluster LLM</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff; }
        .container { max-width: 800px; margin: 0 auto; }
        .section { background: #2a2a2a; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .worker { background: #3a3a3a; margin: 10px 0; padding: 10px; border-radius: 4px; }
        .chat-container { background: #2a2a2a; padding: 20px; border-radius: 8px; height: 300px; overflow-y: auto; }
        .input-container { margin: 20px 0; }
        input, button, select { padding: 10px; font-size: 16px; }
        input[type="text"] { width: 70%; background: #3a3a3a; color: #fff; border: 1px solid #555; }
        select { background: #3a3a3a; color: #fff; border: 1px solid #555; width: 300px; }
        button { background: #4a9eff; color: white; border: none; cursor: pointer; margin: 5px; }
        button:disabled { background: #666; cursor: not-allowed; }
        .status-online { color: #4ade80; }
        .status-offline { color: #f87171; }
        .status-loading { color: #fbbf24; }
        .model-status { background: #3a3a3a; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .flex { display: flex; gap: 10px; align-items: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Phone Cluster LLM</h1>
        
        <div class="section">
            <h3>Model Management</h3>
            <div class="model-status" id="modelStatus">
                No model loaded
            </div>
            <div class="flex">
                <select id="modelSelect">
                    <option value="distilgpt2" selected>DistilGPT2 (82M) - TINY</option>
                    <option value="sshleifer/tiny-gpt2">Tiny GPT2 (12M) - MICRO</option>
                    <option value="microsoft/DialoGPT-small">DialoGPT Small (117M)</option>
                    <option value="EleutherAI/gpt-neo-125M">GPT-Neo 125M</option>
                    <option value="gpt2">GPT2 (124M)</option>
                    <option value="microsoft/DialoGPT-medium">DialoGPT Medium (355M)</option>
                </select>
                <button onclick="loadModel()" id="loadBtn">Load Model</button>
            </div>
        </div>
        
        <div class="section">
            <h3>Connected Workers</h3>
            <div id="workers"></div>
        </div>
        
        <div class="input-container">
            <input type="text" id="userInput" placeholder="Ask something..." onkeypress="if(event.key==='Enter') sendMessage()" disabled>
            <button onclick="sendMessage()" id="sendBtn" disabled>Send</button>
        </div>
        
        <div class="chat-container" id="chat"></div>
    </div>

    <script>
        let modelLoaded = false;
        
        function updateWorkers() {
            fetch('/api/workers')
                .then(r => r.json())
                .then(data => {
                    const html = Object.entries(data.workers).map(([id, w]) => 
                        `<div class="worker">
                            <strong>${id}</strong> - ${w.ip}:${w.port} 
                            <span class="status-${w.status}">${w.status}</span>
                            <br>Layers: ${w.layers || 'None'} | Memory: ${w.memory_used || 'Unknown'}
                        </div>`
                    ).join('');
                    document.getElementById('workers').innerHTML = html;
                });
        }
        
        function loadModel() {
            const modelSelect = document.getElementById('modelSelect');
            const loadBtn = document.getElementById('loadBtn');
            const modelStatus = document.getElementById('modelStatus');
            
            const modelPath = modelSelect.value;
            loadBtn.disabled = true;
            loadBtn.textContent = 'Loading...';
            modelStatus.innerHTML = `<span class="status-loading">Loading ${modelPath}...</span>`;
            
            fetch('/load_model', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model_path: modelPath})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    modelLoaded = true;
                    modelStatus.innerHTML = `<span class="status-online">✅ ${data.model}</span><br>Layers: ${data.total_layers} | Workers: ${data.workers}`;
                    document.getElementById('userInput').disabled = false;
                    document.getElementById('sendBtn').disabled = false;
                } else {
                    modelStatus.innerHTML = `<span class="status-offline">❌ Error: ${data.error}</span>`;
                }
            })
            .catch(err => {
                modelStatus.innerHTML = `<span class="status-offline">❌ Connection error</span>`;
            })
            .finally(() => {
                loadBtn.disabled = false;
                loadBtn.textContent = 'Load Model';
            });
        }
        
        function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message || !modelLoaded) return;
            
            addMessage('You: ' + message);
            input.value = '';
            
            fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: message})
            })
            .then(r => r.json())
            .then(data => {
                addMessage('AI: ' + (data.response || data.error));
            });
        }
        
        function addMessage(msg) {
            const chat = document.getElementById('chat');
            chat.innerHTML += '<div>' + msg + '</div>';
            chat.scrollTop = chat.scrollHeight;
        }
        
        setInterval(updateWorkers, 2000);
        updateWorkers();
    </script>
</body>
</html>
"""

@app.route('/')
def web_ui():
    return render_template_string(WEB_UI)

@app.route('/register_worker', methods=['POST'])
def register_worker():
    """Register a new phone worker"""
    data = request.json
    worker_id = f"{data['ip']}:{data['port']}"
    
    workers[worker_id] = {
        "ip": data['ip'],
        "port": data['port'],
        "gpu_available": data.get('gpu_available', False),
        "memory_available": data.get('memory_available', 2.0),
        "status": "online",
        "layers": None,
        "memory_used": None
    }
    
    print(f"✅ Worker registered: {worker_id}")
    return jsonify({"success": True, "worker_id": worker_id})

@app.route('/api/workers', methods=['GET'])
def get_workers():
    """Get worker status"""
    # Update worker status
    for worker_id, worker in workers.items():
        try:
            response = requests.get(f"http://{worker['ip']}:{worker['port']}/status", timeout=2)
            if response.status_code == 200:
                status_data = response.json()
                worker['status'] = 'online'
                worker['layers'] = f"{status_data.get('layer_range', ['?', '?'])[0]}-{status_data.get('layer_range', ['?', '?'])[1]}" if status_data.get('layers_loaded') else None
                worker['memory_used'] = status_data.get('memory_used', 'Unknown')
            else:
                worker['status'] = 'offline'
        except:
            worker['status'] = 'offline'
    
    return jsonify({"workers": workers})

@app.route('/load_model', methods=['POST'])
def load_model():
    """Discover active workers and distribute model layers"""
    global model_config, tokenizer, total_layers
    
    data = request.json
    model_path = data.get('model_path', 'microsoft/DialoGPT-medium')
    
    try:
        print(f"🔄 Discovering workers and loading model: {model_path}")
        
        # Ping all workers to check status
        active_workers = []
        for worker_id, worker in workers.items():
            try:
                response = requests.get(f"http://{worker['ip']}:{worker['port']}/status", timeout=3)
                if response.status_code == 200:
                    worker['status'] = 'online'
                    active_workers.append((worker_id, worker))
                    print(f"✅ Worker {worker_id} online")
                else:
                    worker['status'] = 'offline'
            except:
                worker['status'] = 'offline'
                print(f"❌ Worker {worker_id} offline")
        
        if not active_workers:
            return jsonify({"error": "No active workers found"}), 400
        
        print(f"📱 Found {len(active_workers)} active workers")
        
        # Load tokenizer and config on master
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        model_config = AutoConfig.from_pretrained(model_path)
        total_layers = getattr(model_config, 'num_hidden_layers', getattr(model_config, 'n_layer', 24))
        
        # Distribute layers across active workers
        layers_per_worker = max(1, total_layers // len(active_workers))
        
        for i, (worker_id, worker) in enumerate(active_workers):
            start_layer = i * layers_per_worker
            end_layer = min((i + 1) * layers_per_worker - 1, total_layers - 1)
            
            # Handle last worker gets remaining layers
            if i == len(active_workers) - 1:
                end_layer = total_layers - 1
            
            # Set next worker in pipeline
            next_worker = active_workers[i + 1] if i < len(active_workers) - 1 else None
            
            load_data = {
                "model_path": model_path,
                "start_layer": start_layer,
                "end_layer": end_layer,
                "device_id": worker_id,
                "next_worker": f"{next_worker[1]['ip']}:{next_worker[1]['port']}" if next_worker else None,
                "pipeline_position": i,
                "total_workers": len(active_workers)
            }
            
            response = requests.post(f"http://{worker['ip']}:{worker['port']}/load_layers", json=load_data, timeout=30)
            if response.status_code == 200:
                print(f"✅ Worker {worker_id}: layers {start_layer}-{end_layer}")
                worker['layer_range'] = (start_layer, end_layer)
            else:
                print(f"❌ Worker {worker_id}: failed to load layers")
                return jsonify({"error": f"Worker {worker_id} failed to load"}), 500
        
        return jsonify({
            "success": True,
            "model": model_path,
            "total_layers": total_layers,
            "active_workers": len(active_workers),
            "pipeline_ready": True
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate text using pipeline parallelism"""
    if not tokenizer:
        return jsonify({"error": "Model not loaded"}), 400
    
    active_workers = [(k, v) for k, v in workers.items() if v['status'] == 'online']
    if not active_workers:
        return jsonify({"error": "No active workers"}), 400
    
    data = request.json
    prompt = data.get('prompt', '')
    max_tokens = data.get('max_tokens', 20)
    
    try:
        # Tokenize on master
        inputs = tokenizer(prompt, return_tensors="pt", padding=True)
        input_ids = inputs['input_ids']
        
        # Start pipeline with first worker
        first_worker = active_workers[0][1]
        pipeline_data = {
            "input_ids": input_ids.tolist(),
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "pipeline_id": f"gen_{hash(prompt)}_{len(active_workers)}"
        }
        
        print(f"🚀 Starting pipeline generation with {len(active_workers)} workers")
        response = requests.post(
            f"http://{first_worker['ip']}:{first_worker['port']}/pipeline_generate",
            json=pipeline_data,
            timeout=60
        )
        
        if response.status_code != 200:
            return jsonify({"error": "Pipeline generation failed"}), 500
        
        result = response.json()
        output_ids = result['output_ids']
        if isinstance(output_ids[0], list):
            output_ids = output_ids[0]  # Flatten [[...]] to [...]
        generated_text = tokenizer.decode(output_ids, skip_special_tokens=True)
        print(f"🔍 Full decoded: '{generated_text}'")
        print(f"🔍 Prompt: '{prompt}'")
        
        # Only strip if prompt is actually at start
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
        else:
            generated_text = generated_text.strip()
            
        print(f"🔍 Final response: '{generated_text}'")
        
        return jsonify({
            "response": generated_text,
            "workers_used": len(active_workers),
            "tokens_generated": result.get('tokens_generated', 0),
            "pipeline_time": result.get('generation_time', 0)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🖥️  Master Coordinator starting on http://localhost:5000")
    print("📱 Workers should register at /register_worker")
    app.run(host="0.0.0.0", port=5000, debug=True)
