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
load_dotenv(override=True)

# Helper to save settings to .env
def save_settings_to_env(openai_key, openai_model, gmail_sender, gmail_pass, freelancer_name, freelancer_email, freelancer_bank):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")
    content = f"""OPENAI_API_KEY={openai_key}
OPENAI_MODEL={openai_model}
GMAIL_SENDER={gmail_sender}
GMAIL_APP_PASS={gmail_pass}
FREELANCER_NAME={freelancer_name}
FREELANCER_EMAIL={freelancer_email}
FREELANCER_BANK_DETAILS={freelancer_bank}
"""
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)
        # Reload env variables override
        load_dotenv(env_path, override=True)
        return True, "Settings saved successfully to .env!"
    except Exception as e:
        return False, f"Failed to save settings: {str(e)}"

# Set page configurations
st.set_page_config(
    page_title="Freelancer Admin Automation Assistant",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= CUSTOM TYPOGRAPHY & PROFESSIONAL THEME =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&family=Syne:wght@700;800&display=swap');

/* Dynamic zero-gravity space background with aurora-like loops */
html, body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 10% 20%, rgba(155, 93, 229, 0.12), transparent 45%),
                radial-gradient(circle at 90% 80%, rgba(0, 212, 255, 0.12), transparent 45%),
                linear-gradient(135deg, #020205 0%, #0a0a0f 60%, #0d0d1e 100%) !important;
    background-size: 200% 200% !important;
    animation: auroraShift 25s ease-in-out infinite alternate !important;
    font-family: 'Inter', sans-serif;
    color: #e2e8f0 !important;
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0) !important;
}

/* Floating nebulas behind cards */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    width: 350px;
    height: 350px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0, 212, 255, 0.08) 0%, transparent 70%);
    top: 15%;
    left: 8%;
    z-index: -1;
    animation: floatBob 14s ease-in-out infinite alternate;
    pointer-events: none;
}
[data-testid="stAppViewContainer"]::after {
    content: "";
    position: fixed;
    width: 450px;
    height: 450px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(155, 93, 229, 0.07) 0%, transparent 70%);
    bottom: 12%;
    right: 8%;
    z-index: -1;
    animation: floatBob 18s ease-in-out infinite alternate-reverse;
    pointer-events: none;
}

@keyframes auroraShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 50% 100%; }
}

/* Custom Space Typography */
h1, h2, h3, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.01em !important;
    color: #ffffff !important;
}
[data-testid="stMarkdownContainer"] h1 {
    font-size: 2.0rem !important;
    white-space: nowrap !important;
}
[data-testid="stMarkdownContainer"] h2 {
    font-size: 1.4rem !important;
    white-space: nowrap !important;
}
[data-testid="stMarkdownContainer"] h3 {
    font-size: 1.1rem !important;
    white-space: nowrap !important;
}

/* Completely hide Sidebar and Sidebar Toggle arrow button */
[data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display: none !important;
}

/* Style Streamlit Tabs to look like a premium glowing Navbar */
[data-testid="stTabBar"] {
    background: rgba(10, 10, 15, 0.45) !important;
    backdrop-filter: blur(12px) !important;
    border-radius: 30px !important;
    padding: 6px 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    box-shadow: 0 4px 25px rgba(0, 212, 255, 0.06) !important;
    margin-bottom: 25px !important;
    display: flex !important;
    justify-content: center !important;
}

[data-testid="stTabBar"] button {
    color: rgba(255, 255, 255, 0.7) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: all 0.25s ease !important;
    border-radius: 20px !important;
    border: none !important;
    background: transparent !important;
    padding: 8px 20px !important;
}

[data-testid="stTabBar"] button p {
    color: inherit !important;
}

[data-testid="stTabBar"] button:hover {
    color: #00d4ff !important;
    background: rgba(0, 212, 255, 0.08) !important;
}

[data-testid="stTabBar"] button[aria-selected="true"] {
    color: #ffffff !important;
    background: linear-gradient(135deg, #9b5de5, #4F46E5) !important;
    box-shadow: 0 0 15px rgba(155, 93, 229, 0.4) !important;
}

/* Hide default bottom red line indicator of Streamlit tabs */
[data-testid="stTabBar"] [data-baseweb="tab-highlight-bar"] {
    display: none !important;
}

/* Weightless float keyframes */
@keyframes floatBob {
    0% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-8px) rotate(0.5deg); }
    100% { transform: translateY(0px) rotate(0deg); }
}

