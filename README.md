# Budget-Tracker-with-AI-Insights
Budget Tracker is a mini full‑stack project using **HTML, CSS and Vanilla JS** on the frontend and **Python (Flask and SQLite)** on the backend. It tracks income/expenses and provides simple AI-ish insights: monthly trend forecasting, outlier detection, and guideline tips.

## Features
- **Full-Stack** – Combines HTML/CSS/JS frontend with Python-Flask backend for real-world practice.
- **AI Insights** – Predicts expenses, detects unusual spending, and applies 50/30/20 budgeting tips.
- **Lightweight** – Uses SQLite for storage, easy to run locally or deploy on free hosting.
- **User-Friendly** – Simple transaction forms, auto-updating charts, mobile-friendly UI.
- **Customizable** – Easily extend with login, recurring expenses, or multi-currency support.
- **Educational** – Covers UI, API design, database handling, and basic AI/ML.
- **Cost-Free** – Works without paid APIs, scalable if needed.

## Project Structure
```
budget-ai/
├─ app.py
├─ schema.sql
├─ requirements.txt
├─ templates/
│  ├─ base.html
│  └─ index.html
└─ static/
   ├─ styles.css
   └─ script.js
```
## 🛠 Tools & Technologies Used
**Frontend:**
- HTML5, CSS3, JavaScript
- Chart.js (for visualizations)

**Backend:**
- Python 3.x
- Flask (web framework)

**Database:**
- SQLite (lightweight relational database)

**AI/Insights:**
- Pandas & NumPy (data processing)
- Scikit-learn (trend prediction & anomaly detection)

## Method to run the project Locally (Windows/macOS/Linux)
1. **Install Python 3.10+** and **pip**.
2. Open a terminal and create a folder:
   ```
   python -m venv .venv
   # Activate it:
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```
4. **Initialize the database** :
   ```
   python app.py --init-db
   ```
5. **Run the server**:
   ```bash
   python app.py
   ```
   -Visit http://127.0.0.1:5000 in your browser.

