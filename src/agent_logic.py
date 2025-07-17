import os
import json
import logging
import google.generativeai as genai
from typing import List, Dict, Any
from pandas_query_engine import PandasQueryEngine, model as query_engine_model
from pandas_aggregation_engine import PandasAggregationEngine
from persona_logic import analyze_trader_persona_with_pandas
import pandas as pd

log = logging.getLogger(__name__)

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        log.warning("GOOGLE_API_KEY not found. Agent will be unable to generate responses.")
        model = None
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        log.info("Gemini API configured successfully.")
except Exception as e:
    log.error(f"Failed to configure Gemini API: {e}", exc_info=True)
    model = None

def find_relevant_trades(query: str, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """ (R) RETRIEVAL Step """
    log.info("[RAG-Step 1/3] RETRIEVAL: Finding relevant trades.")
    relevant_trades = []
    query_lower = query.lower()
    
    log.debug(f"Searching for asset tickers in query: '{query_lower}'")
    for trade in trades:
        if trade['Asset'].lower() in query_lower:
            relevant_trades.append(trade)

    if not relevant_trades:
        log.debug("No asset tickers found. Searching for outcome keywords (loss/profit).")
        if "loss" in query_lower or "lost" in query_lower:
            relevant_trades = [t for t in trades if t["Outcome"] == "Loss"]
        elif "profit" in query_lower or "win" in query_lower or "won" in query_lower:
            relevant_trades = [t for t in trades if t["Outcome"] == "Profit"]

    final_trades = relevant_trades[-5:]
    log.info(f"RETRIEVAL complete. Found {len(final_trades)} relevant trade(s).")
    
    if final_trades:
        log.debug(f"Retrieved trades data:\n{json.dumps(final_trades, indent=2)}")
    
    return final_trades


def generate_response(query: str, persona: Dict[str, Any], trades: List[Dict[str, Any]]) -> str:
    """ Generates a response using the RAG pattern """
    if not model:
        log.error("Cannot generate response; Gemini model is not initialized.")
        return "The generative AI model is not configured. Please check the API key."

    # 1. RETRIEVAL
    relevant_trades = find_relevant_trades(query, trades)

    # 2. AUGMENTATION
    log.info("[RAG-Step 2/3] AUGMENTATION: Building detailed prompt for LLM.")
    prompt = f"""
    You are a conversational AI acting as a trader. Your personality is defined by the following profile:
    ---
    PERSONA:
    {json.dumps(persona, indent=2)}
    ---
    You are answering a question from a user. Ground your answer in your persona and, if relevant, use the specific trade examples provided below to form your narrative.
    Talk in the first person (use "I", "my", "me"). Be conversational and a bit formal, like a real trader would talk. Do not break character.
    ---
    RELEVANT TRADE EXAMPLES (for context):
    {json.dumps(relevant_trades, indent=2) if relevant_trades else "No specific trades seem relevant to this question, so answer based on your general persona."}
    ---
    USER'S QUESTION:
    "{query}"
    YOUR RESPONSE:
    """
    log.info("AUGMENTATION complete.")

    log.debug(f"--- Full Prompt Sent to Gemini ---\n{prompt}\n---------------------------------")

    # 3. GENERATION
    log.info("[RAG-Step 3/3] GENERATION: Sending request to Gemini API.")
    try:
        response = model.generate_content(prompt)
        
        log.info("GENERATION complete. Received response from Gemini.")
        log.debug(f"Raw Gemini response text: '{response.text}'")
        
        return response.text
    except Exception as e:
        log.error(f"An error occurred during Gemini API call: {e}", exc_info=True)
        return "Sorry, I had a moment of brain-freeze. Could you ask me that again?"
    
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

class TradeAgent:
    """
    A multi-tool agent that can retrieve trades or perform aggregations.
    """
    def __init__(self, trades_filepath: str):
        log.info("--- Initializing Trade Agent ---")
        if not query_engine_model:
            raise ConnectionError("Gemini model not initialized.")
        
        self.model = query_engine_model
        
        log.info(f"Loading trades from '{trades_filepath}'...")
        try:
            with open(trades_filepath, "r") as f:
                trades_list = json.load(f)
        except FileNotFoundError:
            log.error(f"Fatal: The trade data file '{trades_filepath}' was not found.")
            raise
        
        self.trades_df = pd.DataFrame(trades_list)
        self.trades_df['Date'] = pd.to_datetime(self.trades_df['Date'])
        log.info(f"Loaded {len(self.trades_df)} trades successfully.")

        log.info("Analyzing trader persona...")
        self.persona = analyze_trader_persona_with_pandas(trades_list)
        log.info(f"Persona created: {self.persona.get('summary_line', 'N/A')}")
        
        # --- Initialize BOTH engines ---
        log.info("Initializing Pandas Query and Aggregation Engines...")
        self.query_engine = PandasQueryEngine(df=self.trades_df)
        self.aggregation_engine = PandasAggregationEngine(df=self.trades_df) # <-- New
        log.info("--- Agent Initialized Successfully ---")

    def _classify_query(self, query: str) -> str:
        """Uses the LLM to classify the user's intent."""
        log.debug("Classifying user query intent...")
        prompt = f"""
        Given the user's question, is the user asking for a list of specific trades or for a calculated number/statistic (like a sum, average, count, or breakdown)?
        Respond with only the single word: 'retrieval' or 'aggregation'.

        User Question: "{query}"
        Classification:
        """
        try:
            response = self.model.generate_content(prompt)
            classification = response.text.strip().lower()
            log.info(f"Query classified as: '{classification}'")
            if classification in ['retrieval', 'aggregation']:
                return classification
        except Exception as e:
            log.error(f"Could not classify query: {e}")
        return 'retrieval'

    def generate_response(self, query: str) -> str:
        """
        Generates a response using a dynamic RAG pattern based on query type.
        """
        log.info(f"--- Received new query: '{query}' ---")
        
        # 1. ROUTER: Classify the user's intent
        query_type = self._classify_query(query)
        
        context_data = {}
        context_key = ""

        # 2. RETRIEVAL / AGGREGATION: Call the appropriate tool
        if query_type == 'aggregation':
            log.info("[RAG-Step 1/2] AGGREGATION: Calculating data with PandasAggregationEngine.")
            context_data = self.aggregation_engine.aggregate(query)
            context_key = "CALCULATED DATA"
        else:
            log.info("[RAG-Step 1/2] RETRIEVAL: Finding relevant trades with PandasQueryEngine.")
            context_data = self.query_engine.query(query)
            context_key = "RELEVANT TRADE EXAMPLES"

        # 3. AUGMENTATION & GENERATION
        log.info("[RAG-Step 2/2] AUGMENTATION & GENERATION: Building prompt and creating response.")
        
        prompt = f"""
        You are a conversational AI acting as a trader. Your personality is defined by your Persona.
        A user has asked a question. You have been given a piece of context data to help you answer.
        Use the context data to form a direct, conversational, and concise answer in the first person ("I", "my").

        ---
        PERSONA:
        {json.dumps(self.persona, indent=2)}
        ---
        CONTEXT: {context_key}:
        {json.dumps(context_data, indent=2, default=str) if context_data is not None else "No data available."}
        ---
        USER'S QUESTION:
        "{query}"
        
        YOUR CONVERSATIONAL AND CONCISE RESPONSE:
        """
        log.debug(f"--- Full Prompt Sent to Gemini ---\n{prompt}\n---------------------------------")

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            log.error(f"An error occurred during Gemini API call: {e}", exc_info=True)
            return "Sorry, I had a moment of brain-freeze. Could you ask me again?"

# # --- Main Execution Block ---
# if __name__ == "__main__":
#     try:
#         agent = TradeAgent(trades_filepath="trades.json")
        
#         print("\n--- Conversational Trade Agent (Multi-Tool Mode) ---")
#         print("I can retrieve trades or calculate stats (e.g., 'total volume', 'how many trades?'). Type 'quit' to exit.")

#         while True:
#             user_query = input("\nYou: ")
#             if user_query.lower() in ['quit', 'exit']:
#                 print("Agent: Catch you on the next trade. Cheers!")
#                 break
            
#             response = agent.generate_response(user_query)
#             print(f"Agent: {response}")

#     except (ConnectionError, FileNotFoundError, ValueError) as e:
#         log.fatal(f"Could not start the agent. {e}")
#     except Exception as e:
#         log.fatal(f"An unexpected error occurred: {e}", exc_info=True)