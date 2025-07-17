const { faker } = require('@faker-js/faker');
const fs = require('fs');

// --- Configuration ---
const NUM_TRADES = 100; // Generate 100 trades as requested.

// --- Data Pools ---
const ASSETS = ['BTC', 'ETH', 'SOL', 'DOGE', 'PEPE', 'ADA', 'XRP', 'MATIC'];

// This object maps a specific strategy (the key) to its general style (the value).
// This is perfect for creating our two tags.
const STRATEGY_PAIRS = {
    'volume-breakout': 'Technical',
    'rsi-divergence': 'Technical',
    'sentiment-riding': 'Sentiment',
    'meme-trend': 'Sentiment',
    'value-entry': 'Value',
    'event-driven': 'Sentiment',
    'long-term-hold': 'Value',
    'stop-loss-hit': 'Risk-Management',
    'take-profit-target': 'Risk-Management'
};

const OUTCOMES = ['Profit', 'Loss', 'Neutral'];

/**
 * Generates a single trade record with exactly two tags.
 * @param {number} tradeId - The unique identifier for the trade.
 * @returns {object} A trade object conforming to the specified column names.
 */
function createRandomTrade(tradeId) {
    const asset = faker.helpers.arrayElement(ASSETS);
    const outcome = faker.helpers.arrayElement(OUTCOMES);

    // Select a random strategy from our list of keys
    const primaryStrategy = faker.helpers.arrayElement(Object.keys(STRATEGY_PAIRS));
    // Get the corresponding style for that strategy
    const secondaryTag = STRATEGY_PAIRS[primaryStrategy];

    // This structure ensures we always have exactly two tags.
    const tags = [primaryStrategy, secondaryTag];

    // Make meme-related tags more likely for meme coins
    if (['DOGE', 'PEPE'].includes(asset) && Math.random() > 0.3) { // 70% chance
        tags[0] = 'meme-trend';
        tags[1] = 'Sentiment';
    }

    return {
        "Trade ID": `T${String(tradeId).padStart(3, '0')}`,
        "Asset": asset,
        "Buy/Sell": faker.helpers.arrayElement(['Buy', 'Sell']),
        "Price": parseFloat(faker.finance.amount({ min: 0.06, max: 45000, dec: 2 })),
        "Volume": parseFloat(faker.finance.amount({ min: 1, max: 10000, dec: 2 })),
        "Date": faker.date.between({ from: '2023-01-01T00:00:00.000Z', to: '2024-07-01T00:00:00.000Z' }),
        "Outcome": outcome,
        "Tags": tags,
    };
}

// --- Main Execution ---
const trades = [];
for (let i = 1; i <= NUM_TRADES; i++) {
    trades.push(createRandomTrade(i));
}

// Write the data to trades.json with human-readable formatting.
fs.writeFileSync('trades.json', JSON.stringify(trades, null, 2));

console.log(`✅ Successfully generated ${NUM_TRADES} trades in trades.json`);
console.log('Sample trade record:', trades[0]);