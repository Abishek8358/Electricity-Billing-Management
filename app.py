from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file
import sqlite3
import random
from datetime import datetime
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key in production


# Bypass login for development
@app.before_request
def auto_login():
    if 'role' not in session:
        session['user_id'] = 1
        session['role'] = 'admin'
        session['customer_id'] = None

# Initialize SQLite database

def init_db():
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,  -- 'admin' or 'customer'
        customer_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        address TEXT,
        section TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS meters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        section TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meter_id INTEGER,
        reading REAL,
        date TEXT,
        FOREIGN KEY (meter_id) REFERENCES meters(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meter_id INTEGER,
        amount REAL,
        date TEXT,
        paid BOOLEAN,
        FOREIGN KEY (meter_id) REFERENCES meters(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        description TEXT,
        status TEXT,
        date TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )''')
    # Insert default admin
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', 'admin123', 'admin'))
    conn.commit()
    conn.close()

# Simulate automatic meter reading
def simulate_meter_reading(meter_id):
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    reading = random.uniform(50, 500)  # kWh
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO readings (meter_id, reading, date) VALUES (?, ?, ?)", (meter_id, reading, date))
    conn.commit()
    conn.close()
    return reading

# Generate bill based on latest reading, only if no unpaid bill exists
def generate_bill(meter_id):
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    # Check for existing unpaid bill
    c.execute("SELECT id FROM bills WHERE meter_id = ? AND paid = ?", (meter_id, False))
    existing_bill = c.fetchone()
    if existing_bill:
        conn.close()
        return None  # Skip if unpaid bill exists
    # Get latest reading
    c.execute("SELECT reading FROM readings WHERE meter_id = ? ORDER BY date DESC LIMIT 1", (meter_id,))
    reading = c.fetchone()
    if reading:
        amount = reading[0] * 0.15  # $0.15 per kWh
        date = datetime.now().strftime('%Y-%m-%d')
        c.execute("INSERT INTO bills (meter_id, amount, date, paid) VALUES (?, ?, ?, ?)", (meter_id, amount, date, False))
        conn.commit()
        bill_id = c.lastrowid
        conn.close()
        return {"bill_id": bill_id, "amount": amount, "date": date}
    conn.close()
    return None

# Generate PDF receipt using reportlab
def generate_receipt(bill_id, customer_id, amount, date):
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    c.execute("SELECT c.name, c.email, m.section FROM customers c JOIN meters m ON c.id = m.customer_id JOIN bills b ON m.id = b.meter_id WHERE b.id = ?", (bill_id,))
    customer = c.fetchone()
    conn.close()
    
    if not customer:
        return None
    
    name, email, section = customer
    receipt_id = str(uuid.uuid4())
    receipt_file = f"receipt_{bill_id}.pdf"
    
    # Create PDF
    c = canvas.Canvas(receipt_file, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(300, 750, "Electricity Bill Receipt")
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"Receipt ID: {receipt_id}")
    c.drawString(50, 680, f"Date: {date}")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 640, "Customer Details")
    c.setFont("Helvetica", 12)
    c.drawString(50, 620, f"Name: {name}")
    c.drawString(50, 600, f"Email: {email}")
    c.drawString(50, 580, f"Section: {section}")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 540, "Payment Details")
    c.setFont("Helvetica", 12)
    c.drawString(50, 520, f"Bill ID: {bill_id}")
    c.drawString(50, 500, f"Amount Paid: ₹{amount:.2f}")
    c.drawString(50, 480, f"Payment Date: {datetime.now().strftime('%Y-%m-%d')}")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(300, 440, "Thank you for your payment!")
    
    c.showPage()
    c.save()
    
    return receipt_file


@app.route('/')
def home():
    return redirect(url_for('admin_dashboard'))

# Login route (kept for reference but bypassed)
@app.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('admin_dashboard'))

# Admin default route (redirect to dashboard)
@app.route('/admin')
def admin():
    if 'role' in session and session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

# Admin: Dashboard page
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html')
    return redirect(url_for('login'))

# Admin: Customers page
@app.route('/admin/customers')
def admin_customers():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_customers.html')
    return redirect(url_for('login'))

# Admin: Bills page
@app.route('/admin/bills')
def admin_bills():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_bills.html')
    return redirect(url_for('login'))

# Admin: Payments page
@app.route('/admin/payments')
def admin_payments():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_payments.html')
    return redirect(url_for('login'))

# Admin: Complaints page
@app.route('/admin/complaints')
def admin_complaints():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_complaints.html')
    return redirect(url_for('login'))

# User: Dashboard page
@app.route('/user')
def user():
    if 'role' in session and session['role'] == 'customer':
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/user/dashboard')
def user_dashboard():
    if 'role' in session and session['role'] == 'customer':
        return render_template('user_dashboard.html')
    return redirect(url_for('login'))

# User: Bills page
@app.route('/user/bills')
def user_bills():
    if 'role' in session and session['role'] == 'customer':
        return render_template('user_bills.html')
    return redirect(url_for('login'))

# User: Complaints page
@app.route('/user/complaints')
def user_complaints():
    if 'role' in session and session['role'] == 'customer':
        return render_template('user_complaints.html')
    return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Admin: Manage customers
@app.route('/api/admin/customers', methods=['GET', 'POST'])
def manage_customers():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    if request.method == 'POST':
        data = request.json
        password = data.get('password', 'password123')  # Allow custom password
        c.execute("INSERT INTO customers (name, email, address, section) VALUES (?, ?, ?, ?)",
                  (data['name'], data['email'], data['address'], data['section']))
        customer_id = c.lastrowid
        c.execute("INSERT INTO meters (customer_id, section) VALUES (?, ?)", (customer_id, data['section']))
        c.execute("INSERT INTO users (username, password, role, customer_id) VALUES (?, ?, ?, ?)",
                  (data['email'], password, 'customer', customer_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Customer added", "customer_id": customer_id})
    c.execute("SELECT * FROM customers")
    customers = [{"id": row[0], "name": row[1], "email": row[2], "address": row[3], "section": row[4]} for row in c.fetchall()]
    conn.close()
    return jsonify(customers)

# Admin: Update customer
@app.route('/api/admin/customers/<int:customer_id>', methods=['PUT', 'DELETE'])
def update_delete_customer(customer_id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    if request.method == 'PUT':
        data = request.json
        # Validate required fields
        if not all([data.get('name'), data.get('email'), data.get('address'), data.get('section')]):
            return jsonify({"error": "Missing required fields"}), 400
        # Check if email is unique (excluding the current customer)
        c.execute("SELECT id FROM customers WHERE email = ? AND id != ?", (data['email'], customer_id))
        if c.fetchone():
            conn.close()
            return jsonify({"error": "Email already exists"}), 400
        # Update customer
        c.execute("UPDATE customers SET name = ?, email = ?, address = ?, section = ? WHERE id = ?",
                  (data['name'], data['email'], data['address'], data['section'], customer_id))
        # Update associated meter section
        c.execute("UPDATE meters SET section = ? WHERE customer_id = ?", (data['section'], customer_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Customer updated"})
    else:  # DELETE
        # Delete associated records
        c.execute("DELETE FROM users WHERE customer_id = ?", (customer_id,))
        c.execute("DELETE FROM meters WHERE customer_id = ?", (customer_id,))
        c.execute("DELETE FROM complaints WHERE customer_id = ?", (customer_id,))
        c.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Customer deleted"})

# Admin: Get readings
@app.route('/api/admin/readings', methods=['GET'])
def admin_readings():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    c.execute("SELECT r.id, r.meter_id, r.reading, r.date, m.section FROM readings r JOIN meters m ON r.meter_id = m.id")
    readings = [{"id": row[0], "meter_id": row[1], "reading": row[2], "date": row[3], "section": row[4]} for row in c.fetchall()]
    conn.close()
    return jsonify(readings)

# Admin: Simulate readings
@app.route('/api/admin/simulate_readings', methods=['POST'])
def simulate_readings():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    c.execute("SELECT id FROM meters")
    meters = [row[0] for row in c.fetchall()]
    conn.close()
    readings = []
    for meter_id in meters:
        reading = simulate_meter_reading(meter_id)
        readings.append({"meter_id": meter_id, "reading": reading})
    return jsonify(readings)

# Admin/User: Manage bills
@app.route('/api/bills', methods=['GET', 'POST'])
def manage_bills():
    if 'role' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    if request.method == 'POST':
        if session['role'] != 'admin':
            return jsonify({"error": "Unauthorized"}), 401
        meter_id = request.json['meter_id']
        bill = generate_bill(meter_id)
        return jsonify(bill if bill else {"message": "No new bill generated (unpaid bill exists or no readings)"})
    if session['role'] == 'admin':
        c.execute("SELECT b.id, b.meter_id, b.amount, b.date, b.paid, m.section FROM bills b JOIN meters m ON b.meter_id = m.id")
    else:
        c.execute("SELECT b.id, b.meter_id, b.amount, b.date, b.paid, m.section FROM bills b JOIN meters m ON b.meter_id = m.id JOIN customers c ON m.customer_id = c.id WHERE c.id = ?",
                  (session['customer_id'],))
    bills = [{"id": row[0], "meter_id": row[1], "amount": row[2], "date": row[3], "paid": row[4], "section": row[5]} for row in c.fetchall()]
    conn.close()
    return jsonify(bills)

# Admin: Update or delete bill
@app.route('/api/bills/<int:bill_id>', methods=['PUT', 'DELETE'])
def update_delete_bill(bill_id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    if request.method == 'PUT':
        data = request.json
        amount = data.get('amount')
        if not amount or amount <= 0:
            conn.close()
            return jsonify({"error": "Invalid amount"}), 400
        c.execute("UPDATE bills SET amount = ? WHERE id = ?", (amount, bill_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Bill updated"})
    else:  # DELETE
        c.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Bill deleted"})

# Admin: Get monthly revenue
@app.route('/api/admin/revenue', methods=['GET'])
def get_monthly_revenue():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    # Group paid bills by month and year, sum the amounts
    c.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as revenue
        FROM bills
        WHERE paid = ?
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month
    """, (True,))
    revenue_data = c.fetchall()
    conn.close()
    
    # Format data for chart: { labels: ["2025-01", "2025-02", ...], data: [revenue1, revenue2, ...] }
    labels = [row[0] for row in revenue_data]
    data = [float(row[1]) for row in revenue_data]
    return jsonify({"labels": labels, "data": data})

# User: Pay bill
@app.route('/api/pay/<int:bill_id>', methods=['POST'])
def pay_bill(bill_id):
    if 'role' not in session or session['role'] != 'customer':
        return jsonify({"error": "Unauthorized"}), 401

    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()

    # Get bill info
    c.execute("SELECT meter_id, amount, date, paid FROM bills WHERE id = ?", (bill_id,))
    bill = c.fetchone()
    if not bill:
        conn.close()
        return jsonify({"error": "Bill not found"}), 404
    
    meter_id, amount, date, paid = bill
    if paid:
        conn.close()
        return jsonify({"message": "Bill already paid"}), 400

    # Verify bill belongs to logged-in customer
    c.execute("SELECT customer_id FROM meters WHERE id = ?", (meter_id,))
    meter_customer_id = c.fetchone()
    if not meter_customer_id or meter_customer_id[0] != session.get('customer_id'):
        conn.close()
        return jsonify({"error": "Unauthorized to pay this bill"}), 403

    # Mark bill as paid
    c.execute("UPDATE bills SET paid = ? WHERE id = ?", (True, bill_id))
    conn.commit()

    # Generate receipt PDF
    receipt_file = generate_receipt(bill_id, meter_customer_id[0], amount, date)

    conn.close()

    if receipt_file:
        # You could send the file URL or a link here, or just acknowledge payment success.
        return jsonify({"message": "Bill paid successfully", "receipt": receipt_file})
    else:
        return jsonify({"message": "Bill paid successfully, but receipt generation failed"})

    # Generate receipt
    receipt_file = generate_receipt(bill_id, customer_id, amount, date)
    if receipt_file and os.path.exists(receipt_file):
        return jsonify({"message": "Bill paid", "receipt": receipt_file})
    return jsonify({"message": "Bill paid, receipt generation failed"})


# User: Download receipt
@app.route('/api/receipt/<filename>')
def download_receipt(filename):
    if 'role' not in session or session['role'] != 'customer':
        return jsonify({"error": "Unauthorized"}), 401
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    return jsonify({"error": "Receipt not found"}), 404
# User: Submit complaint
@app.route('/api/complaints', methods=['POST'])
def submit_complaint():
    if 'role' not in session or session['role'] != 'customer':
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO complaints (customer_id, description, status, date) VALUES (?, ?, ?, ?)",
              (session['customer_id'], data['description'], 'Open', date))
    conn.commit()
    conn.close()
    return jsonify({"message": "Complaint submitted"})

# User: Get user details (for welcome message)
@app.route('/api/user/details', methods=['GET'])
def get_user_details():
    if 'role' not in session or session['role'] != 'customer':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    c.execute("SELECT name FROM customers WHERE id = ?", (session['customer_id'],))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({"name": user[0]})
    return jsonify({"error": "User not found"}), 404

# User: Get complaints
@app.route('/api/user/complaints', methods=['GET'])
def get_user_complaints():
    if 'role' not in session or session['role'] != 'customer':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    c.execute("SELECT id, description, status, date FROM complaints WHERE customer_id = ?", (session['customer_id'],))
    complaints = [{"id": row[0], "description": row[1], "status": row[2], "date": row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(complaints)

# User: Delete complaint
@app.route('/api/user/complaints/<int:complaint_id>', methods=['DELETE'])
def delete_user_complaint(complaint_id):
    if 'role' not in session or session['role'] != 'customer':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    c.execute("SELECT customer_id FROM complaints WHERE id = ?", (complaint_id,))
    complaint = c.fetchone()
    if not complaint or complaint[0] != session['customer_id']:
        conn.close()
        return jsonify({"error": "Unauthorized or complaint not found"}), 401
    c.execute("DELETE FROM complaints WHERE id = ?", (complaint_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Complaint deleted"})

# Admin: Manage complaints
@app.route('/api/admin/complaints', methods=['GET', 'POST'])
def manage_complaints():
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    if request.method == 'POST':
        data = request.json
        c.execute("UPDATE complaints SET status = ? WHERE id = ?", (data['status'], data['id']))
        conn.commit()
        conn.close()
        return jsonify({"message": "Complaint status updated"})
    c.execute("SELECT c.id, c.customer_id, c.description, c.status, c.date, cu.name FROM complaints c JOIN customers cu ON c.customer_id = cu.id")
    complaints = [{"id": row[0], "customer_id": row[1], "description": row[2], "status": row[3], "date": row[4], "customer_name": row[5]} for row in c.fetchall()]
    conn.close()
    return jsonify(complaints)

# Admin: Update or delete complaint
@app.route('/api/admin/complaints/<int:complaint_id>', methods=['PUT', 'DELETE'])
def update_delete_complaint(complaint_id):
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect('electricity.db')
    c = conn.cursor()
    if request.method == 'PUT':
        data = request.json
        status = data.get('status')
        if status not in ['Open', 'In Progress', 'Closed']:
            conn.close()
            return jsonify({"error": "Invalid status"}), 400
        c.execute("UPDATE complaints SET status = ? WHERE id = ?", (status, complaint_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Complaint updated"})
    else:  # DELETE
        c.execute("DELETE FROM complaints WHERE id = ?", (complaint_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Complaint deleted"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)