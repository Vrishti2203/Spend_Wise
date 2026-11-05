const API = "http://127.0.0.1:8000";

document.getElementById("expenseDate").value =
    new Date().toISOString().split("T")[0];

function showMessage(message, color) {
    const element = document.getElementById("message");
    element.textContent = message;
    element.style.color = color;
}

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}


// ADD EXPENSE
document.getElementById("expenseForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const expense = {
        title: document.getElementById("title").value.trim(),
        amount: Number(document.getElementById("amount").value),
        category: document.getElementById("category").value,
        expense_date: document.getElementById("expenseDate").value,
        description: document.getElementById("description").value
    };

    try {
        const response = await fetch(`${API}/expenses`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(expense)
        });

        const result = await response.json();

        if (!response.ok) throw new Error(result.detail || "Unable to add expense.");

        showMessage("Expense added successfully!", "green");

        document.getElementById("expenseForm").reset();
        document.getElementById("expenseDate").value =
            new Date().toISOString().split("T")[0];

        await refreshDashboard();

    } catch (error) {
        showMessage(error.message, "red");
    }
});


// VIEW EXPENSES
async function loadExpenses() {
    const container = document.getElementById("expenses");

    try {
        const response = await fetch(`${API}/expenses`);

        if (!response.ok) throw new Error("Unable to load expenses.");

        const expenses = await response.json();

        if (expenses.length === 0) {
            container.innerHTML = "<p>No expenses added yet.</p>";
            return;
        }

        container.innerHTML = expenses.map(expense => `
            <div class="expense-item">
                <div>
                    <h3>${escapeHTML(expense.title)}</h3>
                    <p>${escapeHTML(expense.category)} | ${escapeHTML(expense.expense_date)}</p>
                </div>

                <div>
                    <strong>₹${Number(expense.amount).toFixed(2)}</strong>

                    <div class="expense-actions">
                        <button class="edit-btn"
                            onclick="openEditForm(${Number(expense.id)})">
                            Edit
                        </button>

                        <button class="delete-btn"
                            onclick="deleteExpense(${Number(expense.id)})">
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        `).join("");

    } catch (error) {
        container.textContent = error.message;
    }
}


// OPEN EDIT FORM
async function openEditForm(id) {
    try {
        const response = await fetch(`${API}/expenses`);

        if (!response.ok) throw new Error("Unable to load expense.");

        const expenses = await response.json();
        const expense = expenses.find(item => item.id === id);

        if (!expense) {
            alert("Expense not found.");
            return;
        }

        document.getElementById("editId").value = expense.id;
        document.getElementById("editTitle").value = expense.title;
        document.getElementById("editAmount").value = expense.amount;
        document.getElementById("editCategory").value = expense.category;
        document.getElementById("editDate").value = expense.expense_date;
        document.getElementById("editDescription").value =
            expense.description || "";

        const editSection = document.getElementById("editSection");
        editSection.style.display = "block";
        editSection.scrollIntoView({ behavior: "smooth" });

    } catch (error) {
        alert(error.message);
    }
}


// SAVE EDITED EXPENSE
document.getElementById("editForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const id = document.getElementById("editId").value;

    const updatedExpense = {
        title: document.getElementById("editTitle").value.trim(),
        amount: Number(document.getElementById("editAmount").value),
        category: document.getElementById("editCategory").value,
        expense_date: document.getElementById("editDate").value,
        description: document.getElementById("editDescription").value
    };

    if (!updatedExpense.title || updatedExpense.amount <= 0) {
        alert("Please enter valid expense details.");
        return;
    }

    try {
        const response = await fetch(`${API}/expenses/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updatedExpense)
        });

        const result = await response.json();

        if (!response.ok) throw new Error(result.detail || "Unable to update expense.");

        alert("Expense updated successfully!");

        document.getElementById("editSection").style.display = "none";
        document.getElementById("editForm").reset();

        await refreshDashboard();

    } catch (error) {
        alert(error.message);
    }
});


// CANCEL EDIT
document.getElementById("cancelEdit").addEventListener("click", function() {
    document.getElementById("editSection").style.display = "none";
    document.getElementById("editForm").reset();
});


// DELETE EXPENSE
async function deleteExpense(id) {
    if (!confirm("Are you sure you want to delete this expense?")) return;

    try {
        const response = await fetch(`${API}/expenses/${id}`, {
            method: "DELETE"
        });

        const result = await response.json();

        if (!response.ok) throw new Error(result.detail || "Unable to delete expense.");

        await refreshDashboard();

    } catch (error) {
        alert(error.message);
    }
}


// MONTHLY SUMMARY
async function loadSummary() {
    try {
        const response = await fetch(`${API}/summary`);

        if (!response.ok) throw new Error("Unable to load summary.");

        const data = await response.json();

        document.getElementById("monthlyTotal").textContent =
            "₹" + Number(data.monthly_total).toFixed(2);

    } catch (error) {
        console.error(error);
    }
}


// AI CHAT DISPLAY
function addChatMessage(message, sender) {
    const container = document.getElementById("chatMessages");
    const messageElement = document.createElement("div");

    messageElement.className = `chat-message ${sender}`;

    // Use textContent so AI responses are displayed safely.
    if (typeof message === "string") {
        messageElement.textContent = message;
    } else {
        messageElement.textContent = JSON.stringify(message, null, 2);
    }

    container.appendChild(messageElement);
    container.scrollTop = container.scrollHeight;

    return messageElement;
}


// AI CHAT
document.getElementById("chatForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const input = document.getElementById("chatInput");
    const sendButton = document.getElementById("chatSend");

    const message = input.value.trim();

    if (!message) return;

    addChatMessage(message, "user");

    input.value = "";
    sendButton.disabled = true;
    sendButton.textContent = "Thinking...";

    const loadingMessage = addChatMessage("Please wait...", "assistant");

    try {
        const response = await fetch(`${API}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "AI assistant could not respond.");
        }

        loadingMessage.textContent =
            typeof result.reply === "string"
                ? result.reply
                : JSON.stringify(result.reply, null, 2);

        // Refresh the dashboard after an AI request because
        // the AI may have added, edited or deleted an expense.
        await refreshDashboard();

    } catch (error) {
        loadingMessage.textContent = "Error: " + error.message;

    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";
        input.focus();
    }
});


// REFRESH DASHBOARD
async function refreshDashboard() {
    await loadExpenses();
    await loadSummary();
}


// INITIAL LOAD
refreshDashboard();