# Automated Debt Collection System AI

This project is an AI-powered debt collection system using a multi-agent orchestration approach. It automatically scrapes public holidays, verifies appropriate calling times, orchestrates decisions using the OpenRouter API (LLM), and executes conversational voice calls via ElevenLabs.

## Step 1: Configuration
Ensure you have a `.env` file in the root directory with the following variables:
```env
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
AIRTABLE_TABLE_NAME=Debtors
APIFY_API_TOKEN=your_apify_api_token
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_AGENT_ID=your_elevenlabs_agent_id
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Step 2: Database Setup (Airtable)
- Create a table named `Debtors` (or match your `.env` setting).
- Make sure to have a column named `Call-Status`.
- Add test data (rows) to let the script pick up pending debtors (e.g. `Call-Status` = `pending`).

## Step 3: Run the Application
Start the orchestration loop by running:
```bash
python main.py
```
Or start the gorgeous web evaluation Sandbox:
```bash
python api/index.py
```
Then visit `http://127.0.0.1:5000`

## Step 4: Submission Components
As requested for the final evaluation, here are the required components:
- **GitHub Repository**: (Insert your GitHub link here)
- **APIFY tokens used**: `apify/cheerio-scraper` (Free tier)
- **11labs agent bot link**: (Insert your ElevenLabs Shareable Agent Link here)

---
- **Airtable Client:** Fetches data and updates statuses.
- **Apify Scraper:** Pre-caches US holidays to ensure no calls occur on holidays.
- **Hermes Manager Agent:** Custom AI orchestration loop using OpenAI's tool-calling format over OpenRouter. Evaluates conditions and acts.
- **Skills:**
  - `scheduling_skill.py`: Checks if the current time and day constitute a good time to call.
  - `voice_trigger_skill.py`: Physically initiates the ElevenLabs Conversation websocket stream.
- **Learning Loop:** Stores a local JSON history tracking call success/failures for immediate feedback context injections in future LLM decisions.

## WhatsApp Integration (Step 8)
WhatsApp integration in ElevenLabs is done through their dashboard, requiring no extra Python code here. See the documentation below for steps to connect.
