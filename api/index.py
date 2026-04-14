from flask import Flask, request, jsonify, render_template_string
import os
import sys

# Connect to our root folder for imports
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
    <title>AI Debt Collector Evaluator Sandbox</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 2rem; max-width: 600px; margin: auto; background-color: #f9f9f9; }
        .card { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        input, select { padding: 10px; width: 100%; box-sizing: border-box; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px;}
        button { background-color: #0070f3; color: white; border: none; padding: 12px; width: 100%; border-radius: 4px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #0051a8; }
        #result { margin-top: 20px; padding: 15px; border-radius: 4px; display: none; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="margin-top:0;">🤖 AI Debt Collector Sandbox</h2>
        <p style="color: #666; font-size: 14px;">Simulate an Airtable record pass to the AI Manager. Watch it verify the schedule and conditionally trigger the ElevenLabs Voice Bot.</p>
        
        <form id="evalForm">
            <label>Name</label>
            <input type="text" name="name" value="Test User Evaluator" required>
            
            <label>Company</label>
            <input type="text" name="company_name" value="Evaluation Inc" required>
            
            <label>Amount Owed ($)</label>
            <input type="number" name="debt_amount" value="500" required>
            
            <label>Due Date</label>
            <input type="date" name="due_date" value="2026-03-01" required>

            <label>Simulate Timezone</label>
            <select name="timezone">
                <!-- If you want to force the bot to call, pick a timezone where it is currently between 9AM and 6PM on a weekday -->
                <option value="America/New_York">US Eastern (America/New_York)</option>
                <option value="Asia/Kolkata" selected>India (Asia/Kolkata)</option>
                <option value="Europe/London">UK (Europe/London)</option>
                <option value="America/Los_Angeles">US Pacific (America/Los_Angeles)</option>
            </select>

            <button type="submit" id="submitBtn">Run Hermes Engine Evaluation</button>
        </form>

        <div id="result"></div>
    </div>

    <script>
        document.getElementById('evalForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const btn = document.getElementById('submitBtn');
            const resultDiv = document.getElementById('result');
            
            btn.innerHTML = "Processing (Analyzing Time, Querying Model)... Please Wait.";
            btn.disabled = true;
            resultDiv.style.display = 'block';
            resultDiv.className = '';
            resultDiv.innerHTML = "Calling the Python API... (Check your VS Code terminal for internal logging)";
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());

            try {
                const response = await fetch('/api/trigger', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const json = await response.json();
                
                if(json.status === "success") {
                    resultDiv.className = 'success';
                    resultDiv.innerHTML = `<b>AI Decision:</b> ${json.decision} <br><br> <small><i>If CALLED was returned, the ElevenLabs speaker stream should have activated!</i></small>`;
                } else {
                    resultDiv.className = 'error';
                    resultDiv.innerHTML = `<b>Error:</b> ${json.message}`;
                }

            } catch(err) {
                resultDiv.className = 'error';
                resultDiv.innerHTML = "<b>Network Error</b>: Failed to contact the backend.";
            }

            btn.innerHTML = "Run Hermes Engine Evaluation";
            btn.disabled = false;
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/trigger', methods=['POST'])
def trigger():
    """Vercel Serverless Route Handler"""
    data = request.json
    try:
        manager = DebtCollectionManager()
        # Returns either 'CALLED' or 'SKIPPED'
        decision = manager.process_debtor(data)
        return jsonify({"status": "success", "decision": decision})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Local Dev Mode
    print("starting Flask Server at http://127.0.0.net:5000")
    app.run(debug=True, port=5000)
