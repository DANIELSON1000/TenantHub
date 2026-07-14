import streamlit as st
import pandas as pd
import io
import os
import json
from datetime import datetime, timedelta
import hashlib
import base64

# Try to import reportlab, fallback to simple text if not available
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    st.warning("📄 ReportLab not installed. Using simple text agreement format.")

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="TenantHub - Property Management",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== BLUE BACKGROUND CUSTOM CSS ====================
st.markdown("""
<style>
    /* Main background - Deep Blue */
    .stApp {
        background: linear-gradient(135deg, #0C2461 0%, #1B3A7A 30%, #2A5298 60%, #4A90D9 100%);
        min-height: 100vh;
    }
    
    /* Main content area */
    .main-content {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1B3A7A 0%, #4A90D9 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(26, 67, 113, 0.4);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.8rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        color: #FFFFFF !important;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
        font-size: 1.2rem;
        color: #E8F4FD !important;
    }
    
    /* Reminder card */
    .reminder-card {
        background: linear-gradient(135deg, #FFF3CD, #FFEAA7);
        border-left: 5px solid #F39C12;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        animation: pulse 2s infinite;
    }
    .reminder-card.urgent {
        background: linear-gradient(135deg, #FADBD8, #F5B7B1);
        border-left-color: #E74C3C;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.01); }
        100% { transform: scale(1); }
    }
    
    /* Cards */
    .dashboard-card {
        background: linear-gradient(135deg, #ffffff, #f0f7ff);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(26, 67, 113, 0.2);
        margin-bottom: 1rem;
        border-left: 5px solid #4A90D9;
        transition: all 0.3s ease;
    }
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(26, 67, 113, 0.3);
    }
    .dashboard-card.green { border-left-color: #2ECC71; }
    .dashboard-card.orange { border-left-color: #F39C12; }
    .dashboard-card.purple { border-left-color: #9B59B6; }
    .dashboard-card.red { border-left-color: #E74C3C; }
    
    .metric-value {
        font-size: 2.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #1B3A7A, #4A90D9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.35rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-active { background: #D5F5E3; color: #1A7A3A; border: 2px solid #2ECC71; }
    .status-pending { background: #FDEBD0; color: #7D6608; border: 2px solid #F39C12; }
    .status-inprogress { background: #D6EAF8; color: #1A5276; border: 2px solid #3498DB; }
    .status-new { background: #FADBD8; color: #7B241C; border: 2px solid #E74C3C; }
    .status-completed { background: #D5F5E3; color: #1A7A3A; border: 2px solid #27AE60; }
    .status-paid { background: #D5F5E3; color: #1A7A3A; border: 2px solid #2ECC71; }
    .status-overdue { background: #FADBD8; color: #7B241C; border: 2px solid #E74C3C; }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #1B3A7A, #4A90D9);
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(26, 67, 113, 0.4);
    }
    
    /* Login box - Compact */
    .login-box {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem 2.5rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        max-width: 380px;
        margin: 1rem auto;
        backdrop-filter: blur(10px);
    }
    .login-box h2 {
        text-align: center;
        color: #1B3A7A;
        margin-bottom: 1.5rem;
        font-size: 1.5rem;
    }
    
    /* Section headers */
    .section-header {
        color: #1B3A7A !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        margin: 1rem 0 !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 3px solid #4A90D9 !important;
    }
    
    /* Login title */
    .login-title {
        text-align: center;
        padding: 0.5rem 0;
    }
    .login-title h1 {
        color: white;
        font-size: 2.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin: 0;
    }
    .login-title p {
        color: rgba(255,255,255,0.9);
        font-size: 1rem;
        margin: 0.2rem 0 0 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== AUTHENTICATION ====================
def check_auth():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        show_login()
        return False
    return True

def show_login():
    st.markdown("""
    <div class="login-title">
        <h1>🏠 TenantHub</h1>
        <p>Property Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h2>🔐 Admin Login</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Enter username", key="login_username")
        password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")
        
        if st.button("Login", key="login_button"):
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Invalid credentials!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

def logout():
    if st.sidebar.button("🚪 Logout", use_container_width=True, key="logout_button"):
        st.session_state.logged_in = False
        st.rerun()

# ==================== DATA MANAGEMENT ====================
def get_default_tenants():
    return pd.DataFrame({
        'ID': [1, 2, 3, 4, 5],
        'Name': ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Emily Brown', 'David Wilson'],
        'Email': ['john@email.com', 'sarah@email.com', 'mike@email.com', 'emily@email.com', 'david@email.com'],
        'Phone': ['(555) 123-4567', '(555) 234-5678', '(555) 345-6789', '(555) 456-7890', '(555) 567-8901'],
        'Unit': ['3B', '7C', '12A', '5D', '9E'],
        'Status': ['Active', 'Active', 'Pending', 'Active', 'Active'],
        'Rent': [1200, 1400, 1600, 1100, 1500],
        'Move_In_Date': ['2024-01-01', '2024-03-15', '2024-06-01', '2023-11-01', '2024-02-01']
    })

def get_default_properties():
    return pd.DataFrame({
        'ID': [1, 2, 3, 4, 5],
        'Address': ['123 Main St', '456 Oak Ave', '789 Pine Rd', '321 Elm St', '654 Maple Dr'],
        'City': ['Springfield', 'Riverside', 'Lakewood', 'Springfield', 'Riverside'],
        'Type': ['Apartment', 'Townhouse', 'Apartment', 'Duplex', 'Single Family'],
        'Units': [12, 8, 16, 6, 4],
        'Occupancy': [10, 7, 15, 5, 4]
    })

def get_default_maintenance():
    return pd.DataFrame({
        'ID': ['M-001', 'M-002', 'M-003', 'M-004'],
        'Unit': ['3B', '7C', '12A', '5D'],
        'Issue': ['Leaky faucet in kitchen', 'Broken AC unit', 'Electrical outlet not working', 'Water heater malfunction'],
        'Status': ['In Progress', 'New', 'Active', 'Completed'],
        'Priority': ['Medium', 'High', 'Low', 'High'],
        'Reported': ['2024-10-20', '2024-10-22', '2024-10-21', '2024-10-18'],
        'Tenant': ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Emily Brown']
    })

def get_default_payments():
    return pd.DataFrame({
        'ID': [1, 2, 3, 4],
        'Tenant': ['John Smith', 'Sarah Johnson', 'Emily Brown', 'David Wilson'],
        'Unit': ['3B', '7C', '5D', '9E'],
        'Amount': [1200, 1400, 1100, 1500],
        'Due_Date': ['2024-11-01', '2024-11-15', '2024-11-01', '2024-11-01'],
        'Status': ['Paid', 'Paid', 'Pending', 'Paid']
    })

def init_data():
    if 'tenants' not in st.session_state or not isinstance(st.session_state.tenants, pd.DataFrame):
        st.session_state.tenants = get_default_tenants()
    if 'properties' not in st.session_state or not isinstance(st.session_state.properties, pd.DataFrame):
        st.session_state.properties = get_default_properties()
    if 'maintenance' not in st.session_state or not isinstance(st.session_state.maintenance, pd.DataFrame):
        st.session_state.maintenance = get_default_maintenance()
    if 'payments' not in st.session_state or not isinstance(st.session_state.payments, pd.DataFrame):
        st.session_state.payments = get_default_payments()
    if 'agreements' not in st.session_state:
        st.session_state.agreements = {}

def download_csv(df, filename):
    if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
        csv = df.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {filename}",
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
            key=f"download_{filename}"
        )

