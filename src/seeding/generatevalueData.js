const { faker } = require('@faker-js/faker');
const fs = require('fs');

// --- Configuration ---
const NUM_TRADES = 100;
// The name of the new output file for this persona
const OUTPUT_FILENAME = 'trades.json';

// --- Data Pools for a VALUE/TECHNICAL Trader ---

// 1. ASSETS: Focused on more established "blue-chip" cryptocurrencies. No meme coins.
const ASSETS = ['BTC', 'ETH', 'ADA', 'MATIC', 'XRP', 'LINK'];

// 2. STRATEGIES: Focused on value, technical analysis, and disciplined risk management.
const STRATEGY_PAIRS = {
    'value-entry': 'Value',
    'long-term-hold': 'Value',
    'support-resistance-play': 'Technical',
    'rsi-divergence': 'Technical',
    'take-profit-target': 'Risk-Management',
    'stop-loss-hit': 'Risk-Management'
};

const OUTCOMES = ['Profit', 'Loss', 'Neutral'];

/**
 * Generates a single trade record for our Value/Technical trader.
 * @param {number} tradeId - The unique identifier for the trade.
 * @returns {object} A trade object.
 */
function createRandomTrade(tradeId) {
    // Select a random strategy from our new, more conservative list
    const primaryStrategy = faker.helpers.arrayElement(Object.keys(STRATEGY_PAIRS));
    const secondaryTag = STRATEGY_PAIRS[primaryStrategy];
    const tags = [primaryStrategy, secondaryTag];

    return {
        "Trade ID": `T${String(tradeId).padStart(3, '0')}`,
        "Asset": faker.helpers.arrayElement(ASSETS),
        "Buy/Sell": faker.helpers.arrayElement(['Buy', 'Sell']),
        "Price": parseFloat(faker.finance.amount({ min: 0.5, max: 45000, dec: 2 })),
        "Volume": parseFloat(faker.finance.amount({ min: 1, max: 50, dec: 2 })), // Smaller volumes
        "Date": faker.date.between({ from: '2023-01-01T00:00:00.000Z', to: '2024-07-01T00:00:00.000Z' }),
        "Outcome": faker.helpers.arrayElement(OUTCOMES),
        "Tags": tags,
    };
}

// --- Main Execution ---
const trades = [];
for (let i = 1; i <= NUM_TRADES; i++) {
    trades.push(createRandomTrade(i));
}

fs.writeFileSync(OUTPUT_FILENAME, JSON.stringify(trades, null, 2));

console.log(`✅ Successfully generated ${NUM_TRADES} trades for the VALUE persona.`);
console.log(`✅ Data saved to ${OUTPUT_FILENAME}`);