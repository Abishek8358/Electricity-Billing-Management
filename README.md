# ⚡ Electricity Billing Management System

A modern, web-based Electricity Billing and Management System built with Python, Flask, and SQLite. The application simplifies user management, automated meter reading simulation, dynamic bill generation, online bill payments, PDF receipt generation, and a responsive customer complaint portal.

---

## 🚀 Live Demo & Deployment
This project is configured for **Vercel** serverless hosting using `vercel.json` with temporary file operations mapped to `/tmp` to bypass serverless read-only restrictions.

- **GitHub Repository**: [https://github.com/Abishek8358/Electricity-Billing-Management](https://github.com/Abishek8358/Electricity-Billing-Management)

---

## 🌟 Key Features

### 👨‍💼 Admin Panel
* **Customer Directory**: Add, update, view, and delete customers. Automatically registers user login credentials.
* **Meter Readings & Simulation**: Trigger virtual smart meters to simulate electricity consumption (in kWh) across all sections.
* **Smart Bill Generation**: Generate individual customer utility bills based on active meter readings using a flat rate pricing model.
* **Revenue Analytics**: Track paid bills and aggregate monthly revenue visualized via graphs.
* **Complaint Resolution**: View customer-submitted issues and update ticket statuses (`Open`, `In Progress`, `Closed`).

### 👤 Customer Portal
* **Dashboard Summary**: Real-time greetings, navigation, and overview.
* **Billing History**: View current, pending, and past utility bills.
* **Secure Payment & PDF Receipts**: Simulates payments for bills and generates dynamic PDF receipts using `reportlab` which are downloadable.
* **Support Ticket System**: Submit descriptions of utility issues, check real-time resolution status, and manage ticket history.

---

## 🛠️ Tech Stack
* **Backend**: Python (Flask)
* **Database**: SQLite3
* **PDF Engine**: ReportLab (Generates printable invoices on demand)
* **Frontend**: HTML5, Vanilla CSS, JavaScript
* **Deployment**: Vercel (Python serverless function runtime)

---

## 📁 Project Directory Structure
```text
Electricity-Billing-Management/
│
├── app.py                    # Flask server, database schema, and API endpoints
├── requirements.txt          # Python dependencies
├── vercel.json               # Serverless configuration for Vercel deployment
├── electricity.db            # SQLite database file (local only)
├── .gitignore                # Excludes virtual environments, database, and logs
│
└── templates/                # Web pages (HTML/CSS/JS)
    ├── login.html            # User authentication (bypassed in dev mode)
    ├── admin_dashboard.html  # Admin panel dashboard landing
    ├── admin_customers.html  # Customer directory management
    ├── admin_bills.html      # Meter readings and bill generation
    ├── admin_payments.html   # Payment auditing and revenue metrics
    ├── admin_complaints.html # Admin support ticketing system
    ├── user_dashboard.html   # Customer home portal
    ├── user_bills.html       # Customer bill viewing and payment page
    └── user_complaints.html  # Customer ticketing form and history
```

---

## 🔧 Installation & Local Setup

### Prerequisites
* Python 3.8+ installed on your system.

### Step-by-Step Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Abishek8358/Electricity-Billing-Management.git
   cd Electricity-Billing-Management
   ```

2. **Set up a Virtual Environment**:
   ```bash
   # On Windows
   python -m venv .venv
   .\.venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```
   The Flask application will start running at **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

---

## 🔒 Authentication Note
For rapid development, prototyping, and demonstration purposes, the login page is currently set to **bypass** mode.
* Opening the application home page will automatically log you in as the **Administrator (`admin`)** role and direct you straight to the admin control panel.
* If you want to log in manually, go to the `/login` route or disable the `@app.before_request` hook in `app.py`.

---

## ⚡ Deployment to Vercel
This repository is configured out-of-the-box for Vercel. 

To deploy:
1. Install the Vercel CLI: `npm install -g vercel`
2. Run `vercel` in the project root directory.
3. Follow the CLI prompt instructions.

*Note: Since Vercel's serverless environment has a read-only filesystem, the SQLite database is copied dynamically to the `/tmp` folder upon execution to allow write permissions. PDFs are generated and served from `/tmp` as well.*
