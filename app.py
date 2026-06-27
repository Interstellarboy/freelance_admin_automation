import streamlit as st
import os
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Import backend modules
import database
import mailer
import doc_compiler

# Initialize SQLite database and seed data
database.init_db()

# Load env variables
load_dotenv()

# Set page configurations
st.set_page_config(
    page_title="Freelancer Admin Automation Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM TYPOGRAPHY & PROFESSIONAL THEME =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #F8F9FB;
    font-family: 'Inter', sans-serif;
    color: #2D3748;
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: #0F172A;
}
[data-testid="stSidebar"] .stMarkdown h1, 
[data-testid="stSidebar"] .stMarkdown h2, 
[data-testid="stSidebar"] .stMarkdown h3,
[data-testid="stSidebar"] label {
    color: #F1F5F9 !important;
    font-family: 'Outfit', sans-serif;
}

/* Card layout systems */
.proposal-card {
    border-left: 5px solid #1A2E40;
    background-color: #FFFFFF;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(26, 46, 64, 0.08);
    margin-bottom: 1.5rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.proposal-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(26, 46, 64, 0.12);
}
.proposal-header {
    color: #1A2E40;
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 1.35rem;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

.invoice-card {
    border-left: 5px solid #7A1C1C;
    background-color: #FFFFFF;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(122, 28, 28, 0.08);
    margin-bottom: 1.5rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.invoice-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(122, 28, 28, 0.12);
}
.invoice-header {
    color: #7A1C1C;
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 1.35rem;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

.reminder-card {
    border-left: 5px solid #D97706;
    background-color: #FFFBEB;
    padding: 1.2rem;
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(217, 119, 6, 0.05);
    margin-bottom: 1.5rem;
}
.reminder-header {
    color: #B45309;
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 1.25rem;
    border-bottom: 1px solid #FCD34D;
    padding-bottom: 0.5rem;
    margin-bottom: 0.75rem;
}

/* Badge status indicators */
.badge-paid {
    background-color: #DEF7EC;
    color: #03543F;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid #BCF0DA;
}
.badge-unpaid {
    background-color: #FEF3C7;
    color: #92400E;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid #FDE68A;
}
.badge-overdue {
    background-color: #FDE8E8;
    color: #9B1C1C;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid #FBD5D5;
}

/* Chat Bubbles */
.chat-bubble-user {
    background-color: #E2E8F0;
    color: #1A202C;
    padding: 0.75rem 1rem;
    border-radius: 12px 12px 0 12px;
    margin-bottom: 0.75rem;
    max-width: 80%;
    margin-left: auto;
    font-size: 0.95rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.chat-bubble-assistant {
    background-color: #FFFFFF;
    color: #2D3748;
    padding: 1rem 1.25rem;
    border-radius: 12px 12px 12px 0;
    margin-bottom: 0.75rem;
    max-width: 85%;
    margin-right: auto;
    font-size: 0.95rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.03);
    border: 1px solid #E2E8F0;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)


# ================= SESSION STATE INITIALIZATION =================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Hello! I am your Freelance Admin Assistant. I can help you manage clients, draft proposals, create invoices, track overdue accounts, and send payment reminders via Gmail.\n\nWhat are we working on today?"}
    ]

# Credentials State
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
if "openai_model" not in st.session_state:
    st.session_state.openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
if "gmail_sender" not in st.session_state:
    st.session_state.gmail_sender = os.environ.get("GMAIL_SENDER", "")
if "gmail_app_pass" not in st.session_state:
    st.session_state.gmail_app_pass = os.environ.get("GMAIL_APP_PASS", "")

# Freelancer Business Defaults
if "freelancer_name" not in st.session_state:
    st.session_state.freelancer_name = os.environ.get("FREELANCER_NAME", "Alex Morgan")
if "freelancer_email" not in st.session_state:
    st.session_state.freelancer_email = os.environ.get("FREELANCER_EMAIL", "alex.morgan@gmail.com")
if "freelancer_bank" not in st.session_state:
    st.session_state.freelancer_bank = os.environ.get("FREELANCER_BANK_DETAILS", "Chase Bank, Acc: XXXXX-12345, Route: YYYYY-67890")

# Active Draft Canvas state
if "active_doc" not in st.session_state:
    st.session_state.active_doc = None  # None or Dict with 'type', 'title'/'number', 'text'/'items'

# Database operation feedback message
if "db_action_msg" not in st.session_state:
    st.session_state.db_action_msg = None


# ================= RULE-BASE MARKDOWN INJECTORS =================
def load_workspace_skills():
    """Reads all markdown skill configuration rules from the workspace root."""
    skills = {}
    skill_files = {
        "chat_interface": "chat-interface-skill.md",
        "proposal_generator": "proposal-generator-skill.md",
        "invoice_generator": "invoice-generator-skill.md",
        "payment_reminder": "payment-reminder-skill.md",
        "data_management": "data-management-skill.md",
        "document_generation": "document-generation-skill.md"
    }
    
    # Workspace root directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    for key, filename in skill_files.items():
        path = os.path.join(base_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    skills[key] = f.read()
            except Exception as e:
                skills[key] = f"Error reading {filename}: {str(e)}"
        else:
            skills[key] = f"Skill file {filename} not found in workspace root."
            
    return skills


# ================= ACTION DISPATCHER & RELATIONAL UPDATER =================
def execute_system_action(command):
    """Executes database mutations or state updates based on structured JSON from LLM."""
    action = command.get("action")
    if not action:
        return
        
    try:
        if action == "create_client":
            client_id = database.create_client(
                client_name=command["client_name"],
                target_email=command["target_email"],
                company_name=command["company_name"],
                contact_details=command.get("contact_details", "")
            )
            st.session_state.db_action_msg = f"✅ Created new client **{command['client_name']}** (ID: {client_id}) in SQLite."
            
        elif action == "create_project":
            project_id = database.create_project(
                project_name=command["project_name"],
                client_id=command["client_id"],
                description=command.get("description", ""),
                status=command.get("status", "active")
            )
            st.session_state.db_action_msg = f"✅ Created new project **{command['project_name']}** (ID: {project_id}) for Client ID: {command['client_id']}."
            
        elif action == "draft_proposal":
            client_id = command["client_id"]
            project_id = command.get("project_id")
            title = command["project_title"]
            text = command["proposal_text"]
            
            # If client_id is not a digit or is a string, resolve it by name
            if isinstance(client_id, str) and not str(client_id).isdigit():
                all_clients = database.get_clients()
                matched = None
                for c in all_clients:
                    if c["client_name"].lower() == client_id.lower() or c["company_name"].lower() == client_id.lower():
                        matched = c
                        break
                if matched:
                    client_id = matched["id"]
                else:
                    # If not matched, auto-create the client (like Masai School)
                    client_id = database.create_client(client_id, "info@masaischool.com", client_id, "Masai School contact details")
            else:
                client_id = int(client_id)
                
            # Fetch client details
            client_info = database.get_client_by_id(client_id)
            client_name = client_info["client_name"] if client_info else "Client"
            
            # Resolve project_id if it's a string name
            if project_id and isinstance(project_id, str) and not str(project_id).isdigit():
                all_projects = database.get_projects()
                matched_p = next((p for p in all_projects if p["project_name"].lower() == project_id.lower()), None)
                if matched_p:
                    project_id = matched_p["id"]
                else:
                    # Create project if not exists
                    project_id = database.create_project(title, client_id, "Auto-created project")
            elif project_id:
                project_id = int(project_id)
            
            # Save proposal to SQLite database
            prop_id = database.create_proposal(client_id, project_id, text)
            
            # Save paths for compiled documents
            base_dir = os.path.dirname(os.path.abspath(__file__))
            pdf_path = os.path.join(base_dir, "active_proposal.pdf")
            docx_path = os.path.join(base_dir, "active_proposal.docx")
            
            # Run compilers
            doc_compiler.compile_proposal_pdf(
                pdf_path, client_name, title, text, 
                st.session_state.freelancer_name, st.session_state.freelancer_email, st.session_state.freelancer_bank
            )
            doc_compiler.compile_proposal_docx(
                docx_path, client_name, title, text, 
                st.session_state.freelancer_name, st.session_state.freelancer_email, st.session_state.freelancer_bank
            )
            
            # Set UI active document state
            st.session_state.active_doc = {
                "type": "proposal",
                "client_id": client_id,
                "project_id": project_id,
                "title": title,
                "text": text,
                "pdf_path": pdf_path,
                "docx_path": docx_path,
                "client_email": client_info["target_email"] if client_info else "",
                "proposal_id": prop_id
            }
            st.session_state.db_action_msg = f"📝 Drafted and compiled proposal for **{title}** (Saved to DB)."
            
        elif action == "draft_invoice":
            project_id = command["project_id"]
            inv_number = command.get("invoice_number") or database.get_next_invoice_number()
            work_items = command["work_items"]
            tax_percentage = float(command.get("tax_percentage", 0.0))
            due_date = command["due_date"]
            
            # Compute financials
            subtotal = sum(float(item.get("hours", 0.0)) * float(item.get("rate", 0.0)) if float(item.get("hours", 0.0)) > 0 else float(item.get("rate", 0.0)) for item in work_items)
            tax_amount = subtotal * (tax_percentage / 100.0)
            grand_total = subtotal + tax_amount
            
            # Fetch project and client details
            projects = database.get_projects()
            
            # Resolve project_id by name if string
            if isinstance(project_id, str) and not str(project_id).isdigit():
                proj = next((p for p in projects if p["project_name"].lower() == project_id.lower()), None)
                if proj:
                    project_id = proj["id"]
            else:
                project_id = int(project_id)
                
            proj = next((p for p in projects if p["id"] == project_id), None)
            if not proj:
                st.session_state.db_action_msg = f"❌ Error: Project ID {project_id} not found."
                return
                
            client_id = proj["client_id"]
            client_info = database.get_client_by_id(client_id)
            
            # Create in SQLite database
            inv_id = database.create_invoice(
                invoice_number=inv_number,
                project_id=project_id,
                subtotal=subtotal,
                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                grand_total=grand_total,
                due_date=due_date,
                work_items_list=work_items,
                freelancer_payment_details=st.session_state.freelancer_bank,
                status="unpaid"
            )
            
            # Setup compiled document files
            base_dir = os.path.dirname(os.path.abspath(__file__))
            pdf_path = os.path.join(base_dir, "active_invoice.pdf")
            docx_path = os.path.join(base_dir, "active_invoice.docx")
            
            doc_compiler.compile_invoice_pdf(
                pdf_path, inv_number, datetime.now().strftime("%Y-%m-%d"), due_date,
                client_info, proj["project_name"], work_items, subtotal, tax_percentage, tax_amount, grand_total,
                st.session_state.freelancer_bank, st.session_state.freelancer_name, st.session_state.freelancer_email
            )
            doc_compiler.compile_invoice_docx(
                docx_path, inv_number, datetime.now().strftime("%Y-%m-%d"), due_date,
                client_info, proj["project_name"], work_items, subtotal, tax_percentage, tax_amount, grand_total,
                st.session_state.freelancer_bank, st.session_state.freelancer_name, st.session_state.freelancer_email
            )
            
            st.session_state.active_doc = {
                "type": "invoice",
                "invoice_id": inv_id,
                "number": inv_number,
                "client_name": client_info["client_name"] if client_info else "",
                "client_email": client_info["target_email"] if client_info else "",
                "project_name": proj["project_name"],
                "work_items": work_items,
                "subtotal": subtotal,
                "tax_percentage": tax_percentage,
                "tax_amount": tax_amount,
                "grand_total": grand_total,
                "due_date": due_date,
                "pdf_path": pdf_path,
                "docx_path": docx_path
            }
            st.session_state.db_action_msg = f"📊 Created and compiled Invoice **{inv_number}** (Saved to DB)."
            
        elif action == "mark_invoice_paid":
            inv_id = command["invoice_id"]
            database.update_invoice_status(inv_id, "paid")
            st.session_state.db_action_msg = f"✅ Marked Invoice ID **{inv_id}** as **Paid**."
            
            # If current active document is this invoice, reset it
            if st.session_state.active_doc and st.session_state.active_doc.get("invoice_id") == inv_id:
                st.session_state.active_doc = None
                
        elif action == "draft_reminder":
            invoice_id = command["invoice_id"]
            recipient_email = command["recipient_email"]
            tone_tier = command["tone_tier"]
            subject = command["subject"]
            body = command["body"]
            
            # Query invoice number
            inv = database.get_invoice_by_id(invoice_id)
            inv_num = inv["invoice_number"] if inv else f"ID {invoice_id}"
            
            st.session_state.active_doc = {
                "type": "reminder",
                "invoice_id": invoice_id,
                "invoice_number": inv_num,
                "recipient_email": recipient_email,
                "tone_tier": tone_tier,
                "subject": subject,
                "text": body,
                # Reminders can attach the overdue invoice PDF if it exists
                "pdf_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "active_invoice.pdf")
            }
            st.session_state.db_action_msg = f"✉️ Drafted payment reminder ({tone_tier} tone) for Invoice **{inv_num}**."
            
    except Exception as e:
        import traceback
        st.session_state.db_action_msg = f"❌ Error executing command: {str(e)}\n{traceback.format_exc()}"


# ================= SIDEBAR LAYOUT (SETTINGS & STATUS) =================
if os.path.exists("masaiboyz.png"):
    st.sidebar.image("masaiboyz.png", width=120)
else:
    st.sidebar.title("🧙‍♂️ Admin Automator")

with st.sidebar:
    
    st.markdown("---")
    
    # Simple Status Summary
    st.subheader("Invoice Ledger Summary")
    invoices = database.get_invoices()
    unpaid_count = sum(1 for i in invoices if i["status"] == "unpaid")
    overdue_count = sum(1 for i in invoices if i["status"] == "overdue")
    paid_count = sum(1 for i in invoices if i["status"] == "paid")
    
    col_u, col_o, col_p = st.columns(3)
    col_u.metric("Unpaid", unpaid_count)
    col_o.metric("Overdue", overdue_count, delta_color="inverse")
    col_p.metric("Paid", paid_count)
    
    st.markdown("---")
    
    # Active Workspace Skills Visual Indicator
    st.subheader("Loaded Skill Modules")
    skills = load_workspace_skills()
    for name, skill_content in skills.items():
        if "Error" in skill_content or "not found" in skill_content:
            st.markdown(f"🔴 **{name.replace('_', ' ').title()}** (Missing)")
        else:
            st.markdown(f"🟢 **{name.replace('_', ' ').title()}** (Injected)")
            
    st.markdown("---")
    st.info("💡 Try asking me to: \n- *'Create a proposal for Stark Industries'*\n- *'Generate invoice INV-002 for project Website Redesign'*\n- *'Review overdue accounts and draft payment reminders'*\n- *'Mark invoice INV-003 as paid'*")


# ================= MAIN PAGE SPLIT-SCREEN LAYOUT =================
st.title("Freelancer Operations Orchestrator")
st.markdown("Manage your freelance administration conversationally. View real-time results in the live layout panel.")

col_chat, col_canvas = st.columns([1, 1])

# ================= LEFT COLUMN: CONVERSATIONAL CHATBOT =================
with col_chat:
    st.subheader("Administrative Chat Interface")
    
    # Render system mutation message if present
    if st.session_state.db_action_msg:
        st.info(st.session_state.db_action_msg)
        st.session_state.db_action_msg = None
        
    # Render chat messages
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                # Strip out the raw JSON block when rendering in chat log
                clean_content = re.sub(r'```json\s*(.*?)\s*```', '', msg["content"], flags=re.DOTALL).strip()
                st.markdown(f'<div class="chat-bubble-assistant">{clean_content}</div>', unsafe_allow_html=True)
                
    # Chat input
    user_input = st.chat_input("Enter your request here...")
    
    if user_input:
        # Show user message in chat
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.rerun()

# Run OpenAI generation if last message is from user
if st.session_state.chat_history[-1]["role"] == "user":
    user_msg = st.session_state.chat_history[-1]["content"]
    
    with col_chat:
        # Processing spinner
        with st.spinner("AI Agent processing rules and executing ledger transactions..."):
            try:
                # Load skills dynamically
                skills = load_workspace_skills()
                
                # Retrieve current database states for grounding
                clients_list = database.get_clients()
                projects_list = database.get_projects()
                invoices_list = database.get_invoices()
                
                # Format system instructions incorporating rules
                system_prompt = f"""You are the Principal Full-Stack Engineer and Python Architect persona. You act as the Core Conversational Orchestrator for the Freelancer Admin Automation suite.
Your goal is to conversationally guide the freelancer, maintain state, extract missing parameters, and update the ledger.

---
INJECTED WORKSPACE BEHAVIOR SKILLS:
1. Chat Interface rules:
{skills.get('chat_interface', 'No file content')}

2. Proposal generation rules:
{skills.get('proposal_generator', 'No file content')}

3. Invoice calculation rules:
{skills.get('invoice_generator', 'No file content')}

4. Payment reminder tones & structures:
{skills.get('payment_reminder', 'No file content')}

5. Client Ledger & SQL Database mappings:
{skills.get('data_management', 'No file content')}

6. PDF/DOCX layouts & style constraints:
{skills.get('document_generation', 'No file content')}

---
CURRENT PERSISTENT SQLITE DATABASE STATE:
Clients (IDs, names, email, company):
{json.dumps(clients_list, indent=2)}

Projects (ID, name, client_id, description, status):
{json.dumps(projects_list, indent=2)}

Invoices (ID, number, project_id, subtotal, grand_total, due_date, status, items):
{json.dumps(invoices_list, indent=2)}

---
ACTION TRIGGER RULES:
To trigger actions, update the database, create proposal/invoice files, or queue emails, append a JSON block inside a ```json ``` code fence at the very end of your response.
Only return ONE action JSON block per turn if needed.
Action structures:
- Create client:
  ```json
  {{"action": "create_client", "client_name": "Name", "target_email": "billing@company.com", "company_name": "Stark Industries", "contact_details": "+1-555-9000"}}
  ```
- Create project:
  ```json
  {{"action": "create_project", "project_name": "Project Name", "client_id": 1, "description": "Details", "status": "active"}}
  ```
- Draft and compile Proposal:
  ```json
  {{"action": "draft_proposal", "client_id": 1, "project_id": 1, "project_title": "Project Title", "proposal_text": "Markdown of full proposal text with ### sections."}}
  ```
- Draft and compile Invoice:
  ```json
  {{"action": "draft_invoice", "project_id": 1, "invoice_number": "INV-005", "work_items": [{{"description": "Design phase", "hours": 10, "rate": 50}}], "tax_percentage": 10.0, "due_date": "YYYY-MM-DD"}}
  ```
- Update status to Paid:
  ```json
  {{"action": "mark_invoice_paid", "invoice_id": 1}}
  ```
- Draft Payment Reminder Email (will display in canvas preview for manual execution):
  ```json
  {{"action": "draft_reminder", "invoice_id": 1, "recipient_email": "pepper.potts@stark.com", "tone_tier": "Gentle", "subject": "Friendly Invoice Reminder INV-002", "body": "Dear Pepper Potts,\\n\\nI hope you are doing well..."}}
  ```
"""
                # Compile messages history
                messages = [{"role": "system", "content": system_prompt}]
                
                # Keep history short or relevant
                for msg in st.session_state.chat_history[-10:-1]: # exclude the latest user message which we append next
                    # Clean out raw JSON block to prevent the LLM from getting confused by its own previous output commands
                    role = msg["role"]
                    content = msg["content"]
                    if role == "assistant":
                        content = re.sub(r'```json\s*(.*?)\s*```', '', content, flags=re.DOTALL).strip()
                    messages.append({"role": role, "content": content})
                    
                messages.append({"role": "user", "content": user_msg})
                
                # Check API Key
                api_key = st.session_state.openai_api_key
                if not api_key:
                    response_text = "⚠️ **OpenAI API Key is missing.** Please configure it in the 'Credentials & Settings' tab in the right panel to proceed."
                else:
                    client = OpenAI(api_key=api_key)
                    completion = client.chat.completions.create(
                        model=st.session_state.openai_model,
                        messages=messages,
                        temperature=0.7
                    )
                    response_text = completion.choices[0].message.content
                    
                # Append assistant reply
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                
                # Parse for JSON action block
                match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
                if match:
                    try:
                        cmd = json.loads(match.group(1).strip())
                        execute_system_action(cmd)
                    except Exception as parse_err:
                        st.session_state.db_action_msg = f"❌ Parsing error on command: {str(parse_err)}"
                        
                st.rerun()
                
            except Exception as e:
                import traceback
                err_text = f"An error occurred: {str(e)}\n\nCheck your connection or API key settings."
                st.session_state.chat_history.append({"role": "assistant", "content": err_text})
                st.error(traceback.format_exc())
                st.rerun()


# ================= RIGHT COLUMN: INTERACTIVE CANVAS & LEDGERS =================
with col_canvas:
    st.subheader("Live Ledger & Compiler Canvas")
    
    tab_preview, tab_ledger, tab_settings = st.tabs([
        "📄 Document Canvas", 
        "🗄️ Relational Ledger", 
        "⚙️ Credentials & Settings"
    ])
    
    # ---------------- TAB 1: LIVE DOCUMENT CANVAS PREVIEW ----------------
    with tab_preview:
        active = st.session_state.active_doc
        if not active:
            st.markdown("""
            <div style='text-align: center; padding: 40px; color: #888;'>
                <h3>No Active Draft Selected</h3>
                <p>Use the chatbot on the left to draft proposals, calculate invoices, or design payment reminders.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            if active["type"] == "proposal":
                # Render proposal preview (Navy Accent)
                st.markdown(f"""
                <div class="proposal-card">
                    <div class="proposal-header">PROPOSAL PREVIEW: {active['title']}</div>
                    <p><b>Freelancer:</b> {st.session_state.freelancer_name} ({st.session_state.freelancer_email})</p>
                    <p><b>Prepared For:</b> Client ID: {active['client_id']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show Text markdown
                st.markdown(active["text"])
                
                # Action Buttons
                st.write("---")
                target_email = st.text_input("Recipient Email Address", value=active.get("client_email", ""), key="prop_email_target")
                
                col_d1, col_d2, col_mail = st.columns(3)
                
                if os.path.exists(active["pdf_path"]):
                    with open(active["pdf_path"], "rb") as f:
                        col_d1.download_button(
                            label="📥 Download PDF",
                            data=f.read(),
                            file_name=f"Proposal_{active['title'].replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            key="proposal_pdf_dl"
                        )
                if os.path.exists(active["docx_path"]):
                    with open(active["docx_path"], "rb") as f:
                        col_d2.download_button(
                            label="📥 Download Word (.docx)",
                            data=f.read(),
                            file_name=f"Proposal_{active['title'].replace(' ', '_')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="proposal_docx_dl"
                        )
                        
                # Email Sender Trigger
                if col_mail.button("✉️ Send via Gmail", key="send_prop_email", disabled=not target_email.strip()):
                    with st.spinner("Dispatching proposal files..."):
                        subj = f"Project Proposal: {active['title']}"
                        body = f"Hello,\n\nPlease find attached the project proposal for '{active['title']}' compiled professionally.\n\nBest regards,\n{st.session_state.freelancer_name}"
                        attachments = [active["pdf_path"], active["docx_path"]]
                        
                        success, log_msg = mailer.send_gmail(
                            recipient_email=target_email.strip(),
                            subject=subj,
                            body_text=body,
                            attachment_paths=attachments,
                            sender_email=st.session_state.gmail_sender,
                            app_password=st.session_state.gmail_app_pass
                        )
                        if success:
                            st.success(f"Email sent successfully to {target_email.strip()}!")
                        else:
                            st.error(f"Failed to dispatch: {log_msg}")
                            
            elif active["type"] == "invoice":
                # Render invoice preview (Burgundy Accent)
                st.markdown(f"""
                <div class="invoice-card">
                    <div class="invoice-header">INVOICE PREVIEW: {active['number']}</div>
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <b>Billed To:</b> {active['client_name']}<br/>
                            <b>Email:</b> {active['client_email']}<br/>
                            <b>Project:</b> {active['project_name']}
                        </div>
                        <div style="text-align: right;">
                            <b>Due Date:</b> <span class="badge-overdue">{active['due_date']}</span><br/>
                            <b>Freelancer:</b> {st.session_state.freelancer_name}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # HTML Table Render
                html_table = f"""
                <table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 0.95rem;">
                    <thead>
                        <tr style="background-color: #7A1C1C; color: white; text-align: left; font-weight: bold;">
                            <th style="padding: 10px; border: 1px solid #E2E8F0;">Work Description</th>
                            <th style="padding: 10px; border: 1px solid #E2E8F0; text-align: right;">Hours</th>
                            <th style="padding: 10px; border: 1px solid #E2E8F0; text-align: right;">Rate</th>
                            <th style="padding: 10px; border: 1px solid #E2E8F0; text-align: right;">Line Total</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for idx, item in enumerate(active["work_items"]):
                    bg = "#FDF8F8" if idx % 2 == 0 else "#F5EBEB"
                    hours = item.get("hours", 0)
                    rate = item.get("rate", 0)
                    total = hours * rate if hours > 0 else rate
                    hours_lbl = f"{hours:.2f}" if hours > 0 else "Flat"
                    html_table += f"""
                        <tr style="background-color: {bg};">
                            <td style="padding: 8px 10px; border: 1px solid #E2E8F0;">{item.get('description', '')}</td>
                            <td style="padding: 8px 10px; border: 1px solid #E2E8F0; text-align: right;">{hours_lbl}</td>
                            <td style="padding: 8px 10px; border: 1px solid #E2E8F0; text-align: right;">${rate:.2f}</td>
                            <td style="padding: 8px 10px; border: 1px solid #E2E8F0; text-align: right;">${total:.2f}</td>
                        </tr>
                    """
                html_table += f"""
                    </tbody>
                </table>
                """
                st.markdown(html_table, unsafe_allow_html=True)
                
                # Totals block
                st.markdown(f"""
                <div style="text-align: right; padding-right: 10px; margin-bottom: 20px;">
                    <p style="margin: 3px 0;">Subtotal: <b>${active['subtotal']:.2f}</b></p>
                    <p style="margin: 3px 0;">Tax ({active['tax_percentage']}%): <b>${active['tax_amount']:.2f}</b></p>
                    <h3 style="color: #7A1C1C; margin: 5px 0;">Grand Total: ${active['grand_total']:.2f}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Bank instructions lower panel
                st.markdown(f"""
                <div style="background-color: #FDF8F8; border-left: 4px solid #7A1C1C; padding: 10px 15px; border-radius: 4px; font-size: 0.85rem; margin-bottom: 20px;">
                    <b style="color: #7A1C1C;">PAYMENT DETAILS:</b><br/>
                    {st.session_state.freelancer_bank}
                </div>
                """, unsafe_allow_html=True)
                
                # Action Buttons
                st.write("---")
                target_email = st.text_input("Recipient Email Address", value=active.get("client_email", ""), key="inv_email_target")
                
                col_d1, col_d2, col_mail = st.columns(3)
                
                if os.path.exists(active["pdf_path"]):
                    with open(active["pdf_path"], "rb") as f:
                        col_d1.download_button(
                            label="📥 Download PDF",
                            data=f.read(),
                            file_name=f"Invoice_{active['number']}.pdf",
                            mime="application/pdf",
                            key="invoice_pdf_dl"
                        )
                if os.path.exists(active["docx_path"]):
                    with open(active["docx_path"], "rb") as f:
                        col_d2.download_button(
                            label="📥 Download Word (.docx)",
                            data=f.read(),
                            file_name=f"Invoice_{active['number']}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="invoice_docx_dl"
                        )
                        
                # Email Sender Trigger
                if col_mail.button("✉️ Send via Gmail", key="send_inv_email", disabled=not target_email.strip()):
                    with st.spinner("Dispatching invoice files..."):
                        subj = f"Invoice {active['number']} from {st.session_state.freelancer_name}"
                        body = f"Dear Client,\n\nPlease find attached invoice {active['number']} in the amount of ${active['grand_total']:.2f}.\n\nPayment Details:\n{st.session_state.freelancer_bank}\n\nThank you,\n{st.session_state.freelancer_name}"
                        attachments = [active["pdf_path"], active["docx_path"]]
                        
                        success, log_msg = mailer.send_gmail(
                            recipient_email=target_email.strip(),
                            subject=subj,
                            body_text=body,
                            attachment_paths=attachments,
                            sender_email=st.session_state.gmail_sender,
                            app_password=st.session_state.gmail_app_pass
                        )
                        if success:
                            st.success(f"Email sent successfully to {target_email.strip()}!")
                        else:
                            st.error(f"Failed to dispatch: {log_msg}")
                            
            elif active["type"] == "reminder":
                # Render payment reminder text (Amber/Orange accent)
                st.markdown(f"""
                <div class="reminder-card">
                    <div class="reminder-header">PAYMENT REMINDER EMAIL: TIER {active['tone_tier'].upper()}</div>
                    <p><b>To:</b> {active['recipient_email']}</p>
                    <p><b>Subject:</b> {active['subject']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show drafted reminder body
                st.text_area("Email Draft Body", active["text"], height=200, disabled=True)
                
                # Action Buttons
                st.write("---")
                target_email = st.text_input("Recipient Email Address", value=active.get("recipient_email", ""), key="rem_email_target")
                
                col_back, col_send = st.columns([2, 1])
                
                # Send reminder email via Gmail
                if col_send.button("🚀 Send Email Now", key="send_reminder_email", disabled=not target_email.strip()):
                    with st.spinner("Sending payment reminder..."):
                        attachments = []
                        if os.path.exists(active["pdf_path"]):
                            attachments.append(active["pdf_path"])
                            
                        success, log_msg = mailer.send_gmail(
                            recipient_email=target_email.strip(),
                            subject=active["subject"],
                            body_text=active["text"],
                            attachment_paths=attachments,
                            sender_email=st.session_state.gmail_sender,
                            app_password=st.session_state.gmail_app_pass
                        )
                        if success:
                            # Log the sent reminder in SQLite database
                            database.create_payment_reminder(
                                invoice_id=active["invoice_id"],
                                recipient_email=target_email.strip(),
                                tone_tier=active["tone_tier"]
                            )
                            st.success("Reminder email successfully sent!")
                            # Reset draft state
                            st.session_state.active_doc = None
                        else:
                            st.error(f"Email dispatch failed: {log_msg}")

    # ---------------- TAB 2: RELATIONAL DATABASE SUMMARY VIEW ----------------
    with tab_ledger:
        st.subheader("Local Client & Invoice Ledgers")
        
        # Action selector
        view_mode = st.radio("Choose Ledger View", ["Clients & Projects", "All Invoices"], horizontal=True)
        
        if view_mode == "Clients & Projects":
            clients_data = database.get_clients()
            if not clients_data:
                st.write("No clients registered.")
            for c in clients_data:
                # Expander for each client details
                with st.expander(f"📁 {c['client_name']} ({c['company_name']})"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Email:** {c['target_email']}")
                        st.write(f"**Contact Details:** {c['contact_details']}")
                    with col2:
                        # Quick history summaries
                        hist = database.get_client_history(c["id"])
                        if hist:
                            st.write(f"**Projects:** {len(hist['projects'])}")
                            st.write(f"**Proposals:** {len(hist['proposals'])}")
                            st.write(f"**Invoices:** {len(hist['invoices'])}")
                            
                    # List projects for this client
                    proj_list = database.get_projects_by_client(c["id"])
                    if proj_list:
                        st.markdown("**Projects:**")
                        for p in proj_list:
                            status_ico = "🟢" if p["status"] == "active" else "🔴"
                            st.write(f"- {status_ico} {p['project_name']} (Status: {p['status']})")
                            
        elif view_mode == "All Invoices":
            inv_data = database.get_invoices()
            if not inv_data:
                st.write("No invoices recorded.")
            else:
                # Display invoice items in a styled layout
                for inv in inv_data:
                    status = inv["status"]
                    if status == "paid":
                        badge_html = '<span class="badge-paid">Paid</span>'
                    elif status == "overdue":
                        badge_html = '<span class="badge-overdue">Overdue</span>'
                    else:
                        badge_html = '<span class="badge-unpaid">Unpaid</span>'
                        
                    with st.container(border=True):
                        col_num, col_proj, col_tot, col_due, col_stat = st.columns([1, 2, 1, 1.5, 1])
                        col_num.markdown(f"**{inv['invoice_number']}**")
                        col_proj.write(f"{inv['project_name']} ({inv['client_name']})")
                        col_tot.write(f"${inv['grand_total']:.2f}")
                        col_due.write(f"Due: {inv['due_date']}")
                        col_stat.markdown(badge_html, unsafe_allow_html=True)
                        
                        # Add dynamic mark-as-paid button
                        if status != "paid":
                            if st.button("Mark Paid", key=f"btn_pay_{inv['id']}"):
                                database.update_invoice_status(inv["id"], "paid")
                                st.success(f"Invoice {inv['invoice_number']} marked as Paid.")
                                st.rerun()

    # ---------------- TAB 3: CREDENTIALS & SETTINGS ----------------
    with tab_settings:
        st.subheader("System Credentials")
        
        # OpenAI Config
        st.session_state.openai_api_key = st.text_input("OpenAI API Key", st.session_state.openai_api_key, type="password")
        st.session_state.openai_model = st.text_input("OpenAI Model", st.session_state.openai_model)
        
        st.subheader("Gmail Mailer Credentials")
        st.session_state.gmail_sender = st.text_input("Gmail Sender Address", st.session_state.gmail_sender)
        st.session_state.gmail_app_pass = st.text_input("Gmail App Password (16 chars)", st.session_state.gmail_app_pass, type="password")
        
        st.subheader("Freelancer Invoice Defaults")
        st.session_state.freelancer_name = st.text_input("Freelancer Business Name", st.session_state.freelancer_name)
        st.session_state.freelancer_email = st.text_input("Freelancer Contact Email", st.session_state.freelancer_email)
        st.session_state.freelancer_bank = st.text_area("Freelancer Payment (Bank) Info", st.session_state.freelancer_bank, height=80)
        
        st.info("💡 Note: Credentials are saved within the active browser session state and fall back to the `.env` settings if available.")