@keyframes floatBobAlt {
    0% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-10px) rotate(-0.5deg); }
    100% { transform: translateY(0px) rotate(0deg); }
}

/* Card entry fade-in */
@keyframes fadeInEntry {
    from {
        opacity: 0;
        transform: translateY(16px) scale(0.98);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

/* Glassmorphism Bento-style Cards */
.proposal-card {
    border-left: 5px solid #9b5de5 !important; /* Neon Violet Accent */
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(16px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(140%) !important;
    color: #e2e8f0 !important;
    padding: 1.5rem;
    border-radius: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07) !important;
    box-shadow: 0 8px 32px 0 rgba(155, 93, 229, 0.06) !important;
    margin-bottom: 1.5rem;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    animation: floatBob 7s ease-in-out infinite, fadeInEntry 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.proposal-card p, .proposal-card b, .proposal-card strong, .proposal-card li, .proposal-card span:not([class^="badge-"]) {
    color: #e2e8f0 !important;
}
.proposal-card:hover {
    transform: translateY(-10px) scale(1.02) !important;
    box-shadow: 0 16px 40px 0 rgba(155, 93, 229, 0.18) !important;
    border-color: rgba(155, 93, 229, 0.4) !important;
}
.proposal-header {
    color: #9b5de5 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700;
    font-size: 1.35rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
    text-shadow: 0 0 10px rgba(155, 93, 229, 0.2);
}

.invoice-card {
    border-left: 5px solid #00d4ff !important; /* Electric Blue Accent */
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(16px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(140%) !important;
    color: #e2e8f0 !important;
    padding: 1.5rem;
    border-radius: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07) !important;
    box-shadow: 0 8px 32px 0 rgba(0, 212, 255, 0.06) !important;
    margin-bottom: 1.5rem;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    animation: floatBobAlt 8s ease-in-out infinite, fadeInEntry 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.invoice-card p, .invoice-card b, .invoice-card strong, .invoice-card li, .invoice-card span:not([class^="badge-"]) {
    color: #e2e8f0 !important;
}
.invoice-card:hover {
    transform: translateY(-10px) scale(1.02) !important;
    box-shadow: 0 16px 40px 0 rgba(0, 212, 255, 0.18) !important;
    border-color: rgba(0, 212, 255, 0.4) !important;
}
.invoice-header {
    color: #00d4ff !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700;
    font-size: 1.35rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
}

.reminder-card {
    border-left: 5px solid #ff007f !important; /* Neon Pink Accent */
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(16px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(140%) !important;
    color: #e2e8f0 !important;
    padding: 1.2rem;
    border-radius: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07) !important;
    box-shadow: 0 8px 32px 0 rgba(255, 0, 127, 0.06) !important;
    margin-bottom: 1.5rem;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    animation: floatBob 6s ease-in-out infinite, fadeInEntry 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.reminder-card p, .reminder-card b, .reminder-card strong, .reminder-card li, .reminder-card span:not([class^="badge-"]) {
    color: #e2e8f0 !important;
}
.reminder-card:hover {
    transform: translateY(-8px) scale(1.02) !important;
    box-shadow: 0 16px 40px 0 rgba(255, 0, 127, 0.18) !important;
    border-color: rgba(255, 0, 127, 0.4) !important;
}
.reminder-header {
    color: #ff007f !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700;
    font-size: 1.25rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0.5rem;
    margin-bottom: 0.75rem;
    text-shadow: 0 0 10px rgba(255, 0, 127, 0.2);
}

/* Badge status indicators */
.badge-paid {
    background-color: rgba(16, 185, 129, 0.12) !important;
    color: #10B981 !important;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid rgba(16, 185, 129, 0.25) !important;
}
.badge-unpaid {
    background-color: rgba(245, 158, 11, 0.12) !important;
    color: #F59E0B !important;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid rgba(245, 158, 11, 0.25) !important;
}
.badge-overdue {
    background-color: rgba(239, 68, 68, 0.12) !important;
    color: #EF4444 !important;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid rgba(239, 68, 68, 0.25) !important;
}

/* Futuristic Space Chat Bubbles */
.chat-bubble-user {
    background: linear-gradient(135deg, #9b5de5, #4F46E5) !important;
    color: #FFFFFF !important;
    padding: 0.85rem 1.1rem;
    border-radius: 16px 16px 0 16px;
    margin-bottom: 0.85rem;
    max-width: 80%;
    margin-left: auto;
    font-size: 0.95rem;
    box-shadow: 0 4px 15px rgba(155, 93, 229, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    animation: fadeInEntry 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.chat-bubble-user * {
    color: #FFFFFF !important;
}
.chat-bubble-assistant {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    color: #e2e8f0 !important;
    padding: 1.1rem 1.35rem;
    border-radius: 16px 16px 16px 0;
    margin-bottom: 0.85rem;
    max-width: 85%;
    margin-right: auto;
    font-size: 0.95rem;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    line-height: 1.55;
    animation: fadeInEntry 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.chat-bubble-assistant p, .chat-bubble-assistant b, .chat-bubble-assistant strong, .chat-bubble-assistant span, .chat-bubble-assistant li {
    color: #e2e8f0 !important;
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
if "active_proposal" not in st.session_state:
    st.session_state.active_proposal = None
if "active_invoice" not in st.session_state:
    st.session_state.active_invoice = None
if "active_reminder" not in st.session_state:
    st.session_state.active_reminder = None

# Database operation feedback message
if "db_action_msg" not in st.session_state:
    st.session_state.db_action_msg = None

# Startup connection check popup modal
if "startup_check_shown" not in st.session_state:
    st.session_state.startup_check_shown = False

if not st.session_state.startup_check_shown:
    openai_ok = bool(st.session_state.openai_api_key)
    gmail_ok = bool(st.session_state.gmail_sender and st.session_state.gmail_app_pass)
    
    openai_class = "status-connected" if openai_ok else "status-missing"
    openai_text = "Connected" if openai_ok else "Missing"
    
    gmail_class = "status-connected" if gmail_ok else "status-missing"
    gmail_text = "Connected" if gmail_ok else "Missing"
    
    st.markdown("""
    <style>
    /* Startup Modal Overlay */
    .startup-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(2, 2, 5, 0.85);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        z-index: 99999;
        display: flex;
        justify-content: center;
        align-items: center;
        animation: fadeInModal 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* Modal Content Card */
    .startup-modal-content {
        background: rgba(10, 10, 15, 0.7);
        border: 1px solid rgba(0, 212, 255, 0.15);
        box-shadow: 0 0 50px rgba(0, 212, 255, 0.15), inset 0 0 30px rgba(0, 212, 255, 0.05);
        border-radius: 20px;
        padding: 35px;
        width: 450px;
        max-width: 90%;
        position: relative;
        overflow: hidden;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
        animation: scaleInModal 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* Scanning line animation */
    .scanner-line {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, transparent, #00d4ff, transparent);
        animation: scanLine 3s linear infinite;
        opacity: 0.7;
    }

    @keyframes scanLine {
        0% { top: 0%; }
        50% { top: 100%; }
        100% { top: 0%; }
    }

    @keyframes fadeInModal {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes scaleInModal {
        from { transform: scale(0.9) translateY(20px); }
        to { transform: scale(1) translateY(0); }
    }

    /* Status Row */
    .status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .status-label {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.88rem;
        font-weight: 500;
        letter-spacing: 0.05em;
        color: #a0aec0;
    }

    .status-badge {
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .status-connected {
        background: rgba(16, 185, 129, 0.12) !important;
        color: #10B981 !important;
        border: 1px solid rgba(16, 185, 129, 0.25) !important;
        text-shadow: 0 0 8px rgba(16, 185, 129, 0.3);
    }

    .status-missing {
        background: rgba(239, 68, 68, 0.12) !important;
        color: #EF4444 !important;
        border: 1px solid rgba(239, 68, 68, 0.25) !important;
        text-shadow: 0 0 8px rgba(239, 68, 68, 0.3);
    }

    .startup-btn-container {
        position: fixed;
        top: 66%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 100000;
        width: 250px;
    }
    .startup-btn-container button {
        background: linear-gradient(135deg, #00d4ff, #9b5de5) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 10px 25px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: bold !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .startup-btn-container button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.5) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="startup-modal-overlay">
        <div class="startup-modal-content" style="padding-bottom: 90px;">
            <div class="scanner-line"></div>
            <h2 style="font-family: 'Space Grotesk', sans-serif; color: #00d4ff; text-align: center; margin-top: 0; text-shadow: 0 0 10px rgba(0, 212, 255, 0.4); font-size: 1.5rem;">
                SYSTEM BOOT SEQUENCE
            </h2>
            <p style="text-align: center; color: #8892b0; font-size: 0.85rem; margin-bottom: 25px;">
                Initializing LancerFlow Operations Orchestrator v1.0.0...
            </p>
            
            <div style="margin-bottom: 25px;">
                <div class="status-row">
                    <span class="status-label">OPENAI COGNITIVE ENGINE</span>
                    <span class="status-badge {openai_class}">{openai_text}</span>
                </div>
                <div class="status-row">
                    <span class="status-label">GMAIL SMTP DISPATCHER</span>
                    <span class="status-badge {gmail_class}">{gmail_text}</span>
                </div>
            </div>
            
            <div style="font-size: 0.8rem; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 8px; margin-bottom: 25px; line-height: 1.5; color: #a0aec0; font-family: monospace;">
                <span style="color: #9b5de5;">[SYS]</span> Gravitational compensators: ACTIVE<br/>
                <span style="color: #9b5de5;">[SYS]</span> Zero-gravity styling layer: ACTIVE<br/>
                <span style="color: #9b5de5;">[SYS]</span> Core database engine: ONLINE
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    btn_col_1, btn_col_2, btn_col_3 = st.columns([1, 1, 1])
    with btn_col_2:
        st.markdown('<div class="startup-btn-container">', unsafe_allow_html=True)
        if st.button("🚀 Enter Dashboard", key="close_startup_modal", use_container_width=True):
            st.session_state.startup_check_shown = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


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
            st.session_state.active_proposal = st.session_state.active_doc
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
            st.session_state.active_invoice = st.session_state.active_doc
            st.session_state.db_action_msg = f"📊 Created and compiled Invoice **{inv_number}** (Saved to DB)."
            
        elif action == "mark_invoice_paid":
            inv_id = command["invoice_id"]
            database.update_invoice_status(inv_id, "paid")
            st.session_state.db_action_msg = f"✅ Marked Invoice ID **{inv_id}** as **Paid**."
            
            # If current active document is this invoice, reset it
            if st.session_state.active_doc and st.session_state.active_doc.get("invoice_id") == inv_id:
                st.session_state.active_doc = None
            if st.session_state.active_invoice and st.session_state.active_invoice.get("invoice_id") == inv_id:
                st.session_state.active_invoice = None
            if st.session_state.active_reminder and st.session_state.active_reminder.get("invoice_id") == inv_id:
                st.session_state.active_reminder = None
                
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
            st.session_state.active_reminder = st.session_state.active_doc
            st.session_state.db_action_msg = f"✉️ Drafted payment reminder ({tone_tier} tone) for Invoice **{inv_num}**."
            
    except Exception as e:
        import traceback
        st.session_state.db_action_msg = f"❌ Error executing command: {str(e)}\n{traceback.format_exc()}"


# Sidebar completely removed


# ================= MAIN PAGE FULL-SCREEN LAYOUT =================
if os.path.exists("logo.jpg"):
    col_l, col_t = st.columns([0.15, 0.85])
    with col_l:
        st.image("logo.jpg", use_container_width=True)
    with col_t:
        st.title("LancerFlow Operations Orchestrator")
else:
    st.title("Freelancer Operations Orchestrator")

st.markdown("Manage your freelance administration conversationally. Select tabs from the navigation bar above to view live outputs.")

tab_chat, tab_proposal, tab_invoice, tab_reminder, tab_ledger = st.tabs([
    "💬 Chat Assistant",
    "📄 Proposals", 
    "💵 Invoices", 
    "✉️ Reminders",
    "🗄️ Relational Ledger"
])

# ================= TAB: CONVERSATIONAL CHATBOT =================
with tab_chat:
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
    
    with tab_chat:
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
                    response_text = "⚠️ **OpenAI API Key is missing.** Please configure it in the 'Credentials & Settings' expander in the sidebar to proceed."
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
import contextlib
with contextlib.nullcontext():
    
    # ---------------- TAB 1: PROPOSALS ----------------
    with tab_proposal:
        active_prop = st.session_state.active_proposal
        if not active_prop:
            st.markdown("""
            <div style='text-align: center; padding: 40px; color: #888;'>
                <h3>No Active Proposal Draft</h3>
                <p>Use the chatbot on the left to draft a proposal. It will compile PDF/DOCX templates automatically.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Render proposal preview (Navy Accent)
            st.markdown(f"""
            <div class="proposal-card">
                <div class="proposal-header">PROPOSAL PREVIEW: {active_prop['title']}</div>
                <p><b>Freelancer:</b> {st.session_state.freelancer_name} ({st.session_state.freelancer_email})</p>
                <p><b>Prepared For:</b> Client ID: {active_prop['client_id']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show Text markdown
            st.markdown(active_prop["text"])
            
            # Action Buttons
            st.write("---")
            target_email = st.text_input("Recipient Email Address", value=active_prop.get("client_email", ""), key="prop_email_target")
            
            col_d1, col_d2, col_mail = st.columns(3)
            
            if os.path.exists(active_prop["pdf_path"]):
                with open(active_prop["pdf_path"], "rb") as f:
                    col_d1.download_button(
                        label="📥 Download PDF",
                        data=f.read(),
                        file_name=f"Proposal_{active_prop['title'].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key="proposal_pdf_dl"
                    )
            if os.path.exists(active_prop["docx_path"]):
                with open(active_prop["docx_path"], "rb") as f:
                    col_d2.download_button(
                        label="📥 Download Word (.docx)",
                        data=f.read(),
                        file_name=f"Proposal_{active_prop['title'].replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="proposal_docx_dl"
                    )
                    
            # Email Sender Trigger
            if col_mail.button("✉️ Send via Gmail", key="send_prop_email", disabled=not target_email.strip()):
                with st.spinner("Dispatching proposal files..."):
                    subj = f"Project Proposal: {active_prop['title']}"
                    body = f"Hello,\n\nPlease find attached the project proposal for '{active_prop['title']}' compiled professionally.\n\nBest regards,\n{st.session_state.freelancer_name}"
                    attachments = [active_prop["pdf_path"], active_prop["docx_path"]]
                    
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

    # ---------------- TAB 2: INVOICES ----------------
    with tab_invoice:
        active_inv = st.session_state.active_invoice
        if not active_inv:
            st.markdown("""
            <div style='text-align: center; padding: 40px; color: #888;'>
                <h3>No Active Invoice Draft</h3>
                <p>Use the chatbot on the left to calculate and compile an invoice.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Render invoice preview (Burgundy Accent)
            st.markdown(f"""
            <div class="invoice-card">
                <div class="invoice-header">INVOICE PREVIEW: {active_inv['number']}</div>
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <b>Billed To:</b> {active_inv['client_name']}<br/>
                        <b>Email:</b> {active_inv['client_email']}<br/>
                        <b>Project:</b> {active_inv['project_name']}
                    </div>
                    <div style="text-align: right;">
                        <b>Due Date:</b> <span class="badge-overdue">{active_inv['due_date']}</span><br/>
                        <b>Freelancer:</b> {st.session_state.freelancer_name}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # HTML Table Render
            html_table = f"""
            <style>
            .invoice-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 0.95rem;
                color: var(--text-color, #1F2937);
            }}
            .invoice-table th {{
                background-color: #10B981;
                color: white;
                padding: 10px;
                border: 1px solid rgba(128, 128, 128, 0.2);
                text-align: left;
                font-weight: 600;
            }}
            .invoice-table td {{
                padding: 10px;
                border: 1px solid rgba(128, 128, 128, 0.2);
            }}
            .invoice-table tr:nth-child(even) {{
                background-color: rgba(128, 128, 128, 0.05);
            }}
            </style>
            <table class="invoice-table">
                <thead>
                    <tr>
                        <th>Work Description</th>
                        <th style="text-align: right;">Hours</th>
                        <th style="text-align: right;">Rate</th>
                        <th style="text-align: right;">Line Total</th>
                    </tr>
                </thead>
                <tbody>
            """
            for idx, item in enumerate(active_inv["work_items"]):
                hours = item.get("hours", 0)
                rate = item.get("rate", 0)
                total = hours * rate if hours > 0 else rate
                hours_lbl = f"{hours:.2f}" if hours > 0 else "Flat"
                html_table += f"""
                    <tr>
                        <td>{item.get('description', '')}</td>
                        <td style="text-align: right;">{hours_lbl}</td>
                        <td style="text-align: right;">${rate:.2f}</td>
                        <td style="text-align: right;">${total:.2f}</td>
                    </tr>
                """
            html_table += f"""
                </tbody>
            </table>
            """
            st.markdown(html_table, unsafe_allow_html=True)
            
            # Totals block
            st.markdown(f"""
            <div style="text-align: right; padding-right: 10px; margin-bottom: 20px; color: var(--text-color, #1F2937);">
                <p style="margin: 3px 0;">Subtotal: <b>${active_inv['subtotal']:.2f}</b></p>
                <p style="margin: 3px 0;">Tax ({active_inv['tax_percentage']}%): <b>${active_inv['tax_amount']:.2f}</b></p>
                <h3 style="color: #10B981; margin: 5px 0;">Grand Total: ${active_inv['grand_total']:.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Bank instructions lower panel
            st.markdown(f"""
            <div style="background-color: rgba(16, 185, 129, 0.08); border-left: 4px solid #10B981; padding: 12px 15px; border-radius: 4px; font-size: 0.88rem; margin-bottom: 20px; color: var(--text-color, #1F2937);">
                <b style="color: #10B981;">PAYMENT DETAILS:</b><br/>
                {st.session_state.freelancer_bank}
            </div>
            """, unsafe_allow_html=True)
            
            # Action Buttons
            st.write("---")
            target_email = st.text_input("Recipient Email Address", value=active_inv.get("client_email", ""), key="inv_email_target")
            
            col_d1, col_d2, col_mail = st.columns(3)
            
            if os.path.exists(active_inv["pdf_path"]):
                with open(active_inv["pdf_path"], "rb") as f:
                    col_d1.download_button(
                        label="📥 Download PDF",
                        data=f.read(),
                        file_name=f"Invoice_{active_inv['number']}.pdf",
                        mime="application/pdf",
                        key="invoice_pdf_dl"
                    )
            if os.path.exists(active_inv["docx_path"]):
                with open(active_inv["docx_path"], "rb") as f:
                    col_d2.download_button(
                        label="📥 Download Word (.docx)",
                        data=f.read(),
                        file_name=f"Invoice_{active_inv['number']}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="invoice_docx_dl"
                    )
                    
            # Email Sender Trigger
            if col_mail.button("✉️ Send via Gmail", key="send_inv_email", disabled=not target_email.strip()):
                with st.spinner("Dispatching invoice files..."):
                    subj = f"Invoice {active_inv['number']} from {st.session_state.freelancer_name}"
                    body = f"Dear Client,\n\nPlease find attached invoice {active_inv['number']} in the amount of ${active_inv['grand_total']:.2f}.\n\nPayment Details:\n{st.session_state.freelancer_bank}\n\nThank you,\n{st.session_state.freelancer_name}"
                    attachments = [active_inv["pdf_path"], active_inv["docx_path"]]
                    
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

    # ---------------- TAB 3: REMINDERS ----------------
    with tab_reminder:
        active_rem = st.session_state.active_reminder
        if not active_rem:
            st.markdown("""
            <div style='text-align: center; padding: 40px; color: #888;'>
                <h3>No Active Reminder Draft</h3>
                <p>Use the chatbot on the left to draft payment reminders for overdue accounts.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Render payment reminder text (Amber/Orange accent)
            st.markdown(f"""
            <div class="reminder-card">
                <div class="reminder-header">PAYMENT REMINDER EMAIL: TIER {active_rem['tone_tier'].upper()}</div>
                <p><b>To:</b> {active_rem['recipient_email']}</p>
                <p><b>Subject:</b> {active_rem['subject']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show drafted reminder body
            st.text_area("Email Draft Body", active_rem["text"], height=200, disabled=True)
            
            # Action Buttons
            st.write("---")
            target_email = st.text_input("Recipient Email Address", value=active_rem.get("recipient_email", ""), key="rem_email_target")
            
            col_back, col_send = st.columns([2, 1])
            
            # Send reminder email via Gmail
            if col_send.button("🚀 Send Email Now", key="send_reminder_email", disabled=not target_email.strip()):
                with st.spinner("Sending payment reminder..."):
                    attachments = []
                    if os.path.exists(active_rem["pdf_path"]):
                        attachments.append(active_rem["pdf_path"])
                        
                    success, log_msg = mailer.send_gmail(
                        recipient_email=target_email.strip(),
                        subject=active_rem["subject"],
                        body_text=active_rem["text"],
                        attachment_paths=attachments,
                        sender_email=st.session_state.gmail_sender,
                        app_password=st.session_state.gmail_app_pass
                    )
                    if success:
                        # Log the sent reminder in SQLite database
                        database.create_payment_reminder(
                            invoice_id=active_rem["invoice_id"],
                            recipient_email=target_email.strip(),
                            tone_tier=active_rem["tone_tier"]
                        )
                        st.success("Reminder email successfully sent!")
                        # Reset draft state
                        st.session_state.active_reminder = None
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
