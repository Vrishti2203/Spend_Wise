
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from database import get_connection
from datetime import date
from typing import Optional
from pathlib import Path
from agent import execute_request


# Initialize FastAPI
app = FastAPI(title="SpendWise - Expense Tracker")


# Project folder location
BASE_DIR = Path(__file__).resolve().parent


# Connect static files
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)


# Allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Expense data format
class Expense(BaseModel):
    title: str
    amount: float
    category: str
    expense_date: date
    description: Optional[str] = None


# Home route
@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


# ADD EXPENSE
@app.post("/expenses")
def add_expense(expense: Expense):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
        INSERT INTO expenses
        (title, amount, category, expense_date, description)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            expense.title,
            expense.amount,
            expense.category,
            expense.expense_date,
            expense.description
        )

        cursor.execute(query, values)
        connection.commit()

        return {
            "message": "Expense added successfully!",
            "expense_id": cursor.lastrowid
        }

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        connection.close()


# VIEW ALL EXPENSES
@app.get("/expenses")
def get_expenses():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM expenses ORDER BY expense_date DESC"
        )

        expenses = cursor.fetchall()

        for expense in expenses:
            expense["amount"] = float(expense["amount"])
            expense["expense_date"] = str(expense["expense_date"])
            expense["created_at"] = str(expense["created_at"])

        return expenses

    finally:
        cursor.close()
        connection.close()


# EDIT / UPDATE EXPENSE
@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, expense: Expense):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
        UPDATE expenses
        SET title = %s,
            amount = %s,
            category = %s,
            expense_date = %s,
            description = %s
        WHERE id = %s
        """

        values = (
            expense.title,
            expense.amount,
            expense.category,
            expense.expense_date,
            expense.description,
            expense_id
        )

        cursor.execute(query, values)

        if cursor.rowcount == 0:
            connection.rollback()
            raise HTTPException(
                status_code=404,
                detail="Expense not found"
            )

        connection.commit()

        return {
            "message": "Expense updated successfully!"
        }

    except HTTPException:
        raise

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        connection.close()


# DELETE EXPENSE
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM expenses WHERE id = %s",
            (expense_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Expense not found"
            )

        connection.commit()

        return {
            "message": "Expense deleted successfully!"
        }

    except HTTPException:
        raise

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        connection.close()


# MONTHLY SPENDING SUMMARY
@app.get("/summary")
def get_summary():

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE YEAR(expense_date) = YEAR(CURDATE())
            AND MONTH(expense_date) = MONTH(CURDATE())
        """)

        total = cursor.fetchone()[0]

        return {
            "monthly_total": float(total)
        }

    finally:
        cursor.close()
        connection.close()

        # AI CHAT REQUEST
class ChatRequest(BaseModel):
    message: str


# AI CHAT ENDPOINT
@app.post("/chat")
def chat_with_ai(request: ChatRequest):

    try:
        result = execute_request(request.message)

        return {
            "reply": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
