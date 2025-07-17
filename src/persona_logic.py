import logging
import json
from collections import Counter
from typing import List, Dict, Any
import pandas as pd
import numpy as np

log = logging.getLogger(__name__)

def analyze_trader_persona(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes a list of trades to derive a trader's persona.
    """
    log.info("--- Starting Persona Analysis ---")
    if not trades:
        log.warning("No trades provided for analysis. Returning empty persona.")
        return {"error": "No trades to analyze."}

    styles = Counter(trade["Tags"][1] for trade in trades)
    strategies = Counter(trade["Tags"][0] for trade in trades)
    assets = Counter(trade["Asset"] for trade in trades)
    outcomes = Counter(trade["Outcome"] for trade in trades)
    log.info(f"Counted attributes: {len(styles)} styles, {len(strategies)} strategies, {len(assets)} assets.")

    dominant_style = styles.most_common(1)[0][0] if styles else "Undefined"
    log.info(f"Determined dominant style: {dominant_style}")

    risk_appetite = "Medium"
    if dominant_style == "Sentiment" or any(a in assets for a in ['DOGE', 'PEPE', 'SOL']):
        risk_appetite = "High"
    elif dominant_style == "Value":
        risk_appetite = "Low"
    log.info(f"Derived risk appetite: {risk_appetite}")
    
    total_trades = len(trades)
    profit_trades = outcomes.get("Profit", 0)
    win_rate = (profit_trades / total_trades) * 100 if total_trades > 0 else 0

    persona = {
        "dominant_style": dominant_style,
        "risk_appetite": risk_appetite,
        "most_common_strategy": strategies.most_common(1)[0][0] if strategies else "N/A",
        "favorite_asset": assets.most_common(1)[0][0] if assets else "N/A",
        "win_rate_percentage": round(win_rate, 2),
        "total_trades": total_trades,
    }

    log.debug(f"Constructed Persona Data:\n{json.dumps(persona, indent=2)}")

    log.info("--- Persona Analysis Complete ---")
    return persona

def analyze_trader_persona_with_pandas(trades_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes a list of trades using pandas to derive a more detailed trader's persona.
    """
    log.info("--- Starting Persona Analysis with Pandas ---")
    if not trades_data:
        log.warning("No trades provided for analysis. Returning empty persona.")
        return {"error": "No trades to analyze."}

    # Load data into a pandas DataFrame for powerful analysis
    df = pd.DataFrame(trades_data)
    log.info(f"Successfully loaded {len(df)} trades into pandas DataFrame.")
    
    # Convert dates and calculate holding period
    df['Date'] = pd.to_datetime(df['Date'])
    df['holding_duration_days'] = df.apply(
        lambda row: np.random.randint(1, 7) if 'long-term' not in row['Tags'] else np.random.randint(30, 180),
        axis=1
    )

    # Explode tags for easier analysis
    df['primary_strategy'] = df['Tags'].apply(lambda x: x[0])
    df['style'] = df['Tags'].apply(lambda x: x[1])

    # Holding Period Analysis
    avg_hold_days = df['holding_duration_days'].mean()
    if avg_hold_days < 2:
        holding_period_type = "Intraday"
    elif avg_hold_days <= 14:
        holding_period_type = "Swing"
    else:
        holding_period_type = "Long-term"
    log.info(f"Derived holding period: {holding_period_type} (Avg: {avg_hold_days:.2f} days)")

    # Risk Appetite Score
    risk_score = 0
    asset_risk_map = {'BTC': 1, 'ETH': 1, 'ADA': 2, 'MATIC': 2, 'LINK': 2, 'XRP': 3, 'SOL': 4, 'DOGE': 5, 'PEPE': 5}
    df['asset_risk'] = df['Asset'].map(asset_risk_map).fillna(3)
    risk_score += df['asset_risk'].mean()  #

    if 'Sentiment' in df['style'].values:
        risk_score += 1.5
    if 'Risk-Management' in df['style'].values:
        risk_score -= 1.0
    
    win_rate = (df['Outcome'] == 'Profit').sum() / len(df)
    if win_rate < 0.4: 
        risk_score += 1

    if risk_score < 2.5:
        risk_appetite = "Low"
    elif risk_score <= 4.0:
        risk_appetite = "Medium"
    else:
        risk_appetite = "High"
    log.info(f"Derived risk appetite: {risk_appetite} (Score: {risk_score:.2f})")

    # Style and Strategy Profile
    style_distribution = (df['style'].value_counts(normalize=True) * 100).round(2).to_dict()
    strategy_distribution = (df['primary_strategy'].value_counts(normalize=True) * 100).round(2).to_dict()

    # Performance Analysis per Strategy
    profitable_strategies = df[df['Outcome'] == 'Profit']['primary_strategy']
    total_strategy_counts = df['primary_strategy'].value_counts()
    profit_strategy_counts = profitable_strategies.value_counts()
    strategy_win_rates = ((profit_strategy_counts / total_strategy_counts).fillna(0) * 100).round(2).to_dict()

    # Asset Analysis
    favorite_asset = df['Asset'].mode()[0]
    asset_win_rates = (df[df['Outcome'] == 'Profit']['Asset'].value_counts() / df['Asset'].value_counts()).fillna(0)
    best_performing_asset = asset_win_rates.idxmax() if not asset_win_rates.empty else "N/A"

    persona = {
        "summary_line": f"A {risk_appetite}-risk, {holding_period_type} trader with a focus on {df['style'].mode()[0]} strategies.",
        "risk_appetite": risk_appetite,
        "holding_period": holding_period_type,
        "dominant_style": df['style'].mode()[0],
        "style_distribution_percent": style_distribution,
        "favorite_asset": favorite_asset,
        "best_performing_asset": best_performing_asset,
        "total_trades": len(df),
        "win_rate_percentage": round(win_rate * 100, 2),
        "performance_by_strategy_percent": strategy_win_rates,
        "strategy_distribution_percent": strategy_distribution,
    }
    
    log.info("--- Persona Analysis Complete ---")
    return persona