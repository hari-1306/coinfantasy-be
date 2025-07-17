import os
import logging
import pandas as pd
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

# --- API Configuration ---
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not found.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    log.info("Gemini API configured successfully for PandasQueryEngine.")
except Exception as e:
    log.error(f"Failed to configure Gemini API: {e}", exc_info=True)
    model = None

class PandasQueryEngine:
    """
    Translates natural language to a full line of pandas filtering code and executes it.
    Includes a robust manual parser as a fallback.
    """
    def __init__(self, df: pd.DataFrame):
        if model is None:
            raise ConnectionError("Gemini API model is not available. Engine cannot function.")
        self.df = df
        self.model = model
        self.schema_prompt = self._generate_schema_prompt()
        log.info("PandasQueryEngine initialized.")

    def _generate_schema_prompt(self) -> str:
        """Generates a detailed schema description for the LLM."""
        schema = "You are querying a pandas DataFrame variable named `df` with the following columns:\n"
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            schema += f"- `{col}` (Type: {dtype})\n"
        if 'Tags' in self.df.columns:
            schema += "\nThe 'Tags' column contains a list of strings.\n"
        return schema

    def _clean_llm_output(self, llm_response: str) -> str:
        """
        A robust function to clean the raw LLM output.
        It removes markdown code fences and ALL backticks.
        """
        return llm_response.replace("`", "").strip()

    def _generate_pandas_code(self, user_query: str) -> str:
        """Uses the LLM to generate a full line of pandas filtering code."""
        prompt = f"""
        You are an expert Python data analyst. Your task is to convert a user's question into a single line of Python code that filters a pandas DataFrame named `df`.

        {self.schema_prompt}
        
        RULES:
        - The output MUST be a single line of code that evaluates to a filtered DataFrame.
        - Use standard boolean indexing with brackets `df[...]`.
        - Use `&` for AND, `|` for OR. Wrap conditions in parentheses.
        - **CRITICAL**: Do not use backticks (`) in your response at all.
        - **DO NOT** use `df.query()`.

        EXAMPLES:
        User Query: "Show me your buy trades for DOGE"
        Pandas Code: df[(df['Buy/Sell'] == 'Buy') & (df['Asset'] == 'DOGE')]

        User Query: "Tell me about your most profitable trades."
        Pandas Code: df[df['Outcome'] == 'Profit']

        User Query: "What were your trades based on sentiment?"
        Pandas Code: df[df['Tags'].apply(lambda tags: 'Sentiment' in tags)]
        ---
        Now, convert the following user query. Respond with ONLY the single line of Python code.

        User Query: "{user_query}"
        Pandas Code:
        """
        try:
            log.info(f"Generating pandas code for: '{user_query}'")
            response = self.model.generate_content(prompt)
            code_string = self._clean_llm_output(response.text)
            log.info(f"CLEANED pandas code: '{code_string}'")
            return code_string
        except Exception as e:
            log.error(f"Failed to generate code from Gemini: {e}", exc_info=True)
            return ""

    def _fallback_manual_parse(self, user_query: str) -> pd.DataFrame:
        """
        A robust manual parser to be used when the LLM fails.
        Constructs a pandas boolean mask based on keywords.
        """
        log.warning("Falling back to robust manual parser.")
        q = user_query.lower()
        
        # Start with a mask that includes all trades
        final_mask = pd.Series(True, index=self.df.index)
        
        # Find all asset tickers mentioned in the query
        assets_in_query = [asset for asset in self.df['Asset'].unique() if asset.lower() in q]
        if assets_in_query:
            final_mask &= self.df['Asset'].isin(assets_in_query)

        # --- Filter by Outcome ---
        if 'loss' in q or 'lost' in q:
            final_mask &= (self.df['Outcome'] == 'Loss')
        if 'profit' in q or 'win' in q or 'won' in q:
            final_mask &= (self.df['Outcome'] == 'Profit')
        if 'neutral' in q:
             final_mask &= (self.df['Outcome'] == 'Neutral')

        # --- Filter by Action ---
        if 'buy' in q or 'bought' in q:
            final_mask &= (self.df['Buy/Sell'] == 'Buy')
        if 'sell' in q or 'sold' in q:
             final_mask &= (self.df['Buy/Sell'] == 'Sell')

        # --- Filter by Tags ---
        all_tags = set(tag for tags_list in self.df['Tags'] for tag in tags_list)
        tags_in_query = [tag for tag in all_tags if tag.lower().replace('-', ' ') in q]
        if tags_in_query:
             final_mask &= self.df['Tags'].apply(lambda tags: any(t in tags for t in tags_in_query))

        return self.df[final_mask]

    def query(self, user_query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a semantic search by generating and evaluating pandas code.
        """
        pandas_code_str = self._generate_pandas_code(user_query)

        results_df = None
        if pandas_code_str:
            try:
                results_df = eval(pandas_code_str, {"df": self.df, "pd": pd})
            except Exception as e:
                log.error(f"Failed to execute LLM-generated code: '{pandas_code_str}'. Error: {e}", exc_info=True)
                results_df = self._fallback_manual_parse(user_query)
        else:
            # If the LLM returns nothing, go straight to the fallback
            results_df = self._fallback_manual_parse(user_query)
        
        final_df = results_df.sort_values(by='Date').tail(limit)
        log.info(f"Query executed successfully. Found {len(final_df)} relevant trade(s).")
        return final_df.to_dict('records')

# # --- (main_example function for testing) ---
# def main_example():
#     """Demonstrates how to use the PandasQueryEngine."""
#     logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

#     try:
#         with open("trades.json", "r") as f:
#             trades_list = json.load(f)
#             # Ensure a DOGE buy trade exists for the test case
#             if not any(trade['Asset'] == 'DOGE' and trade['Buy/Sell'] == 'Buy' for trade in trades_list):
#                  trades_list.append({
#                     "Trade ID": "T999", "Asset": "DOGE", "Buy/Sell": "Buy", "Price": 0.15,
#                     "Volume": 5000, "Date": "2024-02-01T00:00:00.000Z", "Outcome": "Neutral",
#                     "Tags": ["meme-trend-riding", "Sentiment"]
#                 })
#     except FileNotFoundError:
#         log.error("trades.json not found. Please ensure the data file exists.")
#         return

#     df = pd.DataFrame(trades_list)
#     df['Date'] = pd.to_datetime(df['Date'])

#     try:
#         query_engine = PandasQueryEngine(df=df)
#         test_queries = [
#             "Why did you buy DOGE?",
#             "Tell me about your losses.",
#             "What were your profitable trades with ETH?",
#             "What kind of value trades do you do?",
#         ]
#         for q in test_queries:
#             print(f"\n--- Testing Query: '{q}' ---")
#             relevant_trades = query_engine.query(q)
#             print(f"Found {len(relevant_trades)} trades:")
#             print(json.dumps(relevant_trades, indent=2, default=str))
#     except (ValueError, ConnectionError) as e:
#         log.error(f"Could not run example: {e}")

# if __name__ == '__main__':
#     main_example()