def upload_csv(df_type):
    uploaded_file = st.file_uploader(
        f"📤 Upload {df_type} CSV",
        type=['csv'],
        key=f"upload_{df_type}_{datetime.now().timestamp()}"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Loaded {len(df)} records!")
            if st.button(f"Apply {df_type} Data", key=f"apply_{df_type}_{datetime.now().timestamp()}"):
                if df_type == 'Tenants':
                    st.session_state.tenants = df
                elif df_type == 'Properties':
                    st.session_state.properties = df
                elif df_type == 'Maintenance':
                    st.session_state.maintenance = df
                elif df_type == 'Payments':
                    st.session_state.payments = df
                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ==================== PAYMENT REMINDER FUNCTIONS ====================
def check_payment_reminders():
    """Check for upcoming payment due dates and show reminders"""
    if isinstance(st.session_state.payments, pd.DataFrame) and not st.session_state.payments.empty:
        today = datetime.now().date()
        reminders = []
        
        for idx, row in st.session_state.payments.iterrows():
            if row['Status'] != 'Paid':
                due_date = datetime.strptime(row['Due_Date'], '%Y-%m-%d').date()
                days_until = (due_date - today).days
                
                if days_until <= 10 and days_until >= 0:
                    reminders.append({
                        'tenant': row['Tenant'],
                        'unit': row['Unit'],
                        'amount': row['Amount'],
                        'due_date': row['Due_Date'],
                        'days': days_until,
                        'urgent': days_until <= 3
                    })
                elif days_until < 0:
                    reminders.append({
                        'tenant': row['Tenant'],
                        'unit': row['Unit'],
                        'amount': row['Amount'],
                        'due_date': row['Due_Date'],
                        'days': days_until,
                        'urgent': True,
                        'overdue': True
                    })
        
        return reminders
    return []

def generate_payment_dates(move_in_date):
    """Generate payment due dates based on move-in date"""
    move_in = datetime.strptime(move_in_date, '%Y-%m-%d').date()
    today = datetime.now().date()
    
    # Get the day of month from move-in date
    day_of_month = move_in.day
    
    # Generate due dates for next 12 months
    due_dates = []
    for month in range(12):
        year = today.year + (today.month + month - 1) // 12
        month_num = ((today.month - 1 + month) % 12) + 1
        
        # Handle months with fewer days
        last_day = pd.Timestamp(year=year, month=month_num, day=1).days_in_month
        due_day = min(day_of_month, last_day)
        
        due_date = datetime(year, month_num, due_day).date()
        if due_date >= today:
            due_dates.append(due_date.strftime('%Y-%m-%d'))
    
    return due_dates

# ==================== PDF AGREEMENT GENERATOR ====================
def generate_agreement_pdf(tenant_name, unit, rent, move_in_date):
    """Generate a rental agreement PDF with terms and conditions"""
    if REPORTLAB_AVAILABLE:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1B3A7A'),
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1B3A7A'),
            spaceAfter=12,
            spaceBefore=12
        ))
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
        styles.add(ParagraphStyle(
            name='CustomFooter',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceBefore=30
        ))
        
        # Build the document
        story = []
        
        # Title
        story.append(Paragraph("RENTAL AGREEMENT", styles['CustomTitle']))
        story.append(Spacer(1, 0.25*inch))
        
        # Date
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['CustomBody']))
        story.append(Spacer(1, 0.25*inch))
        
        # Parties
        story.append(Paragraph("PARTIES", styles['CustomHeading']))
        story.append(Paragraph(f"This Rental Agreement is made between TenantHub Property Management (hereinafter referred to as 'Landlord') and {tenant_name} (hereinafter referred to as 'Tenant').", styles['CustomBody']))
        story.append(Spacer(1, 0.25*inch))
        
        # Property Details
        story.append(Paragraph("PROPERTY DETAILS", styles['CustomHeading']))
        story.append(Paragraph(f"Property Unit: {unit}", styles['CustomBody']))
        story.append(Paragraph(f"Monthly Rent: ${rent:.2f}", styles['CustomBody']))
        story.append(Paragraph(f"Move-in Date: {move_in_date}", styles['CustomBody']))
        story.append(Spacer(1, 0.25*inch))
        
        # Terms and Conditions
        story.append(Paragraph("TERMS AND CONDITIONS", styles['CustomHeading']))
        
        terms = [
            "1. RENT PAYMENT: Tenant agrees to pay the monthly rent on or before the 1st day of each month. Rent is due on the same day each month as the move-in date.",
            "2. LATE PAYMENT: A late fee of $50 will be charged if rent is not received within 5 days after the due date.",
            "3. SECURITY DEPOSIT: A security deposit equal to one month's rent is required and will be held by Landlord.",
            "4. UTILITIES: Tenant is responsible for all utility costs including electricity, water, gas, and internet.",
            "5. MAINTENANCE: Tenant agrees to maintain the property in good condition and report any issues immediately.",
            "6. PETS: Pets are allowed only with prior written consent and additional pet deposit.",
            "7. SUBLEASING: Subleasing is not permitted without written consent from Landlord.",
            "8. NOTICE: Either party must provide 30 days written notice to terminate this agreement.",
            "9. RENT INCREASE: Rent may be increased with 60 days written notice.",
            "10. GOVERNING LAW: This agreement is governed by the laws of the state.",
            "11. ENTIRE AGREEMENT: This document represents the entire agreement between parties.",
            "12. AMENDMENTS: Any amendments must be in writing and signed by both parties."
        ]
        
        for term in terms:
            story.append(Paragraph(term, styles['CustomBody']))
        
        story.append(Spacer(1, 0.25*inch))
        
        # Signatures
        story.append(Paragraph("SIGNATURES", styles['CustomHeading']))
        story.append(Spacer(1, 0.25*inch))
        
        signature_data = [
            ["Landlord Signature:", "", "Date:", ""],
            ["________________________", "", "______________", ""],
            ["", "", "", ""],
            ["Tenant Signature:", "", "Date:", ""],
            ["________________________", "", "______________", ""]
        ]
        
        sig_table = Table(signature_data, colWidths=[2.5*inch, 0.5*inch, 1.5*inch, 0.5*inch])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(sig_table)
        
        story.append(Spacer(1, 0.5*inch))
        
        # Footer
        story.append(Paragraph("This agreement is legally binding. Please keep a copy for your records.", styles['CustomFooter']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    else:
        # Fallback: Create a simple text agreement
        return generate_text_agreement(tenant_name, unit, rent, move_in_date)

def generate_text_agreement(tenant_name, unit, rent, move_in_date):
    """Generate a simple text agreement as fallback"""
    content = f"""
    ========================================
              RENTAL AGREEMENT
    ========================================
    
    Date: {datetime.now().strftime('%B %d, %Y')}
    
    PARTIES
    --------
    This Rental Agreement is made between TenantHub Property Management 
    (hereinafter referred to as 'Landlord') and {tenant_name} 
    (hereinafter referred to as 'Tenant').
    
    PROPERTY DETAILS
    -----------------
    Property Unit: {unit}
    Monthly Rent: ${rent:.2f}
    Move-in Date: {move_in_date}
    
    TERMS AND CONDITIONS
    --------------------
    1. RENT PAYMENT: Tenant agrees to pay the monthly rent on or before the 
       1st day of each month. Rent is due on the same day each month as the 
       move-in date.
    
    2. LATE PAYMENT: A late fee of $50 will be charged if rent is not received 
       within 5 days after the due date.
    
    3. SECURITY DEPOSIT: A security deposit equal to one month's rent is 
       required and will be held by Landlord.
    
    4. UTILITIES: Tenant is responsible for all utility costs including 
       electricity, water, gas, and internet.
    
    5. MAINTENANCE: Tenant agrees to maintain the property in good condition 
       and report any issues immediately.
    
    6. PETS: Pets are allowed only with prior written consent and additional 
       pet deposit.
    
    7. SUBLEASING: Subleasing is not permitted without written consent from 
       Landlord.
    
    8. NOTICE: Either party must provide 30 days written notice to terminate 
       this agreement.
    
    9. RENT INCREASE: Rent may be increased with 60 days written notice.
    
    10. GOVERNING LAW: This agreement is governed by the laws of the state.
    
    11. ENTIRE AGREEMENT: This document represents the entire agreement 
        between parties.
    
    12. AMENDMENTS: Any amendments must be in writing and signed by both 
        parties.
    
    SIGNATURES
    -----------
    Landlord Signature: ____________________   Date: ______________
    
    Tenant Signature:  ____________________   Date: ______________
    
    ========================================
    This agreement is legally binding. 
    Please keep a copy for your records.
    ========================================
    """
    
    buffer = io.BytesIO()
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)
    return buffer

# ==================== DELETE FUNCTIONS ====================
def delete_tenant(tenant_id):
    df = st.session_state.tenants
    df = df[df['ID'] != tenant_id]
    st.session_state.tenants = df.reset_index(drop=True)
    st.success("✅ Tenant deleted successfully!")
    st.rerun()

def delete_property(prop_id):
    df = st.session_state.properties
    df = df[df['ID'] != prop_id]
    st.session_state.properties = df.reset_index(drop=True)
    st.success("✅ Property deleted successfully!")
    st.rerun()

def delete_maintenance(maint_id):
    df = st.session_state.maintenance
    df = df[df['ID'] != maint_id]
    st.session_state.maintenance = df.reset_index(drop=True)
    st.success("✅ Maintenance request deleted!")
    st.rerun()

def delete_payment(payment_id):
    df = st.session_state.payments
    df = df[df['ID'] != payment_id]
    st.session_state.payments = df.reset_index(drop=True)
    st.success("✅ Payment deleted successfully!")
    st.rerun()

# ==================== MAIN APP ====================
def show_header():
    st.markdown(f"""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>🏠 TenantHub</h1>
                <p>Property Management Dashboard</p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.9rem; opacity: 0.9;">👤 {st.session_state.get('username', 'Admin')}</div>
                <div style="font-size: 0.8rem; opacity: 0.7;">{datetime.now().strftime('%B %d, %Y')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_metrics():
    col1, col2, col3, col4 = st.columns(4)
    
    tenants_df = st.session_state.tenants
    properties_df = st.session_state.properties
    maintenance_df = st.session_state.maintenance
    payments_df = st.session_state.payments
    
    total_tenants = len(tenants_df) if isinstance(tenants_df, pd.DataFrame) and not tenants_df.empty else 0
    total_properties = len(properties_df) if isinstance(properties_df, pd.DataFrame) and not properties_df.empty else 0
    total_revenue = tenants_df['Rent'].sum() if isinstance(tenants_df, pd.DataFrame) and not tenants_df.empty else 0
    active_maintenance = len(maintenance_df[maintenance_df['Status'] != 'Completed']) if isinstance(maintenance_df, pd.DataFrame) and not maintenance_df.empty else 0
    
    # Calculate overdue payments
    overdue = 0
    if isinstance(payments_df, pd.DataFrame) and not payments_df.empty:
        today = datetime.now().date()
        for _, row in payments_df.iterrows():
            if row['Status'] != 'Paid':
                due_date = datetime.strptime(row['Due_Date'], '%Y-%m-%d').date()
                if due_date < today:
                    overdue += 1
    
    with col1:
        st.markdown(f"""
        <div class="dashboard-card green">
            <div class="metric-label">👥 Total Tenants</div>
            <div class="metric-value">{total_tenants}</div>
            <div style="font-size: 0.85rem; color: #555;">Active: {len(tenants_df[tenants_df['Status'] == 'Active']) if isinstance(tenants_df, pd.DataFrame) and not tenants_df.empty else 0}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="dashboard-card orange">
            <div class="metric-label">🏠 Properties</div>
            <div class="metric-value">{total_properties}</div>
            <div style="font-size: 0.85rem; color: #555;">Total Units: {properties_df['Units'].sum() if isinstance(properties_df, pd.DataFrame) and not properties_df.empty else 0}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="dashboard-card purple">
            <div class="metric-label">💰 Monthly Revenue</div>
            <div class="metric-value">${total_revenue:,}</div>
            <div style="font-size: 0.85rem; color: #555;">From {total_tenants} tenants</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="dashboard-card red">
            <div class="metric-label">⚠️ Overdue Payments</div>
            <div class="metric-value">{overdue}</div>
            <div style="font-size: 0.85rem; color: #555;">Need attention</div>
        </div>
        """, unsafe_allow_html=True)

def show_reminders():
    """Show payment reminders"""
    reminders = check_payment_reminders()
    if reminders:
        st.markdown("### 🔔 Payment Reminders")
        for reminder in reminders:
            if reminder.get('overdue', False):
                st.markdown(f"""
                <div class="reminder-card urgent">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>⚠️ OVERDUE</strong> - {reminder['tenant']} (Unit {reminder['unit']})
                            <br>Amount: ${reminder['amount']} - Due: {reminder['due_date']}
                            <br><span style="color: #E74C3C;">Payment is {abs(reminder['days'])} days overdue!</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                urgency = "urgent" if reminder['urgent'] else ""
                st.markdown(f"""
                <div class="reminder-card {urgency}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>⏰ Payment Due Soon</strong> - {reminder['tenant']} (Unit {reminder['unit']})
                            <br>Amount: ${reminder['amount']} - Due: {reminder['due_date']}
                            <br>⏳ {reminder['days']} days remaining
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("---")

def show_tenants():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">👥 Tenant Management</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander("➕ Add New Tenant", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                name = st.text_input("Full Name", placeholder="John Doe", key="tenant_name")
                email = st.text_input("Email", placeholder="john@email.com", key="tenant_email")
                phone = st.text_input("Phone", placeholder="(555) 123-4567", key="tenant_phone")
            
            with col_b:
                unit = st.text_input("Unit Number", placeholder="3B", key="tenant_unit")
                rent = st.number_input("Monthly Rent ($)", min_value=0, step=50, key="tenant_rent")
                status = st.selectbox("Status", ["Active", "Pending", "In Progress", "New"], key="tenant_status")
            
            move_in_date = st.date_input("Move-in Date", datetime.now(), key="tenant_move_in")
            
            col_c, col_d = st.columns(2)
            with col_c:
                if st.button("💾 Add Tenant", key="add_tenant_btn"):
                    new_id = len(st.session_state.tenants) + 1
                    new_tenant = pd.DataFrame({
                        'ID': [new_id],
                        'Name': [name],
                        'Email': [email],
                        'Phone': [phone],
                        'Unit': [unit],
                        'Status': [status],
                        'Rent': [rent],
                        'Move_In_Date': [move_in_date.strftime('%Y-%m-%d')]
                    })
                    st.session_state.tenants = pd.concat([st.session_state.tenants, new_tenant], ignore_index=True)
                    
                    # Generate payment schedule
                    due_dates = generate_payment_dates(move_in_date.strftime('%Y-%m-%d'))
                    for due_date in due_dates:
                        new_payment = pd.DataFrame({
                            'ID': [len(st.session_state.payments) + 1],
                            'Tenant': [name],
                            'Unit': [unit],
                            'Amount': [rent],
                            'Due_Date': [due_date],
                            'Status': ['Pending']
                        })
                        st.session_state.payments = pd.concat([st.session_state.payments, new_payment], ignore_index=True)
                    
                    st.success("✅ Tenant added with payment schedule!")
                    st.rerun()
            
            with col_d:
                if st.button("📄 Generate Agreement", key="gen_agreement_btn"):
                    if name and unit and rent > 0:
                        pdf_buffer = generate_agreement_pdf(name, unit, rent, move_in_date.strftime('%Y-%m-%d'))
                        file_extension = "pdf" if REPORTLAB_AVAILABLE else "txt"
                        st.download_button(
                            label=f"📥 Download Agreement.{file_extension}",
                            data=pdf_buffer,
                            file_name=f"agreement_{name}_{unit}.{file_extension}",
                            mime="application/pdf" if REPORTLAB_AVAILABLE else "text/plain",
                            use_container_width=True,
                            key=f"download_agreement_{name}"
                        )
                    else:
                        st.warning("Please fill in all fields first!")
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.tenants, 'tenants.csv')
            upload_csv('Tenants')
    
    if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
        search = st.text_input("🔍 Search tenants", placeholder="Search by name or unit...", key="tenant_search")
        
        filtered_df = st.session_state.tenants.copy()
        if search:
            filtered_df = filtered_df[
                filtered_df['Name'].str.contains(search, case=False, na=False) | 
                filtered_df['Unit'].str.contains(search, case=False, na=False)
            ]
        
        for idx, row in filtered_df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1.5, 1, 1, 0.8, 0.8])
            
            with col1:
                st.markdown(f"**{row['Name']}**")
                st.caption(row['Email'])
            
            with col2:
                st.write(f"Unit: {row['Unit']}")
                st.write(f"Rent: ${row['Rent']}")
                st.caption(f"Move-in: {row['Move_In_Date']}")
            
            with col3:
                status_class = {
                    "Active": "status-active",
                    "Pending": "status-pending",
                    "In Progress": "status-inprogress",
                    "New": "status-new"
                }.get(row['Status'], "status-active")
                st.markdown(f'<span class="status-badge {status_class}">{row["Status"]}</span>', unsafe_allow_html=True)
            
            with col4:
                if st.button(f"📄 Agreement", key=f"agreement_{row['ID']}_{idx}", use_container_width=True):
                    pdf_buffer = generate_agreement_pdf(row['Name'], row['Unit'], row['Rent'], row['Move_In_Date'])
                    file_extension = "pdf" if REPORTLAB_AVAILABLE else "txt"
                    st.download_button(
                        label=f"📥 Download.{file_extension}",
                        data=pdf_buffer,
                        file_name=f"agreement_{row['Name']}_{row['Unit']}.{file_extension}",
                        mime="application/pdf" if REPORTLAB_AVAILABLE else "text/plain",
                        use_container_width=True,
                        key=f"download_agreement_{row['ID']}"
                    )
            
            with col5:
                if st.button(f"✏️ Edit", key=f"edit_tenant_{row['ID']}_{idx}", use_container_width=True):
                    with st.expander(f"✏️ Editing: {row['Name']}", expanded=True):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            new_name = st.text_input("Name", value=row['Name'], key=f"edit_name_{row['ID']}")
                            new_email = st.text_input("Email", value=row['Email'], key=f"edit_email_{row['ID']}")
                            new_phone = st.text_input("Phone", value=row['Phone'], key=f"edit_phone_{row['ID']}")
                        
                        with col_b:
                            new_unit = st.text_input("Unit", value=row['Unit'], key=f"edit_unit_{row['ID']}")
                            new_rent = st.number_input("Rent", value=float(row['Rent']), step=50.0, key=f"edit_rent_{row['ID']}")
                            new_status = st.selectbox("Status", ["Active", "Pending", "In Progress", "New"], 
                                                     index=["Active", "Pending", "In Progress", "New"].index(row['Status']),
                                                     key=f"edit_status_{row['ID']}")
                        
                        col_c, col_d = st.columns(2)
                        with col_c:
                            if st.button("💾 Save", key=f"save_tenant_{row['ID']}"):
                                df = st.session_state.tenants
                                df.loc[df['ID'] == row['ID'], 'Name'] = new_name
                                df.loc[df['ID'] == row['ID'], 'Email'] = new_email
                                df.loc[df['ID'] == row['ID'], 'Phone'] = new_phone
                                df.loc[df['ID'] == row['ID'], 'Unit'] = new_unit
                                df.loc[df['ID'] == row['ID'], 'Rent'] = new_rent
                                df.loc[df['ID'] == row['ID'], 'Status'] = new_status
                                st.session_state.tenants = df
                                st.success("✅ Tenant updated!")
                                st.rerun()
                        
                        with col_d:
                            if st.button("❌ Cancel", key=f"cancel_tenant_{row['ID']}"):
                                st.rerun()
            
            with col6:
                if st.button(f"🗑️ Delete", key=f"del_tenant_{row['ID']}_{idx}", use_container_width=True):
                    delete_tenant(row['ID'])
            
            st.markdown("---")
    else:
        st.info("No tenants added yet.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_properties():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">🏠 Property Management</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander("➕ Add New Property", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                address = st.text_input("Address", placeholder="123 Main St", key="prop_address")
                city = st.text_input("City", placeholder="Springfield", key="prop_city")
            
            with col_b:
                prop_type = st.selectbox("Property Type", ["Apartment", "Townhouse", "Duplex", "Single Family", "Commercial"], key="prop_type")
                units = st.number_input("Total Units", min_value=1, step=1, key="prop_units")
                occupancy = st.number_input("Occupied Units", min_value=0, max_value=units, step=1, key="prop_occupancy")
            
            if st.button("💾 Add Property", key="add_prop_btn"):
                new_id = len(st.session_state.properties) + 1
                new_property = pd.DataFrame({
                    'ID': [new_id],
                    'Address': [address],
                    'City': [city],
                    'Type': [prop_type],
                    'Units': [units],
                    'Occupancy': [occupancy]
                })
                st.session_state.properties = pd.concat([st.session_state.properties, new_property], ignore_index=True)
                st.success("✅ Property added!")
                st.rerun()
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.properties, 'properties.csv')
            upload_csv('Properties')
    
    if isinstance(st.session_state.properties, pd.DataFrame) and not st.session_state.properties.empty:
        for idx, row in st.session_state.properties.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{row['Address']}**")
                st.caption(row['City'])
            
            with col2:
                st.write(f"Type: {row['Type']}")
                st.write(f"Units: {row['Units']} ({row['Occupancy']} occupied)")
            
            with col3:
                occupancy_pct = int((row['Occupancy'] / row['Units']) * 100)
                st.progress(occupancy_pct / 100)
                st.caption(f"{occupancy_pct}% occupied")
            
            with col4:
                if st.button(f"✏️ Edit", key=f"edit_prop_{row['ID']}_{idx}", use_container_width=True):
                    with st.expander(f"✏️ Editing: {row['Address']}", expanded=True):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            new_address = st.text_input("Address", value=row['Address'], key=f"edit_prop_addr_{row['ID']}")
                            new_city = st.text_input("City", value=row['City'], key=f"edit_prop_city_{row['ID']}")
                        
                        with col_b:
                            new_type = st.selectbox("Type", ["Apartment", "Townhouse", "Duplex", "Single Family", "Commercial"],
                                                   index=["Apartment", "Townhouse", "Duplex", "Single Family", "Commercial"].index(row['Type']),
                                                   key=f"edit_prop_type_{row['ID']}")
                            new_units = st.number_input("Units", value=int(row['Units']), step=1, key=f"edit_prop_units_{row['ID']}")
                            new_occupancy = st.number_input("Occupancy", value=int(row['Occupancy']), step=1, max_value=int(new_units),
                                                           key=f"edit_prop_occ_{row['ID']}")
                        
                        col_c, col_d = st.columns(2)
                        with col_c:
                            if st.button("💾 Save", key=f"save_prop_{row['ID']}"):
                                df = st.session_state.properties
                                df.loc[df['ID'] == row['ID'], 'Address'] = new_address
                                df.loc[df['ID'] == row['ID'], 'City'] = new_city
                                df.loc[df['ID'] == row['ID'], 'Type'] = new_type
                                df.loc[df['ID'] == row['ID'], 'Units'] = new_units
                                df.loc[df['ID'] == row['ID'], 'Occupancy'] = new_occupancy
                                st.session_state.properties = df
                                st.success("✅ Property updated!")
                                st.rerun()
                        
                        with col_d:
                            if st.button("❌ Cancel", key=f"cancel_prop_{row['ID']}"):
                                st.rerun()
            
            with col5:
                if st.button(f"🗑️ Delete", key=f"del_prop_{row['ID']}_{idx}", use_container_width=True):
                    delete_property(row['ID'])
            
            st.markdown("---")
    else:
        st.info("No properties added yet.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_maintenance():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">🔧 Maintenance Management</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander("➕ Report New Issue", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                unit = st.text_input("Unit Number", placeholder="3B", key="maint_unit")
                tenant = st.text_input("Tenant Name", placeholder="John Smith", key="maint_tenant")
                issue = st.text_area("Issue Description", placeholder="Describe the issue...", key="maint_issue")
            
            with col_b:
                priority = st.selectbox("Priority", ["High", "Medium", "Low"], key="maint_priority")
                status = st.selectbox("Status", ["New", "Active", "In Progress", "Completed"], key="maint_status")
            
            if st.button("💾 Report Issue", key="add_maint_btn"):
                new_id = f"M-{len(st.session_state.maintenance) + 1:03d}"
                new_issue = pd.DataFrame({
                    'ID': [new_id],
                    'Unit': [unit],
                    'Issue': [issue],
                    'Status': [status],
                    'Priority': [priority],
                    'Reported': [datetime.now().strftime('%Y-%m-%d')],
                    'Tenant': [tenant]
                })
                st.session_state.maintenance = pd.concat([st.session_state.maintenance, new_issue], ignore_index=True)
                st.success("✅ Issue reported!")
                st.rerun()
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.maintenance, 'maintenance.csv')
            upload_csv('Maintenance')
    
    if isinstance(st.session_state.maintenance, pd.DataFrame) and not st.session_state.maintenance.empty:
        priority_filter = st.selectbox("Filter by priority", ["All", "High", "Medium", "Low"], key="maint_filter")
        
        filtered_df = st.session_state.maintenance.copy()
        if priority_filter != "All":
            filtered_df = filtered_df[filtered_df['Priority'] == priority_filter]
        
        for idx, row in filtered_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1, 1])
            
            with col1:
                st.markdown(f"**#{row['ID']}**")
                st.write(row['Issue'][:50] + "..." if len(row['Issue']) > 50 else row['Issue'])
            
            with col2:
                st.write(f"Unit: {row['Unit']}")
                st.write(f"Tenant: {row['Tenant']}")
            
            with col3:
                priority_color = {
                    "High": "🔴",
                    "Medium": "🟡",
                    "Low": "🟢"
                }.get(row['Priority'], "⚪")
                st.write(f"{priority_color} {row['Priority']}")
                status_class = {
                    "Active": "status-active",
                    "New": "status-new",
                    "In Progress": "status-inprogress",
                    "Completed": "status-completed"
                }.get(row['Status'], "status-active")
                st.markdown(f'<span class="status-badge {status_class}">{row["Status"]}</span>', unsafe_allow_html=True)
            
            with col4:
                if st.button(f"✏️ Edit", key=f"edit_maint_{row['ID']}_{idx}", use_container_width=True):
                    with st.expander(f"✏️ Editing: {row['Issue'][:30]}...", expanded=True):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            new_unit = st.text_input("Unit", value=row['Unit'], key=f"edit_maint_unit_{row['ID']}")
                            new_tenant = st.text_input("Tenant", value=row['Tenant'], key=f"edit_maint_tenant_{row['ID']}")
                            new_issue = st.text_area("Issue", value=row['Issue'], key=f"edit_maint_issue_{row['ID']}")
                        
                        with col_b:
                            new_status = st.selectbox("Status", ["New", "Active", "In Progress", "Completed"],
                                                     index=["New", "Active", "In Progress", "Completed"].index(row['Status']),
                                                     key=f"edit_maint_status_{row['ID']}")
                            new_priority = st.selectbox("Priority", ["High", "Medium", "Low"],
                                                       index=["High", "Medium", "Low"].index(row['Priority']),
                                                       key=f"edit_maint_priority_{row['ID']}")
                        
                        col_c, col_d = st.columns(2)
                        with col_c:
                            if st.button("💾 Save", key=f"save_maint_{row['ID']}"):
                                df = st.session_state.maintenance
                                df.loc[df['ID'] == row['ID'], 'Unit'] = new_unit
                                df.loc[df['ID'] == row['ID'], 'Tenant'] = new_tenant
                                df.loc[df['ID'] == row['ID'], 'Issue'] = new_issue
                                df.loc[df['ID'] == row['ID'], 'Status'] = new_status
                                df.loc[df['ID'] == row['ID'], 'Priority'] = new_priority
                                st.session_state.maintenance = df
                                st.success("✅ Maintenance updated!")
                                st.rerun()
                        
                        with col_d:
                            if st.button("❌ Cancel", key=f"cancel_maint_{row['ID']}"):
                                st.rerun()
            
            with col5:
                if st.button(f"🗑️ Delete", key=f"del_maint_{row['ID']}_{idx}", use_container_width=True):
                    delete_maintenance(row['ID'])
            
            st.markdown("---")
    else:
        st.info("No maintenance issues reported yet.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_payments():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">💰 Payment Management</h2>', unsafe_allow_html=True)
    
    # Show reminders
    show_reminders()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander("➕ Record Payment", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                tenant = st.text_input("Tenant Name", placeholder="John Smith", key="payment_tenant")
                unit = st.text_input("Unit Number", placeholder="3B", key="payment_unit")
                amount = st.number_input("Amount ($)", min_value=0, step=10, key="payment_amount")
            
            with col_b:
                payment_date = st.date_input("Payment Date", datetime.now(), key="payment_date")
                status = st.selectbox("Status", ["Paid", "Pending", "Overdue"], key="payment_status")
            
            if st.button("💾 Record Payment", key="add_payment_btn"):
                new_id = len(st.session_state.payments) + 1
                new_payment = pd.DataFrame({
                    'ID': [new_id],
                    'Tenant': [tenant],
                    'Unit': [unit],
                    'Amount': [amount],
                    'Due_Date': [payment_date.strftime('%Y-%m-%d')],
                    'Status': [status]
                })
                st.session_state.payments = pd.concat([st.session_state.payments, new_payment], ignore_index=True)
                st.success("✅ Payment recorded!")
                st.rerun()
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.payments, 'payments.csv')
            upload_csv('Payments')
    
    if isinstance(st.session_state.payments, pd.DataFrame) and not st.session_state.payments.empty:
        total_collected = st.session_state.payments[st.session_state.payments['Status'] == 'Paid']['Amount'].sum()
        total_pending = st.session_state.payments[st.session_state.payments['Status'] == 'Pending']['Amount'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Collected", f"${total_collected:,}")
        with col2:
            st.metric("⏳ Pending", f"${total_pending:,}")
        with col3:
            st.metric("📊 Total Records", len(st.session_state.payments))
        
        # Filter options
        filter_status = st.selectbox("Filter by status", ["All", "Paid", "Pending", "Overdue"], key="payment_filter")
        
        filtered_df = st.session_state.payments.copy()
        if filter_status != "All":
            filtered_df = filtered_df[filtered_df['Status'] == filter_status]
        
        for idx, row in filtered_df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1, 1, 1, 0.8, 0.8])
            
            with col1:
                st.markdown(f"**{row['Tenant']}**")
                st.caption(f"Unit {row['Unit']}")
            
            with col2:
                st.write(f"${row['Amount']}")
            
            with col3:
                st.caption(f"Due: {row['Due_Date']}")
            
            with col4:
                status_class = {
                    "Paid": "status-paid",
                    "Pending": "status-pending",
                    "Overdue": "status-overdue"
                }.get(row['Status'], "status-active")
                st.markdown(f'<span class="status-badge {status_class}">{row["Status"]}</span>', unsafe_allow_html=True)
            
            with col5:
                if st.button(f"✏️ Edit", key=f"edit_payment_{row['ID']}_{idx}", use_container_width=True):
                    with st.expander(f"✏️ Editing: {row['Tenant']}", expanded=True):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            new_tenant = st.text_input("Tenant", value=row['Tenant'], key=f"edit_pay_tenant_{row['ID']}")
                            new_unit = st.text_input("Unit", value=row['Unit'], key=f"edit_pay_unit_{row['ID']}")
                        
                        with col_b:
                            new_amount = st.number_input("Amount", value=float(row['Amount']), step=10.0, key=f"edit_pay_amount_{row['ID']}")
                            new_status = st.selectbox("Status", ["Paid", "Pending", "Overdue"],
                                                     index=["Paid", "Pending", "Overdue"].index(row['Status']),
                                                     key=f"edit_pay_status_{row['ID']}")
                        
                        col_c, col_d = st.columns(2)
                        with col_c:
                            if st.button("💾 Save", key=f"save_payment_{row['ID']}"):
                                df = st.session_state.payments
                                df.loc[df['ID'] == row['ID'], 'Tenant'] = new_tenant
                                df.loc[df['ID'] == row['ID'], 'Unit'] = new_unit
                                df.loc[df['ID'] == row['ID'], 'Amount'] = new_amount
                                df.loc[df['ID'] == row['ID'], 'Status'] = new_status
                                st.session_state.payments = df
                                st.success("✅ Payment updated!")
                                st.rerun()
                        
                        with col_d:
                            if st.button("❌ Cancel", key=f"cancel_payment_{row['ID']}"):
                                st.rerun()
            
            with col6:
                if st.button(f"🗑️ Delete", key=f"del_payment_{row['ID']}_{idx}", use_container_width=True):
                    delete_payment(row['ID'])
            
            st.markdown("---")
    else:
        st.info("No payments recorded yet.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
def show_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="color: #1B3A7A; margin: 0;">🏠</h1>
            <h3 style="color: #1B3A7A; margin: 0;">TenantHub</h3>
            <p style="color: #888; font-size: 0.8rem;">v2.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        page = st.radio(
            "📋 Navigation",
            ["📊 Dashboard", "👥 Tenants", "🏠 Properties", "🔧 Maintenance", "💰 Payments"],
            index=0,
            key="navigation"
        )
        
        st.markdown("---")
        
        st.markdown("### 📊 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tenants", len(st.session_state.tenants) if isinstance(st.session_state.tenants, pd.DataFrame) else 0)
        with col2:
            st.metric("Properties", len(st.session_state.properties) if isinstance(st.session_state.properties, pd.DataFrame) else 0)
        
        st.markdown("---")
        logout()
        
        return page

# ==================== MAIN ====================
def main():
    if not check_auth():
        return
    
    init_data()
    show_header()
    
    page = show_sidebar()
    
    if page == "📊 Dashboard":
        show_metrics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div style="background: rgba(255,255,255,0.95); padding: 1.5rem; border-radius: 15px; backdrop-filter: blur(10px);">
                <h3 style="color: #1B3A7A;">📋 Recent Activity</h3>
            """, unsafe_allow_html=True)
            
            activities = [
                "🔵 New tenant signed lease for Unit 3B",
                "🟢 Maintenance resolved for Unit 12A",
                "🟡 Rent payment received from Unit 7C",
                "🔴 Inspection scheduled for Unit 5D"
            ]
            for activity in activities:
                st.markdown(f"""
                <div style="padding: 0.5rem 0; border-bottom: 1px solid #eee;">
                    {activity}
                    <span style="color: #999; font-size: 0.8rem; float: right;">{datetime.now().strftime('%H:%M')}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: rgba(255,255,255,0.95); padding: 1.5rem; border-radius: 15px; backdrop-filter: blur(10px);">
                <h3 style="color: #1B3A7A;">📈 Revenue Overview</h3>
            """, unsafe_allow_html=True)
            
            chart_data = {
                'Mon': 1200, 'Tue': 1400, 'Wed': 1100,
                'Thu': 1600, 'Fri': 1800, 'Sat': 900, 'Sun': 700
            }
            st.bar_chart(chart_data, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Show reminders on dashboard
        show_reminders()
    
    elif page == "👥 Tenants":
        show_tenants()
    elif page == "🏠 Properties":
        show_properties()
    elif page == "🔧 Maintenance":
        show_maintenance()
    elif page == "💰 Payments":
        show_payments()

if __name__ == "__main__":
    main()
