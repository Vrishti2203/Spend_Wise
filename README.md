# SpendWise – AI Personal Expense Tracker

SpendWise is a personal expense tracking application that uses AI to help users manage and understand their spending.

## Features
- Add, view, edit and delete expenses.
- Track monthly spending.
- AI-powered expense management.
- AI-based spending queries and insights.
- MySQL database integration.

## Technologies Used
- Python
- FastAPI
- MySQL
- HTML, CSS and JavaScript
- Groq API
- LLM-based AI agents

## Project Structure
```text
SpendWise/
├── main.py
├── agent.py
├── database.py
├── requirements.txt
├── static/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── test_gemini.py
└── README.md
```

## How to Run

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies using `pip install -r requirements.txt`.
4. Create a `.env` file with your database credentials and Groq API key.
5. Run the application:

```bash
python -m uvicorn main:app --reload
```

6. Open `http://127.0.0.1:8000` in your browser.

## Note
This project was developed as an academic project to explore AI-powered personal expense management.