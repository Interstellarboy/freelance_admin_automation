import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(__file__), "freelancer_admin.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database tables and seeds them with mock data if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Clients Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT NOT NULL,
        target_email TEXT NOT NULL,
        company_name TEXT NOT NULL,
        contact_details TEXT
    )
    """)
    
    # 2. Projects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        client_id INTEGER NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed')),
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )
    """)
    
    # 3. Proposals Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        project_id INTEGER,
        generated_text TEXT NOT NULL,
        created_timestamp TEXT NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients(id),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    """)
    
    # 4. Invoices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT NOT NULL UNIQUE,
        project_id INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        tax_percentage REAL DEFAULT 0,
        tax_amount REAL DEFAULT 0,
        grand_total REAL NOT NULL,
        due_date TEXT NOT NULL,
        created_date TEXT NOT NULL,
        status TEXT DEFAULT 'unpaid' CHECK(status IN ('unpaid', 'paid', 'overdue')),
        work_items_json TEXT NOT NULL, -- JSON formatted list of items
        freelancer_payment_details TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    """)
    
    # 5. Payment Reminders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payment_reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        recipient_email TEXT NOT NULL,
        tone_tier TEXT NOT NULL CHECK(tone_tier IN ('Gentle', 'Firm', 'Urgent')),
        sent_timestamp TEXT NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id)
    )
    """)
    
    conn.commit()
    
    # Seed data if empty
    cursor.execute("SELECT COUNT(*) FROM clients")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)
        
    conn.close()

def seed_data(conn):
    cursor = conn.cursor()
    today = datetime.now()
    
    # Clients
    clients = [
        ("Acme Corp", "acme.billing@example.com", "Acme Corporation", "+1-555-0199, 123 Main St, Tech City"),
        ("Stark Industries", "pepper.potts@stark.com", "Stark Industries Inc.", "+1-555-3000, 10880 Malibu Point, CA")
    ]
    cursor.executemany("""
    INSERT INTO clients (client_name, target_email, company_name, contact_details)
    VALUES (?, ?, ?, ?)
    """, clients)
    
    # Projects
    projects = [
        ("Website Redesign", 1, "Migrate client marketing page to a modern Next.js website with Tailwind CSS.", "active"),
        ("Arc Reactor Dashboard", 2, "Create a real-time dashboard for monitoring reactor temperatures.", "active"),
        ("Cybersecurity Audit", 2, "Audit legacy server firewalls and encryption mechanisms.", "completed")
    ]
    cursor.executemany("""
    INSERT INTO projects (project_name, client_id, description, status)
    VALUES (?, ?, ?, ?)
    """, projects)
    
    # Invoices
    # Invoice 1: INV-001, project 1, due in 7 days, unpaid
    inv1_created = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    inv1_due = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    inv1_items = json.dumps([
        {"description": "Initial Wireframing & UX Mockups", "hours": 10.0, "rate": 50.0},
        {"description": "React Components & Landing Page Implementation", "hours": 14.0, "rate": 50.0}
    ])
    
    # Invoice 2: INV-002, project 2, overdue by 10 days, unpaid
    inv2_created = (today - timedelta(days=25)).strftime("%Y-%m-%d")
    inv2_due = (today - timedelta(days=10)).strftime("%Y-%m-%d")
    inv2_items = json.dumps([
        {"description": "Backend Database & Streamlit Dashboard Setup", "hours": 30.0, "rate": 100.0}
    ])
    
    # Invoice 3: INV-003, project 3, overdue by 25 days, unpaid
    inv3_created = (today - timedelta(days=40)).strftime("%Y-%m-%d")
    inv3_due = (today - timedelta(days=25)).strftime("%Y-%m-%d")
    inv3_items = json.dumps([
        {"description": "Full-stack Security Penetration Testing", "hours": 45.0, "rate": 100.0}
    ])
    
    # Invoice 4: INV-004, project 1, paid
    inv4_created = (today - timedelta(days=20)).strftime("%Y-%m-%d")
    inv4_due = (today - timedelta(days=5)).strftime("%Y-%m-%d")
    inv4_items = json.dumps([
        {"description": "Initial Project Discovery Workshop", "hours": 16.0, "rate": 50.0}
    ])
    
    payment_details = "Bank of America, Account: XXXXX-12345, Routing: YYYYY-67890"
    
    invoices = [
        ("INV-001", 1, 1200.0, 10.0, 120.0, 1320.0, inv1_due, inv1_created, "unpaid", inv1_items, payment_details),
        ("INV-002", 2, 3000.0, 5.0, 150.0, 3150.0, inv2_due, inv2_created, "unpaid", inv2_items, payment_details),
        ("INV-003", 3, 4500.0, 0.0, 0.0, 4500.0, inv3_due, inv3_created, "unpaid", inv3_items, payment_details),
        ("INV-004", 1, 800.0, 10.0, 80.0, 880.0, inv4_due, inv4_created, "paid", inv4_items, payment_details),
    ]
    cursor.executemany("""
    INSERT INTO invoices (invoice_number, project_id, subtotal, tax_percentage, tax_amount, grand_total, due_date, created_date, status, work_items_json, freelancer_payment_details)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, invoices)
    
    conn.commit()

