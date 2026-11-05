
import os
import json
from datetime import date
from decimal import Decimal

from dotenv import load_dotenv
from groq import Groq
from database import get_connection


# =====================================
# 1. AI CONNECTION
# =====================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("Groq API key not found in .env file")

client = Groq(api_key=api_key)

MODEL = "openai/gpt-oss-120b"


def ask_ai(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def parse_ai_json(response):
    response = response.strip()

    if response.startswith("```"):
        response = response.split("\n", 1)[1]
        response = response.rsplit("```", 1)[0]

    return json.loads(response)


# =====================================
# 2. EXPENSE MANAGEMENT AGENT
# =====================================

def get_all_expenses():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM expenses ORDER BY expense_date DESC"
        )
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def add_expense(title, amount, category, expense_date, description=None):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
        INSERT INTO expenses
        (title, amount, category, expense_date, description)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            title, amount, category, expense_date, description
        )

        cursor.execute(query, values)
        connection.commit()

        return {
            "message": "Expense added successfully!",
            "expense_id": cursor.lastrowid
        }

    finally:
        cursor.close()
        connection.close()


def edit_expense(expense_id, title, amount, category,
                 expense_date, description=None):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SELECT id FROM expenses WHERE id = %s",
            (expense_id,)
        )

        if cursor.fetchone() is None:
            return {"message": "Expense not found."}

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
            title, amount, category,
            expense_date, description, expense_id
        )

        cursor.execute(query, values)
        connection.commit()

        return {"message": "Expense updated successfully!"}

    finally:
        cursor.close()
        connection.close()


def delete_expense(expense_id):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM expenses WHERE id = %s",
            (expense_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:
            return {"message": "Expense not found."}

        return {"message": "Expense deleted successfully!"}

    finally:
        cursor.close()
        connection.close()


# =====================================
# 3. EXPENSE ANALYSIS AGENT
# =====================================

def get_monthly_spending():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
        SELECT COALESCE(SUM(amount), 0) AS monthly_total
        FROM expenses
        WHERE MONTH(expense_date) = MONTH(CURDATE())
        AND YEAR(expense_date) = YEAR(CURDATE())
        """

        cursor.execute(query)
        result = cursor.fetchone()

        return result["monthly_total"]

    finally:
        cursor.close()
        connection.close()


def get_category_spending():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
        SELECT category, SUM(amount) AS total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        """

        cursor.execute(query)
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


# =====================================
# 4. COORDINATOR AGENT
# =====================================

def coordinator_agent(user_message):

    prompt = f"""
    You are the Coordinator Agent of SpendWise.

    Classify the user's request into exactly one intent:

    add_expense
    view_expenses
    edit_expense
    delete_expense
    monthly_spending
    category_spending
    general_question

    Return ONLY a valid JSON object:
    {{"intent": "intent_name"}}

    User request: {user_message}
    """

    response = ask_ai(prompt)

    return parse_ai_json(response)


# =====================================
# 5. EXTRACT EXPENSE DETAILS
# =====================================

def extract_expense_details(user_message):

    today = date.today().isoformat()

    prompt = f"""
    Extract expense information from the user's message.

    Today's date is {today}.

    Return ONLY a JSON object containing:
    title, amount, category, expense_date, description.

    Use YYYY-MM-DD for expense_date.
    Use today's date when the user says today.
    Use null when a detail is missing.

    Allowed categories:
    Food, Travel, Shopping, Education,
    Entertainment, Other.

    User message: {user_message}
    """

    response = ask_ai(prompt)

    return parse_ai_json(response)


# =====================================
# 6. EXTRACT EDIT DETAILS
# =====================================

def extract_edit_details(user_message):

    expenses = get_all_expenses()

    prompt = f"""
    The user wants to edit an expense.

    Existing expenses:
    {json.dumps(expenses, default=str)}

    User request:
    {user_message}

    Identify the expense to edit using its ID.
    Extract the new details requested by the user.

    Return ONLY JSON in this format:
    {{
        "expense_id": null,
        "title": null,
        "amount": null,
        "category": null,
        "expense_date": null,
        "description": null
    }}

    Only provide a new value for fields the user wants to change.
    Keep all other fields null.
    Do not guess the expense ID.
    """

    response = ask_ai(prompt)

    return parse_ai_json(response)


# =====================================
# 7. EXECUTE USER REQUEST
# =====================================

def execute_request(user_message):

    result = coordinator_agent(user_message)
    intent = result.get("intent")

    # ADD EXPENSE
    if intent == "add_expense":

        details = extract_expense_details(user_message)

        required_fields = [
            "title", "amount", "category", "expense_date"
        ]

        if any(details.get(field) is None for field in required_fields):
            return {
                "message": "Please provide the expense name, amount, category and date."
            }

        try:
            amount = Decimal(str(details["amount"]))

            if amount <= 0:
                return {"message": "Expense amount must be greater than zero."}

            return add_expense(
                details["title"],
                amount,
                details["category"],
                details["expense_date"],
                details.get("description")
            )

        except (ValueError, TypeError):
            return {"message": "Please provide a valid expense amount."}

    # VIEW EXPENSES
    elif intent == "view_expenses":
        return get_all_expenses()

    # MONTHLY SPENDING
    elif intent == "monthly_spending":
        total = get_monthly_spending()
        return f"Your total spending this month is ₹{total}."

    # CATEGORY SPENDING
    elif intent == "category_spending":
        return get_category_spending()

    # DELETE EXPENSE
    elif intent == "delete_expense":

        expenses = get_all_expenses()

        prompt = f"""
        Existing expenses:
        {json.dumps(expenses, default=str)}

        User request:
        {user_message}

        Identify the exact expense the user wants to delete.

        Return ONLY JSON:
        {{"expense_id": null}}

        Use the existing ID.
        If the expense is ambiguous, return null.
        """

        details = parse_ai_json(ask_ai(prompt))
        expense_id = details.get("expense_id")

        if not isinstance(expense_id, int):
            return {"message": "Please specify which expense ID to delete."}

        return delete_expense(expense_id)

    # EDIT EXPENSE
    elif intent == "edit_expense":

        details = extract_edit_details(user_message)

        expense_id = details.get("expense_id")

        if not isinstance(expense_id, int):
            return {"message": "Please specify which expense you want to edit."}

        expenses = get_all_expenses()
        existing = next(
            (item for item in expenses if item["id"] == expense_id),
            None
        )

        if existing is None:
            return {"message": "Expense not found."}

        title = details.get("title") or existing["title"]
        amount = details.get("amount") or existing["amount"]
        category = details.get("category") or existing["category"]
        expense_date = details.get("expense_date") or existing["expense_date"]
        description = (
            details["description"]
            if details.get("description") is not None
            else existing["description"]
        )

        try:
            amount = Decimal(str(amount))

            if amount <= 0:
                return {"message": "Expense amount must be greater than zero."}

            return edit_expense(
                expense_id,
                title,
                amount,
                category,
                expense_date,
                description
            )

        except (ValueError, TypeError):
            return {"message": "Please provide valid expense details."}

    # GENERAL QUESTION
    elif intent == "general_question":
        return ask_ai(user_message)

    return {"message": "Sorry, I could not understand that request."}
