import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# --- Central Logging Configuration ---
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# --- Import your completed agent logic ---
from src.agent_logic import TradeAgent

# --- Application Setup ---
load_dotenv()
log.info("Loaded environment variables from .env file.")

app = FastAPI(
    title="Conversational Trade Agent",
    description="An AI agent that emulates a trader's personality based on their trade history.",
)

# Allow all origins for easy frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Agent Instance ---
agent: TradeAgent = None

@app.on_event("startup")
def startup_event():
    """Load data and initialize the full TradeAgent on app startup."""
    global agent
    log.info("--- Application Startup: Initializing Trade Agent ---")
    try:
        agent = TradeAgent(trades_filepath="src\\data\\trades.json")
        log.info("--- Agent initialized successfully. Application is ready. ---")
    except Exception as e:
        log.fatal(f"FATAL: Could not initialize TradeAgent during startup: {e}", exc_info=True)
        agent = None

# --- API Endpoints ---
class ChatQuery(BaseModel):
    query: str

@app.post("/chat", tags=["Conversational Agent"])
async def chat_with_agent(request: ChatQuery):
    """
    The main conversational endpoint. Takes a user query and returns the agent's response.
    """
    log.info(f"--- [/chat] New Request Received: '{request.query}' ---")

    # Check if the agent was initialized successfully on startup
    if not agent:
        log.error("Service is not ready. The TradeAgent is not available.")
        raise HTTPException(status_code=503, detail="Service Unavailable: The agent is not running.")
    
    # Tcall the agent's generate_response method
    log.info("Handing off query to agent for response generation...")
    response_text = agent.generate_response(request.query)
    log.info("Response generated. Sending back to user.")
    
    return {"user_query": request.query, "agent_response": response_text}

@app.get("/persona", tags=["Persona"])
def get_trader_persona():
    """Returns the JSON object of the agent's calculated persona."""
    log.info("Request received for /persona endpoint.")
    
    if not agent or not agent.persona:
        raise HTTPException(status_code=404, detail="Persona not found or agent not initialized.")
    return agent.persona