def sync_invoice_statuses():
    """Checks for invoices that are unpaid but past their due date, and marks them overdue."""
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
    UPDATE invoices
    SET status = 'overdue'
    WHERE status = 'unpaid' AND due_date < ?
    """, (today_str,))
    
    conn.commit()
    conn.close()

# ================= CLIENT CRUD =================

def create_client(client_name, target_email, company_name, contact_details=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO clients (client_name, target_email, company_name, contact_details)
    VALUES (?, ?, ?, ?)
    """, (client_name, target_email, company_name, contact_details))
    client_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return client_id

def get_clients():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients ORDER BY client_name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_client_by_id(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# ================= PROJECT CRUD =================

def create_project(project_name, client_id, description=None, status='active'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO projects (project_name, client_id, description, status)
    VALUES (?, ?, ?, ?)
    """, (project_name, client_id, description, status))
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id

def get_projects():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.*, c.client_name, c.company_name
    FROM projects p
    JOIN clients c ON p.client_id = c.id
    ORDER BY p.project_name
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_projects_by_client(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE client_id = ?", (client_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ================= PROPOSAL CRUD =================

def create_proposal(client_id, project_id, generated_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO proposals (client_id, project_id, generated_text, created_timestamp)
    VALUES (?, ?, ?, ?)
    """, (client_id, project_id, generated_text, timestamp_str))
    proposal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return proposal_id

def get_proposals():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT prop.*, c.client_name, p.project_name
    FROM proposals prop
    JOIN clients c ON prop.client_id = c.id
    LEFT JOIN projects p ON prop.project_id = p.id
    ORDER BY prop.created_timestamp DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_proposals_by_client(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proposals WHERE client_id = ? ORDER BY created_timestamp DESC", (client_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ================= INVOICE CRUD =================

def create_invoice(invoice_number, project_id, subtotal, tax_percentage, tax_amount, grand_total, due_date, work_items_list, freelancer_payment_details, status='unpaid'):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_date = datetime.now().strftime("%Y-%m-%d")
    
    # Store work items list as JSON string
    work_items_json = json.dumps(work_items_list)
    
    cursor.execute("""
    INSERT INTO invoices (invoice_number, project_id, subtotal, tax_percentage, tax_amount, grand_total, due_date, created_date, status, work_items_json, freelancer_payment_details)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (invoice_number, project_id, subtotal, tax_percentage, tax_amount, grand_total, due_date, created_date, status, work_items_json, freelancer_payment_details))
    invoice_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return invoice_id

def get_next_invoice_number():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT invoice_number FROM invoices ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return "INV-001"
    
    last_num_str = row['invoice_number']
    if last_num_str.startswith("INV-"):
        try:
            num = int(last_num_str[4:])
            return f"INV-{num + 1:03d}"
        except ValueError:
            pass
            
    return "INV-100" # Fallback if format is different

def get_invoices():
    sync_invoice_statuses()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT inv.*, p.project_name, c.client_name, c.target_email, c.company_name
    FROM invoices inv
    JOIN projects p ON inv.project_id = p.id
    JOIN clients c ON p.client_id = c.id
    ORDER BY inv.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_invoice_by_id(invoice_id):
    sync_invoice_statuses()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT inv.*, p.project_name, c.client_name, c.target_email, c.company_name
    FROM invoices inv
    JOIN projects p ON inv.project_id = p.id
    JOIN clients c ON p.client_id = c.id
    WHERE inv.id = ?
    """, (invoice_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        data = dict(row)
        data['work_items'] = json.loads(data['work_items_json'])
        return data
    return None

def get_invoice_by_number(invoice_number):
    sync_invoice_statuses()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT inv.*, p.project_name, c.client_name, c.target_email, c.company_name
    FROM invoices inv
    JOIN projects p ON inv.project_id = p.id
    JOIN clients c ON p.client_id = c.id
    WHERE inv.invoice_number = ?
    """, (invoice_number,))
    row = cursor.fetchone()
    conn.close()
    if row:
        data = dict(row)
        data['work_items'] = json.loads(data['work_items_json'])
        return data
    return None

def update_invoice_status(invoice_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (status, invoice_id))
    conn.commit()
    conn.close()

# ================= REMINDER CRUD =================

def create_payment_reminder(invoice_id, recipient_email, tone_tier):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO payment_reminders (invoice_id, recipient_email, tone_tier, sent_timestamp)
    VALUES (?, ?, ?, ?)
    """, (invoice_id, recipient_email, tone_tier, timestamp_str))
    reminder_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reminder_id

def get_reminders_by_invoice(invoice_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payment_reminders WHERE invoice_id = ? ORDER BY sent_timestamp DESC", (invoice_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ================= RELATIONAL SUMMARY LEDGER =================

def get_client_history(client_id):
    sync_invoice_statuses()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Client Info
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()
    if not client:
        conn.close()
        return None
        
    # Projects
    cursor.execute("SELECT * FROM projects WHERE client_id = ?", (client_id,))
    projects = [dict(r) for r in cursor.fetchall()]
    
    # Proposals
    cursor.execute("""
    SELECT prop.*, p.project_name
    FROM proposals prop
    LEFT JOIN projects p ON prop.project_id = p.id
    WHERE prop.client_id = ?
    ORDER BY prop.created_timestamp DESC
    """, (client_id,))
    proposals = [dict(r) for r in cursor.fetchall()]
    
    # Invoices
    cursor.execute("""
    SELECT inv.*, p.project_name
    FROM invoices inv
    JOIN projects p ON inv.project_id = p.id
    WHERE p.client_id = ?
    ORDER BY inv.created_date DESC
    """, (client_id,))
    invoices = []
    for r in cursor.fetchall():
        inv_dict = dict(r)
        inv_dict['work_items'] = json.loads(inv_dict['work_items_json'])
        invoices.append(inv_dict)
        
    # Reminders
    cursor.execute("""
    SELECT rem.*, inv.invoice_number, p.project_name
    FROM payment_reminders rem
    JOIN invoices inv ON rem.invoice_id = inv.id
    JOIN projects p ON inv.project_id = p.id
    WHERE p.client_id = ?
    ORDER BY rem.sent_timestamp DESC
    """, (client_id,))
    reminders = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "client": dict(client),
        "projects": projects,
        "proposals": proposals,
        "invoices": invoices,
        "reminders": reminders
    }

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
