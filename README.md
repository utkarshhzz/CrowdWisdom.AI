# Automated AI Debt Collection Agent

A sophisticated, multi-agent AI system designed to intelligently orchestrate and automate debt collection procedures using conversational AI. The project utilizes a custom LLM orchestration loop to verify suitable calling windows (respecting public holidays via web scraping and timezone validation), fetches active records from Airtable, and executes real-time conversational voice calls via ElevenLabs.

## Key Features
- **Conversational Voice AI**: Integrates the ElevenLabs Conversational AI Agent for dynamic, human-like phone calls and negotiations.
- **Smart Orchestration (Hermes Manager)**: Custom autonomous loop leveraging OpenRouter (LLM) to decide precisely *when* and *whether* to initiate calls based on real-world constraints.
- **Compliance & Scheduling Skill**: Automatically scrapes US public holidays (via Apify) and verifies working hours to strictly adhere to debt collection communication compliance.
- **Continuous Learning Loop**: Implements localized feedback storage and call history tracking (JSON), dynamically injecting past interaction context into subsequent LLM decisions to improve success rates.
- **Dynamic Database Integration**: Bidirectional Airtable integration fetches pending debtors and updates their status context post-call in real time.
- **Vercel Ready**: Contains serverless API deployment configurations (\api/index.py\ and \vercel.json\) to host a sandbox UI and webhooks.

##  System Architecture
1. **Airtable Client**: Acts as the CMS/Database, queuing debtors with a \Call-Status\ of \pending\.
2. **Apify Scraper**: Caches US holiday calendars to prevent non-compliant outbound calls.
3. **Hermes Orchestrator Agent**: Analyzes debtor info, decides on action feasibility via custom tool-calling, and manages the decision loop.
4. **Skills/Tools**:
   - \scheduling_skill.py\: Evaluates local time and holidays.
   - \voice_trigger_skill.py\: Establishes the ElevenLabs WebSocket stream to initiate the active voice agent dialogue.
5. **Feedback Loop**: Records call outcomes in \call_history.json\ for context tracking.

##  How to Run Locally

### Prerequisites
You need an active Python 3.9+ environment and API keys for the following services:
- **Airtable** (API Key, Base ID, Table Name)
- **Apify** (API Token for scraping)
- **ElevenLabs** (API Key, Agent ID)
- **OpenRouter** (API Key for LLM orchestration)

### 1. Installation
Clone the repository and install the dependencies:
\\\bash
git clone <your-github-repo-url>
cd <repository-directory>
python -m venv venv
venv\Scripts\Activate.ps1 # On Windows
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
\\\

### 2. Environment Configuration
Create a \.env\ file in the root directory:
\\\env
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
AIRTABLE_TABLE_NAME=Debtors
APIFY_API_TOKEN=your_apify_api_token
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_AGENT_ID=your_elevenlabs_agent_id
OPENROUTER_API_KEY=your_openrouter_api_key
\\\

### 3. Database Setup (Airtable)
- Create a table matching your \AIRTABLE_TABLE_NAME\ (e.g., \Debtors\).
- Ensure it contains a column named \Call-Status\.
- Add test rows with \Call-Status\ set to \pending\.

### 4. Running the Application
**Backend Orchestration Loop:**
\\\bash
python main.py
\\\
**Web Evaluation Sandbox:**
\\\bash
python api/index.py
\\\
Then navigate to \http://127.0.0.1:5000\ in your local browser.

## Deployment (Vercel)
This project is configured for Vercel Serverless deployment. 
1. Ensure the Vercel CLI is installed.
2. Run \vercel\ to link the project and deploy the frontend sandbox / API endpoints.
3. Configure environment variables in the Vercel Dashboard matching your \.env\ file.
4. (Optional) Connect your ElevenLabs Agent to external channels like Twilio or WhatsApp through the ElevenLabs dashboard.
