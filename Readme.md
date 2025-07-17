# Conversational Trade Agent

This project is an AI-powered agent that emulates a trader's personality and answers questions about trade history using natural language. It leverages Gemini LLM, FastAPI, and pandas for data analysis.

> **Live Demo:**  
> The API can be accessed here: [https://coinfantasy-be.onrender.com/docs](https://coinfantasy-be.onrender.com/docs)

## Folder Structure

```
.
├── .env
├── .gitignore
├── requirements.txt
├── src/
│   ├── agent_logic.py
│   ├── main.py
│   ├── pandas_aggregation_engine.py
│   ├── pandas_query_engine.py
│   ├── persona_logic.py
│   ├── __pycache__/
│   ├── data/
│   │   ├── trades.json
│   │   └── trades_value_persona.json
│   └── seeding/
│       ├── generateData.js
│       ├── generatevalueData.js
│       └── package.json
```

### Root Files

- **.env**: Environment variables (API keys, etc.).
- **.gitignore**: Specifies files/folders to ignore in version control.
- **requirements.txt**: Python dependencies for the project.

### `src/` Directory

- **agent_logic.py**: Implements the main agent logic, including RAG (Retrieval-Augmentation-Generation) and integration with Gemini LLM.
- **main.py**: FastAPI application entry point; exposes API endpoints for chat and persona retrieval.
- **pandas_aggregation_engine.py**: Handles natural language aggregation queries using pandas and Gemini.
- **pandas_query_engine.py**: Handles natural language retrieval/filtering queries using pandas and Gemini.
- **persona_logic.py**: Analyzes trade data to derive trader persona and profile.
- **__pycache__/**: Python bytecode cache (ignored by git).

#### `src/data/`

- **trades.json**: Example trade data for a general trader persona.
- **trades_value_persona.json**: Example trade data for a value/technical trader persona.

#### `src/seeding/`

- **generateData.js**: Script to generate sample trade data for general persona (Node.js, uses Faker).
- **generatevalueData.js**: Script to generate sample trade data for value/technical persona.
- **package.json**: Node.js dependencies for seeding scripts.

---

## Getting Started

1. Install Python dependencies:
    ```sh
    pip install -r requirements.txt
    ```
2. Set up your `.env` file with required API keys.
3. Run the FastAPI server:
    ```sh
    uvicorn src.main:app --reload
    ```
4. (Optional) Generate new trade data using the seeding scripts in `src/seeding/`.

---

## API Endpoints

### `POST /chat`

**Purpose:**  
Interact with the conversational trade agent.

**Functionality:**  
- Accepts a user query (question or instruction about trades or trading strategy).
- Processes the query using Gemini LLM and pandas, referencing trade data and trader persona.
- Returns a natural language response, emulating a trader’s personality and providing insights, analysis, or answers based on the available data.

**Example Request:**
```json
{
  "message": "What was my most profitable trade last month?"
}
```

**Example Response:**
```json
{
  "response": "Your most profitable trade last month was buying BTC on June 12, which yielded a profit of $1,200."
}
```

---

### `GET /persona`

**Purpose:**  
Retrieve the calculated trader persona/profile.

**Functionality:**  
- Analyzes the trade history and patterns using pandas and custom logic.
- Returns a summary of the trader’s style (e.g., value investor, technical trader), risk profile, and behavioral insights.

**Example Response:**
```json
{
  "persona": "Value Investor",
  "description": "You tend to hold assets for longer periods and focus on undervalued opportunities. Your trading style is cautious and data-driven."
}
```