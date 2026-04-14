from flask import Flask, request, jsonify, render_template_string
import os
import sys

# Tell the app it is running on Vercel ONLY if it actually is on Vercel. 
# We remove the hardcoded os.environ["VERCEL"] = "1" so that local testing uses real speakers.
if not os.environ.get("VERCEL"):
    print("RUNNING IN LOCAL MODE: ElevenLabs Voice Streams are Active!")

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

from agent.manager import DebtCollectionManager

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Voice Orchestrator | Hermes</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; }
        body, html {
            margin: 0; padding: 0; height: 100%;
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #020617 100%);
            color: #ffffff;
            display: flex; justify-content: center; align-items: center;
            overflow-x: hidden;
        }
        
        .blob {
            position: absolute; filter: blur(80px); z-index: -1;
            animation: move 10s infinite alternate ease-in-out;
        }
        .blob-1 { top: 10%; left: 20%; width: 400px; height: 400px; background: rgba(56, 189, 248, 0.4); border-radius: 50%; }
        .blob-2 { bottom: 10%; right: 10%; width: 500px; height: 500px; background: rgba(236, 72, 153, 0.3); border-radius: 50%; animation-delay: 2s; }
        
        @keyframes move {
            from { transform: translateY(0) scale(1); }
            to { transform: translateY(50px) scale(1.1); }
        }

        .glass-container {
            position: relative; z-index: 10;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            padding: 40px; width: 100%; max-width: 600px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        
        h2 { margin-top: 0; font-weight: 700; font-size: 28px; text-transform: uppercase; letter-spacing: 2px; text-align: center; }
        p.subtitle { color: #94a3b8; text-align: center; margin-bottom: 30px; font-size: 14px; }
        
        .form-group { display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 20px; }
        .input-box { flex: 1 1 calc(50% - 15px); display: flex; flex-direction: column; }
        label { font-size: 12px; color: #bae6fd; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
        
        input, select {
            background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff; padding: 12px; border-radius: 8px; font-size: 14px; outline: none; transition: 0.3s;
        }
        input:focus, select:focus { border-color: #38bdf8; background: rgba(255, 255, 255, 0.15); }
        option { background: #0f172a; color: #fff; }
        
        button {
            width: 100%; padding: 15px; font-size: 16px; font-weight: 700;
            background: linear-gradient(90deg, #38bdf8, #ec4899); color: #fff;
            border: none; border-radius: 8px; cursor: pointer;
            box-shadow: 0 4px 15px rgba(56, 189, 248, 0.4); transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(56, 189, 248, 0.6); }
        button:disabled { background: #555; cursor: not-allowed; box-shadow: none; transform: none; }
        
        .loader-container { display: none; text-align: center; margin-top: 20px; }
        .spinner {
            width: 40px; height: 40px; border: 4px solid rgba(255, 255, 255, 0.1);
            border-top-color: #38bdf8; border-radius: 50%;
            animation: spin 1s infinite linear; margin: 0 auto;
        }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .status-text { margin-top: 10px; font-size: 14px; color: #94a3b8; font-style: italic; }

        .result-box {
            display: none; margin-top: 25px; padding: 20px; border-radius: 12px;
            animation: fadeIn 0.5s ease; text-align: center; font-weight: 600; font-size: 18px;
        }
        .success { background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); color: #4ade80; }
        .skip { background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); color: #fbbf24; }
        
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .badge {
            position: absolute; top: -15px; left: 50%; transform: translateX(-50%);
            background: linear-gradient(90deg, #f43f5e, #e11d48);
            padding: 5px 15px; border-radius: 20px; font-size: 11px; font-weight: bold; letter-spacing: 1px;
            box-shadow: 0 4px 10px rgba(244, 63, 94, 0.4);
        }
    </style>
</head>
<body>

    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>

    <div class="glass-container">
        <div class="badge">EVALUATION SANDBOX</div>
        <h2>Hermes Orchestrator</h2>
        <p class="subtitle">Simulate the dynamic AI tooling to decide if a debt collection call should be placed based on constraints.</p>

        <form id="evalForm">
            <div class="form-group">
                <div class="input-box">
                    <label>Debtor Name</label>
                    <input type="text" name="name" value="Evaluator Smith" required>
                </div>
                <div class="input-box">
                    <label>Amount Owed ($)</label>
                    <input type="number" name="debt_amount" value="1500" required>
                </div>
            </div>

            <div class="form-group" style="flex-direction: column;">
                <label>Environment Timezone (Simulated Logic Test)</label>
                <select name="timezone" style="width: 100%;">
                    <option value="Asia/Kolkata">Asia/Kolkata (Force LLM Skill Defense = False)</option>
                    <option value="America/New_York" selected>US Eastern (Attempt Logic Pass)</option>
                    <option value="Europe/London">UK Standard Time</option>
                </select>
            </div>

            <button type="submit" id="submitBtn">Initialize AI Decision Engine</button>
        </form>

        <div class="loader-container" id="loader">
            <div class="spinner"></div>
            <div class="status-text" id="statusText">Connecting OpenRouter Toolkit...</div>
        </div>

        <div id="result" class="result-box"></div>
    </div>

    <script>
        const statusMessages = [
            "Initializing Hermes Multimodal LLM...",
            "Loading Database History...",
            "Invoking Scheduling Skill Validation...",
            "Checking Apify Public Holiday Caches...",
            "Awaiting LLM Call Decision..."
        ];

        document.getElementById("evalForm").addEventListener("submit", async(e) => {
            e.preventDefault();
            
            const btn = document.getElementById("submitBtn");
            const loader = document.getElementById("loader");
            const resultDiv = document.getElementById("result");
            const statusText = document.getElementById("statusText");
            
            btn.disabled = true;
            resultDiv.style.display = "none";
            loader.style.display = "block";
            
            let msgIndex = 0;
            const interval = setInterval(() => {
                statusText.innerText = statusMessages[msgIndex % statusMessages.length];
                msgIndex++;
            }, 1000);

            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch("/api/trigger", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });
                
                clearInterval(interval);
                const json = await response.json();
                
                loader.style.display = "none";
                resultDiv.style.display = "block";

                if (json.status === "success") {
                    if(json.decision === "CALLED") {
                        resultDiv.className = "result-box success";
                        resultDiv.innerHTML = `✅ AI Action: <b>CALLED.</b><br><br><span style="font-size:12px; font-weight:400;">The AI Agent safely bypassed logic gates, evaluated the cache history, and successfully simulated the Voice API socket!</span>`;
                    } else {
                        resultDiv.className = "result-box skip";
                        resultDiv.innerHTML = `⚠️ AI Action: <b>SKIPPED.</b><br><br><span style="font-size:12px; font-weight:400;">The AI Scheduling Tool successfully blocked the action because it realized it was illegal to call (either out of hours, weekend, or holiday)!</span>`;
                    }
                } else {
                    resultDiv.className = "result-box skip";
                    resultDiv.innerHTML = "❌ Error: " + json.message;
                }

            } catch(err) {
                clearInterval(interval);
                loader.style.display = "none";
                resultDiv.style.display = "block";
                resultDiv.className = "result-box skip";
                resultDiv.innerHTML = "❌ Network Exception inside Vercel.";
            }

            btn.disabled = false;
        });
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/trigger", methods=["POST"])
def trigger():
    data = request.json
    try:
        manager = DebtCollectionManager()
        decision = manager.process_debtor(data)
        return jsonify({"status": "success", "decision": decision})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
