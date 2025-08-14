#!/usr/bin/env python3
import os
import sqlite3
from flask import Flask, jsonify, request, render_template, g
from datetime import datetime, date
import math

try:
    import numpy as np
except Exception:
    np = None

DATABASE = os.path.join(os.path.dirname(__file__), "budget.db")

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript(open(os.path.join(os.path.dirname(__file__), "schema.sql"), "r", encoding="utf-8").read())
        db.commit()

def parse_date(dstr):
    return datetime.strptime(dstr, "%Y-%m-%d").date()

def month_key(dt: date):
    return f"{dt.year}-{dt.month:02d}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/transactions", methods=["GET", "POST"])
def api_transactions():
    db = get_db()
    if request.method == "POST":
        data = request.get_json(force=True)
        try:
            tdate = parse_date(data.get("date"))
            amount = float(data.get("amount"))
            ttype = data.get("type")
            if ttype not in ("expense", "income"):
                raise ValueError("Invalid type")
            category = (data.get("category") or "").strip()[:50]
            note = (data.get("note") or "").strip()[:200]
        except Exception as e:
            return jsonify({"ok": False, "error": f"Invalid input: {e}"}), 400
        db.execute(
            "INSERT INTO transactions (date, amount, type, category, note) VALUES (?, ?, ?, ?, ?)",
            (tdate.isoformat(), amount, ttype, category, note),
        )
        db.commit()
        return jsonify({"ok": True})
    else:
        rows = db.execute(
            "SELECT id, date, amount, type, category, note FROM transactions ORDER BY date DESC, id DESC"
        ).fetchall()
        return jsonify([dict(r) for r in rows])

@app.route("/api/transactions/<int:tid>", methods=["DELETE"])
def delete_transaction(tid):
    db = get_db()
    db.execute("DELETE FROM transactions WHERE id = ?", (tid,))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/insights")
def insights():
    db = get_db()
    rows = db.execute("SELECT date, amount, type, category FROM transactions").fetchall()
    tx = [dict(r) for r in rows]

    today = date.today()
    this_month = f"{today.year}-{today.month:02d}"
    monthly = {}
    cat_totals_this_month = {}
    cat_all = {}

    for r in tx:
        d = parse_date(r["date"])
        mk = month_key(d)
        amt = float(r["amount"]) * (1 if r["type"] == "expense" else -1)
        monthly.setdefault(mk, 0.0)
        monthly[mk] += amt

        if mk == this_month and r["type"] == "expense":
            cat_totals_this_month[r["category"]] = cat_totals_this_month.get(r["category"], 0.0) + float(r["amount"])

        if r["type"] == "expense":
            cat_all.setdefault(r["category"], []).append(float(r["amount"]))

    sorted_months = sorted(monthly.keys())
    months_tail = sorted_months[-12:]
    forecast = None
    trend_slope = None
    if months_tail:
        y = [monthly[m] for m in months_tail]
        x = list(range(len(y)))
        if np and len(y) >= 2:
            coeffs = np.polyfit(x, y, 1)
            trend_slope = float(coeffs[0])
            forecast = float(np.polyval(coeffs, len(y)))
        else:
            forecast = sum(y) / len(y)

    outlier_notes = []
    for cat, vals in cat_all.items():
        if len(vals) < 3:
            continue
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = math.sqrt(var)
        threshold = mean + 2 * std
        for r in tx:
            if r["type"] == "expense" and r["category"] == cat and float(r["amount"]) > threshold:
                outlier_notes.append({
                    "category": cat,
                    "amount": float(r["amount"]),
                    "date": r["date"],
                    "threshold": round(threshold, 2)
                })

    needs_categories = {"Rent", "Groceries", "Utilities", "Transport", "Healthcare", "Insurance", "Education"}
    wants_categories = {"Dining", "Entertainment", "Shopping", "Travel", "Subscriptions"}
    savings_categories = {"Investments", "Savings"}
    totals = {"needs": 0.0, "wants": 0.0, "savings": 0.0}

    dbmonth = db.execute("SELECT amount, type, category FROM transactions WHERE strftime('%Y-%m', date) = ?", (this_month,)).fetchall()
    for r in dbmonth:
        amt = float(r["amount"])
        if r["type"] == "income":
            totals["savings"] += amt
            continue
        cat = r["category"]
        if cat in needs_categories:
            totals["needs"] += amt
        elif cat in wants_categories:
            totals["wants"] += amt
        elif cat in savings_categories:
            totals["savings"] += amt

    monthly_expense = totals["needs"] + totals["wants"]
    guideline = {
        "needs_pct": round((totals["needs"] / monthly_expense) * 100, 1) if monthly_expense > 0 else 0.0,
        "wants_pct": round((totals["wants"] / monthly_expense) * 100, 1) if monthly_expense > 0 else 0.0,
        "savings_amount": round(totals["savings"], 2),
    }
    recs = []
    if guideline["needs_pct"] > 50:
        recs.append(f"Your 'Needs' are {guideline['needs_pct']}% of expenses (target ≤ 50%). Consider reducing utilities, groceries, or transport.")
    if guideline["wants_pct"] > 30:
        recs.append(f"'Wants' are {guideline['wants_pct']}% of expenses (target ≤ 30%). Try a weekly cap on Dining/Shopping.")
    if guideline["savings_amount"] < 0.2 * (monthly_expense):
        recs.append(f"Set aside at least 20% of expenses for savings/investments. You're currently at ₹{guideline['savings_amount']:.0f}.")

    resp = {
        "monthly_net": [{"month": m, "net": round(monthly[m], 2)} for m in months_tail],
        "forecast_next_month_net": round(forecast, 2) if forecast is not None else None,
        "trend_slope": round(trend_slope, 2) if trend_slope is not None else None,
        "top_categories_this_month": sorted(
            [{"category": c, "total": round(v, 2)} for c, v in cat_totals_this_month.items()],
            key=lambda x: x["total"], reverse=True
        )[:5],
        "outliers": outlier_notes[:5],
        "recommendations": recs[:5],
    }
    return jsonify(resp)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Budget Tracker with AI Insights")
    parser.add_argument("--init-db", action="store_true", help="Initialize the SQLite database")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5000)))
    args = parser.parse_args()

    if args["init_db"] if isinstance(args, dict) else args.init_db:
        init_db()
        print("Database initialized at", DATABASE)
    else:
        if not os.path.exists(DATABASE):
            init_db()
        app.run(host="0.0.0.0", port=args.port, debug=True)
