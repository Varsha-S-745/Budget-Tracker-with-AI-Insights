-- SQLite schema for budget tracker
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    type TEXT NOT NULL CHECK (type IN ('expense', 'income')),
    category TEXT NOT NULL,
    note TEXT
);

-- Some starter data (optional). Comment out if not needed.
INSERT INTO transactions (date, amount, type, category, note) VALUES
(date('now','start of month','-2 months','+5 days'), 1200, 'expense', 'Groceries', 'monthly groceries'),
(date('now','start of month','-2 months','+10 days'), 300, 'expense', 'Transport', 'fuel'),
(date('now','start of month','-1 months','+3 days'), 1500, 'expense', 'Rent', 'rent'),
(date('now','start of month','-1 months','+6 days'), 500, 'expense', 'Dining', 'dinner out'),
(date('now','start of month','+2 days'), 700, 'expense', 'Groceries', 'this month groceries'),
(date('now','start of month','+5 days'), 400, 'expense', 'Dining', 'cafe visits'),
(date('now','start of month','+7 days'), 2000, 'income', 'Salary', 'salary credit'),
(date('now','start of month','+8 days'), 600, 'expense', 'Utilities', 'electricity');
