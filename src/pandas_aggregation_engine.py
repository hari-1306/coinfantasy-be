import logging
import pandas as pd
from typing import Any

from src.pandas_query_engine import model

log = logging.getLogger(__name__)

class PandasAggregationEngine:
    """
    Translates natural language to pandas aggregation code and executes it.
    """
    def __init__(self, df: pd.DataFrame):
        if model is None:
            raise ConnectionError("Gemini API model is not available. Engine cannot function.")
        self.df = df
        self.model = model
        self.schema_prompt = self._generate_schema_prompt()
        log.info("PandasAggregationEngine initialized.")

    def _generate_schema_prompt(self) -> str:
        """Generates a detailed schema description for the LLM."""
        schema = "You are working with a pandas DataFrame variable named `df` with the following columns:\n"
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            schema += f"- `{col}` (Type: {dtype})\n"
        return schema

    def _clean_llm_output(self, llm_response: str) -> str:
        """Cleans the raw LLM output."""
        return llm_response.replace("`", "").strip()

    def _generate_pandas_code(self, user_query: str) -> str:
        """Uses the LLM to generate pandas aggregation code."""
        prompt = f"""
        You are an expert Python data analyst. Your task is to convert a user's question into a single line of Python code that calculates a result from a pandas DataFrame named `df`.

        {self.schema_prompt}

        RULES:
        - The code MUST be a single line that can be executed by Python's `eval()` function.
        - It should produce a single value, a dictionary, or a JSON string as a result.
        - For a real "Profit/Loss", assume a simple calculation for this exercise: sum of `Price` * `Volume`.
        - Use standard pandas functions like `.sum()`, `.mean()`, `.count()`, `.value_counts().to_json()`.

        EXAMPLES:
        User Query: "How many trades have I made?"
        Pandas Code: `len(df)`

        User Query: "What is my total trading volume?"
        Pandas Code: `df['Volume'].sum()`

        User Query: "What is my overall profit?"
        Pandas Code: `(df[df['Outcome'] == 'Profit']['Price'] * df[df['Outcome'] == 'Profit']['Volume']).sum() - (df[df['Outcome'] == 'Loss']['Price'] * df[df['Outcome'] == 'Loss']['Volume']).sum()`

        User Query: "What's the breakdown of my trade outcomes?"
        Pandas Code: `df['Outcome'].value_counts().to_json()`

        User Query: "What's my average trade size for BTC?"
        Pandas Code: `df[df['Asset'] == 'BTC']['Volume'].mean()`
        ---
        Now, convert the following user query. Respond with ONLY the single line of Python code.

        User Query: "{user_query}"
        Pandas Code:
        """
        try:
            log.info(f"AGGREGATION: Generating pandas code for: '{user_query}'")
            response = self.model.generate_content(prompt)
            code_string = self._clean_llm_output(response.text)
            log.info(f"AGGREGATION: CLEANED pandas code: '{code_string}'")
            return code_string
        except Exception as e:
            log.error(f"AGGREGATION: Failed to generate code from Gemini: {e}", exc_info=True)
            return ""

    def aggregate(self, user_query: str) -> Any:
        """
        Performs a semantic aggregation by generating and evaluating pandas code.
        """
        pandas_code_str = self._generate_pandas_code(user_query)

        if not pandas_code_str:
            log.warning("AGGREGATION: Generated code was empty. Returning None.")
            return None

        try:
            result = eval(pandas_code_str, {"df": self.df, "pd": pd})
            log.info(f"AGGREGATION: Code executed successfully. Result: {result}")
            return result
        except Exception as e:
            log.error(f"AGGREGATION: Failed to execute code: '{pandas_code_str}'. Error: {e}", exc_info=True)
            return "Error: I couldn't calculate that."