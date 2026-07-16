import streamlit as st
import pandas as pd
import io
import os
import json
from datetime import datetime, timedelta
import hashlib
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import re
import pickle

# Try to import reportlab, fallback to simple text if not available
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ==================== DATA PERSISTENCE ====================
DATA_DIR = "data"

def ensure_data_dir():
    """Ensure data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_data_to_csv(df, filename):
    """Save DataFrame to CSV file"""
    try:
        ensure_data_dir()
        if df is not None and isinstance(df, pd.DataFrame):
            filepath = os.path.join(DATA_DIR, filename)
            df.to_csv(filepath, index=False)
            return True
        return False
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

def load_data_from_csv(filename, default_df):
    """Load DataFrame from CSV file, return default if not found"""
    try:
        ensure_data_dir()
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            if not df.empty:
                # Ensure all columns exist
                for col in default_df.columns:
                    if col not in df.columns:
                        df[col] = ''
                return df
        return default_df.copy()
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return default_df.copy()

def save_all_data():
    """Save all data to CSV files"""
    try:
        ensure_data_dir()
        success = True
        
        if 'tenants' in st.session_state and isinstance(st.session_state.tenants, pd.DataFrame):
            if not save_data_to_csv(st.session_state.tenants, 'tenants.csv'):
                success = False
        if 'properties' in st.session_state and isinstance(st.session_state.properties, pd.DataFrame):
            if not save_data_to_csv(st.session_state.properties, 'properties.csv'):
                success = False
        if 'maintenance' in st.session_state and isinstance(st.session_state.maintenance, pd.DataFrame):
            if not save_data_to_csv(st.session_state.maintenance, 'maintenance.csv'):
                success = False
        if 'payments' in st.session_state and isinstance(st.session_state.payments, pd.DataFrame):
            if not save_data_to_csv(st.session_state.payments, 'payments.csv'):
                success = False
        
        return success
    except Exception as e:
        print(f"Error saving data: {e}")
        return False

def load_all_data():
    """Load all data from CSV files"""
    try:
        ensure_data_dir()
        
        if 'tenants' not in st.session_state or st.session_state.tenants.empty:
            st.session_state.tenants = load_data_from_csv('tenants.csv', get_default_tenants())
        if 'properties' not in st.session_state or st.session_state.properties.empty:
            st.session_state.properties = load_data_from_csv('properties.csv', get_default_properties())
        if 'maintenance' not in st.session_state or st.session_state.maintenance.empty:
            st.session_state.maintenance = load_data_from_csv('maintenance.csv', get_default_maintenance())
        if 'payments' not in st.session_state or st.session_state.payments.empty:
            st.session_state.payments = load_data_from_csv('payments.csv', get_default_payments())
        
        # Ensure Payment_Time column exists in payments
        if 'payments' in st.session_state and isinstance(st.session_state.payments, pd.DataFrame):
            if 'Payment_Time' not in st.session_state.payments.columns:
                st.session_state.payments['Payment_Time'] = ''
        
        # Ensure Property columns exist in tenants
        if 'tenants' in st.session_state and isinstance(st.session_state.tenants, pd.DataFrame):
            if 'Property' not in st.session_state.tenants.columns:
                st.session_state.tenants['Property'] = ''
            if 'Property_Type' not in st.session_state.tenants.columns:
                st.session_state.tenants['Property_Type'] = ''
            if 'Property_ID' not in st.session_state.tenants.columns:
                st.session_state.tenants['Property_ID'] = ''
        
        update_all_occupancy()
        
        return True
    except Exception as e:
        print(f"Error loading data: {e}")
        return False

def reset_to_defaults():
    """Reset all data to defaults (empty dataframes)"""
    st.session_state.tenants = get_default_tenants()
    st.session_state.properties = get_default_properties()
    st.session_state.maintenance = get_default_maintenance()
    st.session_state.payments = get_default_payments()
    save_all_data()
    st.success("✅ Reset to default data!")

# ==================== EMAIL CONFIGURATION ====================
EMAIL_SENDER = "ndahabonimanadaniel13@gmail.com"
EMAIL_PASSWORD = "xsfa ooya nbnn pofr"
EMAIL_RECIPIENT = "ndahabonimanadaniel13@gmail.com"

def send_email_report(recipient_email, subject, body, attachment=None, attachment_name=None):
    """Send email report with optional attachment"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        if attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.getvalue())
            encoders.encode_base64(part)
            if attachment_name:
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment_name}'
                )
            else:
                part.add_header(
                    'Content-Disposition',
                    'attachment; filename= report.csv'
                )
            msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def generate_tenant_report():
    """Generate tenant report as CSV"""
    if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
        csv_buffer = io.BytesIO()
        st.session_state.tenants.to_csv(csv_buffer, index=False)
        csv_buffer.name = "tenant_report.csv"
        return csv_buffer
    return None

def generate_payment_report():
    """Generate payment report as CSV"""
    if isinstance(st.session_state.payments, pd.DataFrame) and not st.session_state.payments.empty:
        csv_buffer = io.BytesIO()
        st.session_state.payments.to_csv(csv_buffer, index=False)
        csv_buffer.name = "payment_report.csv"
        return csv_buffer
    return None

def generate_full_report_text():
    """Generate full system report with table format in text"""
    report = []
    report.append("=" * 80)
    report.append("TENANTHUB - SYSTEM REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Tenants Table with Property Type
    report.append("TENANTS:")
    report.append("-" * 80)
    if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
        report.append(f"{'Name':<20} {'Property':<20} {'Type':<22} {'Unit':<10} {'Rent':<15} {'Status':<12} {'Move-In':<12}")
        report.append("-" * 80)
        for _, tenant in st.session_state.tenants.iterrows():
            prop_type = tenant.get('Property_Type', 'N/A')
            report.append(f"{tenant['Name']:<20} {tenant.get('Property', 'N/A'):<20} {prop_type:<22} {tenant['Unit']:<10} {format_currency(tenant['Rent']):<15} {tenant['Status']:<12} {tenant['Move_In_Date']:<12}")
    else:
        report.append("  No tenants found")
    report.append("")
    
    # Properties Table
    report.append("PROPERTIES:")
    report.append("-" * 80)
    if isinstance(st.session_state.properties, pd.DataFrame) and not st.session_state.properties.empty:
        report.append(f"{'Address':<25} {'Type':<22} {'Units':<8} {'Occupied':<10} {'Available':<10}")
        report.append("-" * 80)
        for _, prop in st.session_state.properties.iterrows():
            available = prop['Units'] - prop['Occupancy']
            report.append(f"{prop['Address']:<25} {prop['Type']:<22} {prop['Units']:<8} {prop['Occupancy']:<10} {available:<10}")
    else:
        report.append("  No properties found")
    report.append("")
    
    # Payments Table with Timestamps
    report.append("PAYMENTS:")
    report.append("-" * 80)
    if isinstance(st.session_state.payments, pd.DataFrame) and not st.session_state.payments.empty:
        total_paid = st.session_state.payments[st.session_state.payments['Status'] == 'Paid']['Amount'].sum()
        total_pending = st.session_state.payments[st.session_state.payments['Status'] == 'Pending']['Amount'].sum()
        report.append(f"  Total Collected: {format_currency(total_paid)}")
        report.append(f"  Total Pending: {format_currency(total_pending)}")
        report.append("")
        report.append(f"{'Tenant':<20} {'Unit':<8} {'Amount':<15} {'Due Date':<12} {'Status':<12} {'Payment Time':<20}")
        report.append("-" * 80)
        for _, payment in st.session_state.payments.iterrows():
            payment_time = payment.get('Payment_Time', 'Not paid')
            if payment['Status'] == 'Paid':
                status_display = "✅ PAID"
            else:
                status_display = "⏳ PENDING"
            report.append(f"{payment['Tenant']:<20} {payment['Unit']:<8} {format_currency(payment['Amount']):<15} {payment['Due_Date']:<12} {status_display:<12} {payment_time:<20}")
    else:
        report.append("  No payments recorded")
    report.append("")
    
    # Maintenance Table
    report.append("MAINTENANCE:")
    report.append("-" * 80)
    if isinstance(st.session_state.maintenance, pd.DataFrame) and not st.session_state.maintenance.empty:
        open_issues = st.session_state.maintenance[st.session_state.maintenance['Status'] != 'Completed']
        report.append(f"  Open Issues: {len(open_issues)}")
        report.append("")
        report.append(f"{'ID':<8} {'Unit':<8} {'Issue':<35} {'Status':<15} {'Priority':<10} {'Reported':<12}")
        report.append("-" * 80)
        for _, issue in st.session_state.maintenance.iterrows():
            issue_short = issue['Issue'][:32] + "..." if len(issue['Issue']) > 35 else issue['Issue']
            report.append(f"{issue['ID']:<8} {issue['Unit']:<8} {issue_short:<35} {issue['Status']:<15} {issue['Priority']:<10} {issue['Reported']:<12}")
    else:
        report.append("  No maintenance issues")
    
    report.append("")
    report.append("=" * 80)
    report.append("End of Report")
    
    return "\n".join(report)

def generate_full_report_html():
    """Generate full system report with HTML table format for email"""
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #1B3A7A; text-align: center; }
            h2 { color: #1B3A7A; margin-top: 30px; }
            table { 
                border-collapse: collapse; 
                width: 100%; 
                margin: 10px 0;
                font-size: 12px;
            }
            th { 
                background-color: #1B3A7A; 
                color: white; 
                padding: 10px;
                text-align: left;
                border: 1px solid #ddd;
            }
            td { 
                padding: 8px; 
                border: 1px solid #ddd;
                text-align: left;
            }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .summary { 
                background-color: #f0f7ff; 
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }
            .status-paid { color: #27AE60; font-weight: bold; }
            .status-pending { color: #F39C12; font-weight: bold; }
            .status-overdue { color: #E74C3C; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🏠 TenantHub - System Report</h1>
        <p style="text-align: center; color: #666;">
            Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
        </p>
    """
    
    # Tenants Table with Property Type
    html += """
        <h2>👥 Tenants</h2>
    """
    if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
        html += """
        <table>
            <tr>
                <th>Name</th>
                <th>Property</th>
                <th>Type</th>
                <th>Unit</th>
                <th>Rent</th>
                <th>Status</th>
                <th>Move-In Date</th>
            </tr>
        """
        for _, tenant in st.session_state.tenants.iterrows():
            prop_type = tenant.get('Property_Type', 'N/A')
            html += f"""
            <tr>
                <td>{tenant['Name']}</td>
                <td>{tenant.get('Property', 'N/A')}</td>
                <td>{prop_type}</td>
                <td>{tenant['Unit']}</td>
                <td>{format_currency(tenant['Rent'])}</td>
                <td><span class="status-{tenant['Status'].lower()}">{tenant['Status']}</span></td>
                <td>{tenant['Move_In_Date']}</td>
            </tr>
            """
        html += "</table>"
    else:
        html += "<p>No tenants found</p>"
    
    # Properties Table
    html += """
        <h2>🏠 Properties</h2>
    """
    if isinstance(st.session_state.properties, pd.DataFrame) and not st.session_state.properties.empty:
        html += """
        <table>
            <tr>
                <th>Address</th>
                <th>Type</th>
                <th>Total Units</th>
                <th>Occupied</th>
                <th>Available</th>
                <th>Occupancy %</th>
            </tr>
        """
        for _, prop in st.session_state.properties.iterrows():
            available = prop['Units'] - prop['Occupancy']
            occupancy_pct = int((prop['Occupancy'] / prop['Units']) * 100) if prop['Units'] > 0 else 0
            html += f"""
            <tr>
                <td>{prop['Address']}</td>
                <td>{prop['Type']}</td>
                <td>{prop['Units']}</td>
                <td>{prop['Occupancy']}</td>
                <td>{available}</td>
                <td>{occupancy_pct}%</td>
            </tr>
            """
        html += "</table>"
    else:
        html += "<p>No properties found</p>"
    
    # Payments Table with Timestamps
    html += """
        <h2>💰 Payments</h2>
    """
    if isinstance(st.session_state.payments, pd.DataFrame) and not st.session_state.payments.empty:
        total_paid = st.session_state.payments[st.session_state.payments['Status'] == 'Paid']['Amount'].sum()
        total_pending = st.session_state.payments[st.session_state.payments['Status'] == 'Pending']['Amount'].sum()
        html += f"""
        <div class="summary">
            <strong>Total Collected:</strong> {format_currency(total_paid)} &nbsp;|&nbsp;
            <strong>Total Pending:</strong> {format_currency(total_pending)} &nbsp;|&nbsp;
            <strong>Total Records:</strong> {len(st.session_state.payments)}
        </div>
        <table>
            <tr>
                <th>Tenant</th>
                <th>Unit</th>
                <th>Amount</th>
                <th>Due Date</th>
                <th>Status</th>
                <th>Payment Time</th>
            </tr>
        """
        for _, payment in st.session_state.payments.iterrows():
            payment_time = payment.get('Payment_Time', 'Not paid')
            status_class = payment['Status'].lower()
            html += f"""
            <tr>
                <td>{payment['Tenant']}</td>
                <td>{payment['Unit']}</td>
                <td>{format_currency(payment['Amount'])}</td>
                <td>{payment['Due_Date']}</td>
                <td><span class="status-{status_class}">{payment['Status']}</span></td>
                <td>{payment_time}</td>
            </tr>
            """
        html += "</table>"
    else:
        html += "<p>No payments recorded</p>"
    
    # Maintenance Table
    html += """
        <h2>🔧 Maintenance</h2>
    """
    if isinstance(st.session_state.maintenance, pd.DataFrame) and not st.session_state.maintenance.empty:
        open_issues = st.session_state.maintenance[st.session_state.maintenance['Status'] != 'Completed']
        html += f"<p><strong>Open Issues:</strong> {len(open_issues)}</p>"
        html += """
        <table>
            <tr>
                <th>ID</th>
                <th>Unit</th>
                <th>Issue</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Reported</th>
                <th>Tenant</th>
            </tr>
        """
        for _, issue in st.session_state.maintenance.iterrows():
            html += f"""
            <tr>
                <td>{issue['ID']}</td>
                <td>{issue['Unit']}</td>
                <td>{issue['Issue']}</td>
                <td>{issue['Status']}</td>
                <td>{issue['Priority']}</td>
                <td>{issue['Reported']}</td>
                <td>{issue['Tenant']}</td>
            </tr>
            """
        html += "</table>"
    else:
        html += "<p>No maintenance issues</p>"
    
    html += """
        <hr>
        <p style="text-align: center; color: #999; font-size: 11px;">
            End of Report - Generated by TenantHub
        </p>
    </body>
    </html>
    """
    
    return html

def send_email_report_with_table(recipient_email, subject, html_content, csv_attachment=None, attachment_name=None):
    """Send email report with HTML table format"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        if csv_attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(csv_attachment.getvalue())
            encoders.encode_base64(part)
            if attachment_name:
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment_name}'
                )
            else:
                part.add_header(
                    'Content-Disposition',
                    'attachment; filename= report.csv'
                )
            msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True, "Email sent successfully!"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def format_currency(amount):
    """Format amount in Rwandan Francs"""
    return f"RWF {amount:,.0f}"

def send_tenant_info_email(tenant_name, email):
    """Send tenant information via email with table format"""
    if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
        tenant = st.session_state.tenants[st.session_state.tenants['Name'] == tenant_name]
        if not tenant.empty:
            tenant_data = tenant.iloc[0]
            
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #1B3A7A; }}
                    h2 {{ color: #1B3A7A; margin-top: 20px; }}
                    table {{ 
                        border-collapse: collapse; 
                        width: 100%; 
                        margin: 10px 0;
                        font-size: 12px;
                    }}
                    th {{ 
                        background-color: #1B3A7A; 
                        color: white; 
                        padding: 10px;
                        text-align: left;
                        border: 1px solid #ddd;
                    }}
                    td {{ 
                        padding: 8px; 
                        border: 1px solid #ddd;
                    }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>🏠 Tenant Information</h1>
                <h2>👤 {tenant_data['Name']}</h2>
                <table>
                    <tr><td><strong>Email:</strong></td><td>{tenant_data['Email']}</td></tr>
                    <tr><td><strong>Phone:</strong></td><td>{tenant_data['Phone']}</td></tr>
                    <tr><td><strong>Property:</strong></td><td>{tenant_data.get('Property', 'N/A')}</td></tr>
                    <tr><td><strong>Property Type:</strong></td><td>{tenant_data.get('Property_Type', 'N/A')}</td></tr>
                    <tr><td><strong>Unit:</strong></td><td>{tenant_data['Unit']}</td></tr>
                    <tr><td><strong>Status:</strong></td><td>{tenant_data['Status']}</td></tr>
                    <tr><td><strong>Monthly Rent:</strong></td><td>{format_currency(tenant_data['Rent'])}</td></tr>
                    <tr><td><strong>Move-in Date:</strong></td><td>{tenant_data['Move_In_Date']}</td></tr>
                </table>
                
                <h2>💰 Payment History</h2>
            """
            
            if isinstance(st.session_state.payments, pd.DataFrame) and not st.session_state.payments.empty:
                payments = st.session_state.payments[st.session_state.payments['Tenant'] == tenant_name]
                if not payments.empty:
                    html += """
                    <table>
                        <tr>
                            <th>Due Date</th>
                            <th>Amount</th>
                            <th>Status</th>
                            <th>Payment Time</th>
                        </tr>
                    """
                    for _, payment in payments.iterrows():
                        payment_time = payment.get('Payment_Time', 'Not paid')
                        html += f"""
                        <tr>
                            <td>{payment['Due_Date']}</td>
                            <td>{format_currency(payment['Amount'])}</td>
                            <td>{payment['Status']}</td>
                            <td>{payment_time}</td>
                        </tr>
                        """
                    html += "</table>"
                else:
                    html += "<p>No payments recorded</p>"
            else:
                html += "<p>No payments recorded</p>"
            
            html += """
            </body>
            </html>
            """
            
            success, message = send_email_report_with_table(
                EMAIL_RECIPIENT,
                f"Tenant Information - {tenant_name}",
                html
            )
            
            return success, message
    
    return False, "Tenant not found"

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="TenantHub - Property Management",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0C2461 0%, #1B3A7A 30%, #2A5298 60%, #4A90D9 100%);
        min-height: 100vh;
    }
    
    .main-content {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    
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
    
    .section-header {
        color: #1B3A7A !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        margin: 1rem 0 !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 3px solid #4A90D9 !important;
    }
    
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
    
    .save-indicator {
        background: #D5F5E3;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        color: #1A7A3A;
        border: 1px solid #2ECC71;
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
                load_all_data()
                st.rerun()
            else:
                st.error("❌ Invalid credentials!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

def logout():
    if st.sidebar.button("🚪 Logout", use_container_width=True, key="logout_button"):
        save_all_data()
        st.session_state.logged_in = False
        st.rerun()

# ==================== DATA MANAGEMENT ====================
def get_default_tenants():
    """Return empty dataframe with correct columns"""
    return pd.DataFrame(columns=['ID', 'Name', 'Email', 'Phone', 'Property', 'Property_Type', 'Property_ID', 'Unit', 'Status', 'Rent', 'Move_In_Date'])

def get_default_properties():
    """Return empty dataframe with correct columns"""
    return pd.DataFrame(columns=['ID', 'Address', 'City', 'Type', 'Units', 'Occupancy'])

def get_default_maintenance():
    """Return empty dataframe with correct columns"""
    return pd.DataFrame(columns=['ID', 'Unit', 'Issue', 'Status', 'Priority', 'Reported', 'Tenant'])

def get_default_payments():
    """Return empty dataframe with correct columns - includes Payment_Time field"""
    return pd.DataFrame(columns=['ID', 'Tenant', 'Unit', 'Amount', 'Due_Date', 'Status', 'Payment_Time'])

def init_data():
    """Initialize data from CSV files if they exist, otherwise use defaults"""
    ensure_data_dir()
    
    if 'tenants' not in st.session_state:
        st.session_state.tenants = load_data_from_csv('tenants.csv', get_default_tenants())
    if 'properties' not in st.session_state:
        st.session_state.properties = load_data_from_csv('properties.csv', get_default_properties())
    if 'maintenance' not in st.session_state:
        st.session_state.maintenance = load_data_from_csv('maintenance.csv', get_default_maintenance())
    if 'payments' not in st.session_state:
        st.session_state.payments = load_data_from_csv('payments.csv', get_default_payments())
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
                save_all_data()
                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ==================== PROPERTY OCCUPANCY MANAGEMENT ====================
def update_property_occupancy(property_name):
    """Update occupancy count for a specific property"""
    try:
        if isinstance(st.session_state.properties, pd.DataFrame) and not st.session_state.properties.empty:
            # Find property by name (case-insensitive)
            property_mask = st.session_state.properties['Address'].str.lower() == property_name.lower()
            if property_mask.any():
                if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
                    # Count active tenants for this property (case-insensitive)
                    if 'Property' in st.session_state.tenants.columns:
                        active_tenants = st.session_state.tenants[
                            (st.session_state.tenants['Property'].str.lower() == property_name.lower()) & 
                            (st.session_state.tenants['Status'] == 'Active')
                        ]
                        occupancy_count = len(active_tenants)
                    else:
                        occupancy_count = len(st.session_state.tenants[st.session_state.tenants['Status'] == 'Active'])
                    
                    # Update occupancy
                    idx = st.session_state.properties[property_mask].index[0]
                    st.session_state.properties.loc[idx, 'Occupancy'] = occupancy_count
                    save_all_data()
                    return True
        return False
    except Exception as e:
        print(f"Error updating occupancy for {property_name}: {e}")
        return False

def update_all_occupancy():
    """Update occupancy counts for all properties"""
    try:
        if isinstance(st.session_state.properties, pd.DataFrame) and not st.session_state.properties.empty:
            for _, prop in st.session_state.properties.iterrows():
                update_property_occupancy(prop['Address'])
            return True
        return False
    except Exception as e:
        print(f"Error updating all occupancy: {e}")
        return False

def get_available_properties():
    """Get list of properties with available units"""
    available = []
    if isinstance(st.session_state.properties, pd.DataFrame) and not st.session_state.properties.empty:
        for _, prop in st.session_state.properties.iterrows():
            if prop['Occupancy'] < prop['Units']:
                available.append({
                    'address': prop['Address'],
                    'available_units': prop['Units'] - prop['Occupancy'],
                    'total_units': prop['Units'],
                    'type': prop['Type'],
                    'id': prop['ID']
                })
    return available

# ==================== PAYMENT FUNCTIONS ====================
def check_payment_reminders():
    """Check for upcoming payment due dates and show reminders"""
    if isinstance(st.session_state.payments, pd.DataFrame) and not st.session_state.payments.empty:
        today = datetime.now().date()
        reminders = []
        
        for idx, row in st.session_state.payments.iterrows():
            if row['Status'] != 'Paid':
                try:
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
                except:
                    continue
        
        return reminders
    return []

def generate_next_payment_date(move_in_date):
    """Generate the next payment due date based on move-in date"""
    try:
        move_in = datetime.strptime(move_in_date, '%Y-%m-%d').date()
        today = datetime.now().date()
        
        day_of_month = move_in.day
        
        test_date = today
        for _ in range(12):
            year = test_date.year
            month = test_date.month
            
            try:
                last_day = pd.Timestamp(year=year, month=month, day=1).days_in_month
                due_day = min(day_of_month, last_day)
                due_date = datetime(year, month, due_day).date()
                
                if due_date >= today:
                    return due_date.strftime('%Y-%m-%d')
                
                if month == 12:
                    test_date = datetime(year + 1, 1, 1).date()
                else:
                    test_date = datetime(year, month + 1, 1).date()
            except:
                if month == 12:
                    test_date = datetime(year + 1, 1, 1).date()
                else:
                    test_date = datetime(year, month + 1, 1).date()
                continue
        
        return None
    except:
        return None

def auto_generate_payments():
    """Automatically generate payment records for all active tenants"""
    if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
        new_payments_added = 0
        
        for _, tenant in st.session_state.tenants.iterrows():
            if tenant['Status'] == 'Active':
                current_month = datetime.now().strftime('%Y-%m')
                existing_payment = st.session_state.payments[
                    (st.session_state.payments['Tenant'] == tenant['Name']) & 
                    (st.session_state.payments['Due_Date'].str[:7] == current_month)
                ]
                
                if existing_payment.empty:
                    next_due = generate_next_payment_date(tenant['Move_In_Date'])
                    if next_due:
                        new_payment = pd.DataFrame({
                            'ID': [len(st.session_state.payments) + 1],
                            'Tenant': [tenant['Name']],
                            'Unit': [tenant['Unit']],
                            'Amount': [tenant['Rent']],
                            'Due_Date': [next_due],
                            'Status': ['Pending'],
                            'Payment_Time': ['']
                        })
                        st.session_state.payments = pd.concat([st.session_state.payments, new_payment], ignore_index=True)
                        new_payments_added += 1
        
        if new_payments_added > 0:
            save_all_data()
            st.success(f"✅ Auto-generated {new_payments_added} new payment{'s' if new_payments_added > 1 else ''} for this month!")
        elif len(st.session_state.tenants) > 0:
            st.info("No new payments needed this month.")
        
        return new_payments_added
    return 0

def mark_payment_as_paid(payment_id):
    """Mark a payment as paid and record the timestamp"""
    try:
        if isinstance(st.session_state.payments, pd.DataFrame) and not st.session_state.payments.empty:
            # Ensure Payment_Time column exists
            if 'Payment_Time' not in st.session_state.payments.columns:
                st.session_state.payments['Payment_Time'] = ''
            
            df = st.session_state.payments
            idx = df[df['ID'] == payment_id].index
            if not idx.empty:
                df.at[idx[0], 'Status'] = 'Paid'
                df.at[idx[0], 'Payment_Time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                st.session_state.payments = df
                save_all_data()
                return True
        return False
    except Exception as e:
        print(f"Error marking payment as paid: {e}")
        return False

# ==================== PDF AGREEMENT GENERATOR ====================
def generate_agreement_pdf(tenant_name, property_name, property_type, unit, rent, move_in_date):
    """Generate a rental agreement PDF with terms and conditions"""
    if REPORTLAB_AVAILABLE:
        try:
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
            
            story = []
            
            story.append(Paragraph("RENTAL AGREEMENT", styles['CustomTitle']))
            story.append(Spacer(1, 0.25*inch))
            
            story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['CustomBody']))
            story.append(Spacer(1, 0.25*inch))
            
            story.append(Paragraph("PARTIES", styles['CustomHeading']))
            story.append(Paragraph(f"This Rental Agreement is made between TenantHub Property Management (hereinafter referred to as 'Landlord') and {tenant_name} (hereinafter referred to as 'Tenant').", styles['CustomBody']))
            story.append(Spacer(1, 0.25*inch))
            
            story.append(Paragraph("PROPERTY DETAILS", styles['CustomHeading']))
            story.append(Paragraph(f"Property: {property_name}", styles['CustomBody']))
            story.append(Paragraph(f"Property Type: {property_type}", styles['CustomBody']))
            story.append(Paragraph(f"Unit: {unit}", styles['CustomBody']))
            story.append(Paragraph(f"Monthly Rent: {format_currency(rent)}", styles['CustomBody']))
            story.append(Paragraph(f"Move-in Date: {move_in_date}", styles['CustomBody']))
            story.append(Spacer(1, 0.25*inch))
            
            story.append(Paragraph("TERMS AND CONDITIONS", styles['CustomHeading']))
            
            terms = [
                "1. RENT PAYMENT: Tenant agrees to pay the monthly rent on or before the 1st day of each month. Rent is due on the same day each month as the move-in date.",
                "2. LATE PAYMENT: A late fee of RWF 50,000 will be charged if rent is not received within 5 days after the due date.",
                "3. SECURITY DEPOSIT: A security deposit equal to one month's rent is required and will be held by Landlord.",
                "4. UTILITIES: Tenant is responsible for all utility costs including electricity, water, gas, and internet.",
                "5. MAINTENANCE: Tenant agrees to maintain the property in good condition and report any issues immediately.",
                "6. PETS: Pets are allowed only with prior written consent and additional pet deposit.",
                "7. SUBLEASING: Subleasing is not permitted without written consent from Landlord.",
                "8. NOTICE: Either party must provide 30 days written notice to terminate this agreement.",
                "9. RENT INCREASE: Rent may be increased with 60 days written notice.",
                "10. GOVERNING LAW: This agreement is governed by the laws of Rwanda.",
                "11. ENTIRE AGREEMENT: This document represents the entire agreement between parties.",
                "12. AMENDMENTS: Any amendments must be in writing and signed by both parties."
            ]
            
            for term in terms:
                story.append(Paragraph(term, styles['CustomBody']))
            
            story.append(Spacer(1, 0.25*inch))
            
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
            
            story.append(Paragraph("This agreement is legally binding. Please keep a copy for your records.", styles['CustomFooter']))
            
            doc.build(story)
            buffer.seek(0)
            return buffer
        except Exception as e:
            return generate_text_agreement(tenant_name, property_name, property_type, unit, rent, move_in_date)
    else:
        return generate_text_agreement(tenant_name, property_name, property_type, unit, rent, move_in_date)

def generate_text_agreement(tenant_name, property_name, property_type, unit, rent, move_in_date):
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
    Property: {property_name}
    Property Type: {property_type}
    Unit: {unit}
    Monthly Rent: {format_currency(rent)}
    Move-in Date: {move_in_date}
    
    TERMS AND CONDITIONS
    --------------------
    1. RENT PAYMENT: Tenant agrees to pay the monthly rent on or before the 
       1st day of each month. Rent is due on the same day each month as the 
       move-in date.
    
    2. LATE PAYMENT: A late fee of RWF 50,000 will be charged if rent is not 
       received within 5 days after the due date.
    
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
    
    10. GOVERNING LAW: This agreement is governed by the laws of Rwanda.
    
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
    try:
        tenant = st.session_state.tenants[st.session_state.tenants['ID'] == tenant_id]
        if not tenant.empty:
            property_name = tenant.iloc[0].get('Property', None)
            
            df = st.session_state.tenants
            df = df[df['ID'] != tenant_id]
            st.session_state.tenants = df.reset_index(drop=True)
            
            if property_name:
                update_property_occupancy(property_name)
            
            save_all_data()
            st.success("✅ Tenant deleted successfully!")
            st.rerun()
    except Exception as e:
        st.error(f"Error deleting tenant: {str(e)}")

def delete_property(prop_id):
    try:
        df = st.session_state.properties
        df = df[df['ID'] != prop_id]
        st.session_state.properties = df.reset_index(drop=True)
        save_all_data()
        st.success("✅ Property deleted successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting property: {str(e)}")

def delete_maintenance(maint_id):
    try:
        df = st.session_state.maintenance
        df = df[df['ID'] != maint_id]
        st.session_state.maintenance = df.reset_index(drop=True)
        save_all_data()
        st.success("✅ Maintenance request deleted!")
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting maintenance: {str(e)}")

def delete_payment(payment_id):
    try:
        df = st.session_state.payments
        df = df[df['ID'] != payment_id]
        st.session_state.payments = df.reset_index(drop=True)
        save_all_data()
        st.success("✅ Payment deleted successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error deleting payment: {str(e)}")

# ==================== EMAIL REPORT FUNCTIONS ====================
def show_email_report_section():
    """Display email report section in sidebar or main area"""
    st.markdown("### 📧 Email Reports")
    
    if st.button("📊 Send Full Report (Table)", use_container_width=True, key="email_full_report_table"):
        with st.spinner("Generating and sending report..."):
            html_content = generate_full_report_html()
            success, message = send_email_report_with_table(
                EMAIL_RECIPIENT,
                f"TenantHub Full Report - {datetime.now().strftime('%Y-%m-%d')}",
                html_content
            )
            if success:
                st.success("✅ Full report sent successfully!")
            else:
                st.error(f"❌ {message}")
    
    if st.button("📊 Send Full Report (Text)", use_container_width=True, key="email_full_report_text"):
        with st.spinner("Generating and sending report..."):
            report_text = generate_full_report_text()
            success, message = send_email_report(
                EMAIL_RECIPIENT,
                f"TenantHub Full Report - {datetime.now().strftime('%Y-%m-%d')}",
                report_text
            )
            if success:
                st.success("✅ Full report sent successfully!")
            else:
                st.error(f"❌ {message}")
    
    if st.button("👥 Send Tenant Report", use_container_width=True, key="email_tenant_report"):
        with st.spinner("Generating and sending report..."):
            csv_buffer = generate_tenant_report()
            if csv_buffer:
                success, message = send_email_report(
                    EMAIL_RECIPIENT,
                    f"Tenant Report - {datetime.now().strftime('%Y-%m-%d')}",
                    "Please find attached the tenant report.",
                    csv_buffer,
                    "tenant_report.csv"
                )
                if success:
                    st.success("✅ Tenant report sent successfully!")
                else:
                    st.error(f"❌ {message}")
            else:
                st.warning("No tenant data available")
    
    if st.button("💰 Send Payment Report", use_container_width=True, key="email_payment_report"):
        with st.spinner("Generating and sending report..."):
            csv_buffer = generate_payment_report()
            if csv_buffer:
                success, message = send_email_report(
                    EMAIL_RECIPIENT,
                    f"Payment Report - {datetime.now().strftime('%Y-%m-%d')}",
                    "Please find attached the payment report.",
                    csv_buffer,
                    "payment_report.csv"
                )
                if success:
                    st.success("✅ Payment report sent successfully!")
                else:
                    st.error(f"❌ {message}")
            else:
                st.warning("No payment data available")
    
    if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
        st.markdown("### 📤 Send Tenant Info")
        tenant_names = st.session_state.tenants['Name'].tolist()
        selected_tenant = st.selectbox("Select Tenant", tenant_names, key="email_tenant_select")
        
        if st.button("📧 Send Tenant Information", use_container_width=True, key="email_tenant_info"):
            with st.spinner("Sending tenant information..."):
                success, message = send_tenant_info_email(selected_tenant, EMAIL_RECIPIENT)
                if success:
                    st.success(f"✅ Tenant information sent successfully!")
                else:
                    st.error(f"❌ {message}")

# ==================== MAIN APP ====================
def show_header():
    st.markdown(f"""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>🏠 TenantHub</h1>
                <p>Property Management System - Rwanda</p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.9rem; opacity: 0.9;">👤 {st.session_state.get('username', 'Admin')}</div>
                <div style="font-size: 0.8rem; opacity: 0.7;">{datetime.now().strftime('%B %d, %Y')}</div>
                <div style="margin-top: 5px;">
                    <span class="save-indicator">💾 Data Saved</span>
                </div>
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
    
    overdue = 0
    if isinstance(payments_df, pd.DataFrame) and not payments_df.empty:
        today = datetime.now().date()
        for _, row in payments_df.iterrows():
            if row['Status'] != 'Paid':
                try:
                    due_date = datetime.strptime(row['Due_Date'], '%Y-%m-%d').date()
                    if due_date < today:
                        overdue += 1
                except:
                    continue
    
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
            <div class="metric-value">{format_currency(total_revenue)}</div>
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
                            <br>Amount: {format_currency(reminder['amount'])} - Due: {reminder['due_date']}
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
                            <br>Amount: {format_currency(reminder['amount'])} - Due: {reminder['due_date']}
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
                # Property selection with type - FIXED
                available_props = get_available_properties()
                if available_props:
                    # Create display options with property type
                    prop_options = []
                    prop_addresses = []
                    prop_types = []
                    prop_ids = []
                    
                    for p in available_props:
                        display_text = f"{p['address']} ({p['type']}) - {p['available_units']} units available"
                        prop_options.append(display_text)
                        prop_addresses.append(p['address'])
                        prop_types.append(p['type'])
                        prop_ids.append(p['id'])
                    
                    selected_index = st.selectbox(
                        "Select Property", 
                        range(len(prop_options)),
                        format_func=lambda i: prop_options[i],
                        key="tenant_property_index"
                    )
                    
                    property_name = prop_addresses[selected_index] if selected_index is not None else ""
                    property_type = prop_types[selected_index] if selected_index is not None else ""
                    property_id = prop_ids[selected_index] if selected_index is not None else ""
                    
                    # Get available units for this property
                    if property_name:
                        property_data = st.session_state.properties[st.session_state.properties['Address'] == property_name]
                        if not property_data.empty:
                            max_units = property_data.iloc[0]['Units']
                            unit_options = [f"Unit {i+1}" for i in range(max_units)]
                            
                            # Get occupied units - case insensitive
                            if 'Property' in st.session_state.tenants.columns:
                                occupied_units = st.session_state.tenants[
                                    (st.session_state.tenants['Property'].str.lower() == property_name.lower()) & 
                                    (st.session_state.tenants['Status'] == 'Active')
                                ]['Unit'].tolist()
                            else:
                                occupied_units = []
                            
                            available_units = [u for u in unit_options if u not in occupied_units]
                            
                            if available_units:
                                unit = st.selectbox("Select Unit", available_units, key="tenant_unit")
                            else:
                                st.warning("⚠️ No available units in this property!")
                                unit = ""
                        else:
                            unit = st.text_input("Unit Number", placeholder="3B", key="tenant_unit_input")
                    else:
                        unit = st.text_input("Unit Number", placeholder="3B", key="tenant_unit_input")
                else:
                    st.warning("⚠️ No properties with available units! Please add a property first.")
                    property_name = ""
                    property_type = ""
                    property_id = ""
                    unit = st.text_input("Unit Number", placeholder="3B", key="tenant_unit_input")
                
                rent = st.number_input("Monthly Rent (RWF)", min_value=0, step=5000, key="tenant_rent")
                status = st.selectbox("Status", ["Active", "Pending", "In Progress", "New"], key="tenant_status")
            
            move_in_date = st.date_input("Move-in Date", datetime.now(), key="tenant_move_in")
            
            col_c, col_d = st.columns(2)
            with col_c:
                if st.button("💾 Add Tenant", key="add_tenant_btn"):
                    if name and unit and rent > 0 and property_name:
                        new_id = len(st.session_state.tenants) + 1
                        
                        # Ensure columns exist
                        if 'Property' not in st.session_state.tenants.columns:
                            st.session_state.tenants['Property'] = ''
                        if 'Property_Type' not in st.session_state.tenants.columns:
                            st.session_state.tenants['Property_Type'] = ''
                        if 'Property_ID' not in st.session_state.tenants.columns:
                            st.session_state.tenants['Property_ID'] = ''
                        
                        new_tenant = pd.DataFrame({
                            'ID': [new_id],
                            'Name': [name],
                            'Email': [email],
                            'Phone': [phone],
                            'Property': [property_name],
                            'Property_Type': [property_type],
                            'Property_ID': [property_id],
                            'Unit': [unit],
                            'Status': [status],
                            'Rent': [rent],
                            'Move_In_Date': [move_in_date.strftime('%Y-%m-%d')]
                        })
                        st.session_state.tenants = pd.concat([st.session_state.tenants, new_tenant], ignore_index=True)
                        
                        # Update occupancy for the property
                        update_property_occupancy(property_name)
                        
                        # Generate first payment
                        next_due = generate_next_payment_date(move_in_date.strftime('%Y-%m-%d'))
                        if next_due:
                            new_payment = pd.DataFrame({
                                'ID': [len(st.session_state.payments) + 1],
                                'Tenant': [name],
                                'Unit': [unit],
                                'Amount': [rent],
                                'Due_Date': [next_due],
                                'Status': ['Pending'],
                                'Payment_Time': ['']
                            })
                            st.session_state.payments = pd.concat([st.session_state.payments, new_payment], ignore_index=True)
                        
                        save_all_data()
                        st.success(f"✅ Tenant added to {property_name} ({property_type})! Next payment due: {next_due if next_due else 'N/A'} ({format_currency(rent)})")
                        st.rerun()
                    else:
                        if not property_name:
                            st.warning("Please select a property with available units!")
                        else:
                            st.warning("Please fill in all required fields!")
            
            with col_d:
                if st.button("📄 Generate Agreement", key="gen_agreement_btn"):
                    if name and property_name and unit and rent > 0:
                        pdf_buffer = generate_agreement_pdf(name, property_name, property_type, unit, rent, move_in_date.strftime('%Y-%m-%d'))
                        file_extension = "pdf" if REPORTLAB_AVAILABLE else "txt"
                        st.download_button(
                            label=f"📥 Download Agreement.{file_extension}",
                            data=pdf_buffer,
                            file_name=f"agreement_{name}_{unit}.{file_extension}",
                            mime="application/pdf" if REPORTLAB_AVAILABLE else "text/plain",
                            use_container_width=True,
                            key=f"download_agreement_{name}_{datetime.now().timestamp()}"
                        )
                    else:
                        st.warning("Please fill in all fields first!")
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.tenants, 'tenants.csv')
            upload_csv('Tenants')
        with st.expander("📧 Email Reports", expanded=False):
            show_email_report_section()
        if st.button("🔄 Generate All Payments", use_container_width=True, key="auto_gen_payments"):
            with st.spinner("Generating payments..."):
                auto_generate_payments()
    
    if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
        search = st.text_input("🔍 Search tenants", placeholder="Search by name or unit...", key="tenant_search")
        
        filtered_df = st.session_state.tenants.copy()
        if search:
            filtered_df = filtered_df[
                filtered_df['Name'].str.contains(search, case=False, na=False) | 
                filtered_df['Unit'].str.contains(search, case=False, na=False) |
                filtered_df['Property'].str.contains(search, case=False, na=False)
            ]
        
        for idx, row in filtered_df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1.8, 1, 1, 0.8, 0.8])
            
            with col1:
                st.markdown(f"**{row['Name']}**")
                st.caption(row['Email'])
            
            with col2:
                st.write(f"Property: {row.get('Property', 'N/A')}")
                st.write(f"Type: {row.get('Property_Type', 'N/A')}")
                st.write(f"Unit: {row['Unit']}")
                st.caption(f"Move-in: {row['Move_In_Date']}")
            
            with col3:
                st.write(f"Rent: {format_currency(row['Rent'])}")
                status_class = {
                    "Active": "status-active",
                    "Pending": "status-pending",
                    "In Progress": "status-inprogress",
                    "New": "status-new"
                }.get(row['Status'], "status-active")
                st.markdown(f'<span class="status-badge {status_class}">{row["Status"]}</span>', unsafe_allow_html=True)
            
            with col4:
                if st.button(f"📄 Agreement", key=f"agreement_{row['ID']}_{idx}", use_container_width=True):
                    property_name = row.get('Property', 'N/A')
                    property_type = row.get('Property_Type', 'N/A')
                    pdf_buffer = generate_agreement_pdf(row['Name'], property_name, property_type, row['Unit'], row['Rent'], row['Move_In_Date'])
                    file_extension = "pdf" if REPORTLAB_AVAILABLE else "txt"
                    st.download_button(
                        label=f"📥 Download.{file_extension}",
                        data=pdf_buffer,
                        file_name=f"agreement_{row['Name']}_{row['Unit']}.{file_extension}",
                        mime="application/pdf" if REPORTLAB_AVAILABLE else "text/plain",
                        use_container_width=True,
                        key=f"download_agreement_{row['ID']}_{datetime.now().timestamp()}"
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
                            new_property = st.text_input("Property", value=row.get('Property', ''), key=f"edit_property_{row['ID']}")
                            new_property_type = st.text_input("Property Type", value=row.get('Property_Type', ''), key=f"edit_property_type_{row['ID']}")
                            new_unit = st.text_input("Unit", value=row['Unit'], key=f"edit_unit_{row['ID']}")
                            new_rent = st.number_input("Rent (RWF)", value=float(row['Rent']), step=5000.0, key=f"edit_rent_{row['ID']}")
                            new_status = st.selectbox("Status", ["Active", "Pending", "In Progress", "New"], 
                                                     index=["Active", "Pending", "In Progress", "New"].index(row['Status']),
                                                     key=f"edit_status_{row['ID']}")
                        
                        col_c, col_d = st.columns(2)
                        with col_c:
                            if st.button("💾 Save", key=f"save_tenant_{row['ID']}"):
                                old_property = row.get('Property', None)
                                df = st.session_state.tenants
                                df.loc[df['ID'] == row['ID'], 'Name'] = new_name
                                df.loc[df['ID'] == row['ID'], 'Email'] = new_email
                                df.loc[df['ID'] == row['ID'], 'Phone'] = new_phone
                                if 'Property' in df.columns:
                                    df.loc[df['ID'] == row['ID'], 'Property'] = new_property
                                if 'Property_Type' in df.columns:
                                    df.loc[df['ID'] == row['ID'], 'Property_Type'] = new_property_type
                                df.loc[df['ID'] == row['ID'], 'Unit'] = new_unit
                                df.loc[df['ID'] == row['ID'], 'Rent'] = new_rent
                                df.loc[df['ID'] == row['ID'], 'Status'] = new_status
                                st.session_state.tenants = df
                                
                                if old_property:
                                    update_property_occupancy(old_property)
                                if new_property:
                                    update_property_occupancy(new_property)
                                
                                save_all_data()
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
        st.info("No tenants added yet. Please add a property first, then add tenants.")
    
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
                prop_type = st.selectbox(
                    "Property Type", 
                    ["1 Room & Dining Room", "1 Room", "2 Room & Dining Room"], 
                    key="prop_type"
                )
                units = st.number_input("Total Units", min_value=1, step=1, value=1, key="prop_units")
                st.info("Occupancy will be automatically calculated based on assigned tenants.")
            
            if st.button("💾 Add Property", key="add_prop_btn"):
                if address and city:
                    new_id = len(st.session_state.properties) + 1
                    new_property = pd.DataFrame({
                        'ID': [new_id],
                        'Address': [address],
                        'City': [city],
                        'Type': [prop_type],
                        'Units': [units],
                        'Occupancy': [0]
                    })
                    st.session_state.properties = pd.concat([st.session_state.properties, new_property], ignore_index=True)
                    save_all_data()
                    st.success("✅ Property added! You can now add tenants to this property.")
                    st.rerun()
                else:
                    st.warning("Please fill in all required fields!")
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.properties, 'properties.csv')
            upload_csv('Properties')
        if st.button("🔄 Update Occupancy", use_container_width=True, key="update_occupancy"):
            with st.spinner("Updating occupancy..."):
                update_all_occupancy()
                st.success("✅ Occupancy updated!")
    
    if isinstance(st.session_state.properties, pd.DataFrame) and not st.session_state.properties.empty:
        update_all_occupancy()
        
        for idx, row in st.session_state.properties.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{row['Address']}**")
                st.caption(row['City'])
            
            with col2:
                st.write(f"Type: {row['Type']}")
                st.write(f"Units: {row['Units']} ({row['Occupancy']} occupied)")
                available = row['Units'] - row['Occupancy']
                st.write(f"Available: {available}")
            
            with col3:
                try:
                    occupancy_pct = int((row['Occupancy'] / row['Units']) * 100) if row['Units'] > 0 else 0
                    st.progress(occupancy_pct / 100)
                    st.caption(f"{occupancy_pct}% occupied")
                except:
                    st.caption("N/A")
            
            with col4:
                if st.button(f"✏️ Edit", key=f"edit_prop_{row['ID']}_{idx}", use_container_width=True):
                    with st.expander(f"✏️ Editing: {row['Address']}", expanded=True):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            new_address = st.text_input("Address", value=row['Address'], key=f"edit_prop_addr_{row['ID']}")
                            new_city = st.text_input("City", value=row['City'], key=f"edit_prop_city_{row['ID']}")
                        
                        with col_b:
                            new_type = st.selectbox(
                                "Type", 
                                ["1 Room & Dining Room", "1 Room", "2 Room & Dining Room"],
                                index=["1 Room & Dining Room", "1 Room", "2 Room & Dining Room"].index(row['Type']) if row['Type'] in ["1 Room & Dining Room", "1 Room", "2 Room & Dining Room"] else 0,
                                key=f"edit_prop_type_{row['ID']}"
                            )
                            new_units = st.number_input("Total Units", value=int(row['Units']), min_value=1, step=1, key=f"edit_prop_units_{row['ID']}")
                            st.info("Occupancy is automatically calculated based on assigned tenants.")
                        
                        col_c, col_d = st.columns(2)
                        with col_c:
                            if st.button("💾 Save", key=f"save_prop_{row['ID']}"):
                                df = st.session_state.properties
                                df.loc[df['ID'] == row['ID'], 'Address'] = new_address
                                df.loc[df['ID'] == row['ID'], 'City'] = new_city
                                df.loc[df['ID'] == row['ID'], 'Type'] = new_type
                                df.loc[df['ID'] == row['ID'], 'Units'] = new_units
                                st.session_state.properties = df
                                update_all_occupancy()
                                save_all_data()
                                st.success("✅ Property updated!")
                                st.rerun()
                        
                        with col_d:
                            if st.button("❌ Cancel", key=f"cancel_prop_{row['ID']}"):
                                st.rerun()
            
            with col5:
                if st.button(f"🗑️ Delete", key=f"del_prop_{row['ID']}_{idx}", use_container_width=True):
                    has_tenants = False
                    if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
                        if 'Property' in st.session_state.tenants.columns:
                            has_tenants = len(st.session_state.tenants[st.session_state.tenants['Property'].str.lower() == row['Address'].lower()]) > 0
                    
                    if has_tenants:
                        st.error("❌ Cannot delete property with assigned tenants! Please remove tenants first.")
                    else:
                        delete_property(row['ID'])
            
            st.markdown("---")
    else:
        st.info("No properties added yet. Add a property to get started!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_maintenance():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">🔧 Maintenance Management</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander("➕ Report New Issue", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
                    unit_options = st.session_state.tenants['Unit'].tolist()
                    unit = st.selectbox("Unit Number", unit_options, key="maint_unit")
                    tenant_data = st.session_state.tenants[st.session_state.tenants['Unit'] == unit]
                    tenant_name = tenant_data.iloc[0]['Name'] if not tenant_data.empty else ""
                else:
                    unit = st.text_input("Unit Number", placeholder="3B", key="maint_unit")
                    tenant_name = ""
                
                tenant = st.text_input("Tenant Name", value=tenant_name, key="maint_tenant")
                issue = st.text_area("Issue Description", placeholder="Describe the issue...", key="maint_issue")
            
            with col_b:
                priority = st.selectbox("Priority", ["High", "Medium", "Low"], key="maint_priority")
                status = st.selectbox("Status", ["New", "Active", "In Progress", "Completed"], key="maint_status")
            
            if st.button("💾 Report Issue", key="add_maint_btn"):
                if unit and tenant and issue:
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
                    save_all_data()
                    st.success("✅ Issue reported!")
                    st.rerun()
                else:
                    st.warning("Please fill in all required fields!")
    
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
                st.caption(f"Reported: {row['Reported']}")
            
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
                                save_all_data()
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
    
    show_reminders()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🔄 Generate Payments for This Month", use_container_width=True, key="auto_gen_payments_btn"):
            with st.spinner("Generating payments..."):
                auto_generate_payments()
        
        with st.expander("➕ Record Payment Manually", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                if isinstance(st.session_state.tenants, pd.DataFrame) and not st.session_state.tenants.empty:
                    tenant_options = st.session_state.tenants['Name'].tolist()
                    selected_tenant = st.selectbox("Select Tenant", tenant_options, key="payment_tenant_select")
                    
                    tenant_data = st.session_state.tenants[st.session_state.tenants['Name'] == selected_tenant]
                    if not tenant_data.empty:
                        unit = tenant_data.iloc[0]['Unit']
                        rent = tenant_data.iloc[0]['Rent']
                    else:
                        unit = ""
                        rent = 0
                else:
                    selected_tenant = st.text_input("Tenant Name", placeholder="John Smith", key="payment_tenant")
                    unit = st.text_input("Unit Number", placeholder="3B", key="payment_unit")
                    rent = 0
                
                amount = st.number_input("Amount (RWF)", value=float(rent) if rent > 0 else 0.0, min_value=0.0, step=5000.0, key="payment_amount")
            
            with col_b:
                payment_date = st.date_input("Payment Date", datetime.now(), key="payment_date")
                status = st.selectbox("Status", ["Paid", "Pending", "Overdue"], key="payment_status")
                if status == "Paid":
                    payment_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    payment_time = ""
            
            if st.button("💾 Record Payment", key="add_payment_btn"):
                if selected_tenant and unit and amount > 0:
                    new_id = len(st.session_state.payments) + 1
                    new_payment = pd.DataFrame({
                        'ID': [new_id],
                        'Tenant': [selected_tenant],
                        'Unit': [unit],
                        'Amount': [amount],
                        'Due_Date': [payment_date.strftime('%Y-%m-%d')],
                        'Status': [status],
                        'Payment_Time': [payment_time if status == "Paid" else ""]
                    })
                    st.session_state.payments = pd.concat([st.session_state.payments, new_payment], ignore_index=True)
                    save_all_data()
                    if status == "Paid":
                        st.success(f"✅ Payment recorded! Paid on: {payment_time} ({format_currency(amount)})")
                    else:
                        st.success(f"✅ Payment recorded! ({format_currency(amount)})")
                    st.rerun()
                else:
                    st.warning("Please fill in all required fields!")
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.payments, 'payments.csv')
            upload_csv('Payments')
        with st.expander("📧 Email Reports", expanded=False):
            show_email_report_section()
    
    if isinstance(st.session_state.payments, pd.DataFrame) and not st.session_state.payments.empty:
        total_collected = st.session_state.payments[st.session_state.payments['Status'] == 'Paid']['Amount'].sum()
        total_pending = st.session_state.payments[st.session_state.payments['Status'] == 'Pending']['Amount'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Collected", format_currency(total_collected))
        with col2:
            st.metric("⏳ Pending", format_currency(total_pending))
        with col3:
            st.metric("📊 Total Records", len(st.session_state.payments))
        
        filter_status = st.selectbox("Filter by status", ["All", "Paid", "Pending", "Overdue"], key="payment_filter")
        
        filtered_df = st.session_state.payments.copy()
        if filter_status != "All":
            filtered_df = filtered_df[filtered_df['Status'] == filter_status]
        
        filtered_df = filtered_df.sort_values('Due_Date', ascending=False)
        
        for idx, row in filtered_df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1, 1.2, 1.2, 0.8, 0.8])
            
            with col1:
                st.markdown(f"**{row['Tenant']}**")
                st.caption(f"Unit {row['Unit']}")
            
            with col2:
                st.write(format_currency(row['Amount']))
            
            with col3:
                st.caption(f"Due: {row['Due_Date']}")
                if row['Status'] == 'Paid' and row.get('Payment_Time'):
                    st.caption(f"✅ Paid: {row['Payment_Time']}")
            
            with col4:
                status_class = {
                    "Paid": "status-paid",
                    "Pending": "status-pending",
                    "Overdue": "status-overdue"
                }.get(row['Status'], "status-active")
                st.markdown(f'<span class="status-badge {status_class}">{row["Status"]}</span>', unsafe_allow_html=True)
                
                if row['Status'] != 'Paid':
                    if st.button(f"✅ Mark Paid", key=f"mark_paid_{row['ID']}_{idx}", use_container_width=True):
                        if mark_payment_as_paid(row['ID']):
                            st.success(f"✅ Payment marked as paid on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to mark payment as paid.")
            
            with col5:
                if st.button(f"✏️ Edit", key=f"edit_payment_{row['ID']}_{idx}", use_container_width=True):
                    with st.expander(f"✏️ Editing: {row['Tenant']}", expanded=True):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            new_tenant = st.text_input("Tenant", value=row['Tenant'], key=f"edit_pay_tenant_{row['ID']}")
                            new_unit = st.text_input("Unit", value=row['Unit'], key=f"edit_pay_unit_{row['ID']}")
                        
                        with col_b:
                            new_amount = st.number_input("Amount (RWF)", value=float(row['Amount']), step=5000.0, key=f"edit_pay_amount_{row['ID']}")
                            new_status = st.selectbox("Status", ["Paid", "Pending", "Overdue"],
                                                     index=["Paid", "Pending", "Overdue"].index(row['Status']),
                                                     key=f"edit_pay_status_{row['ID']}")
                            if new_status == "Paid" and row['Status'] != "Paid":
                                new_payment_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                new_payment_time = row.get('Payment_Time', '')
                        
                        col_c, col_d = st.columns(2)
                        with col_c:
                            if st.button("💾 Save", key=f"save_payment_{row['ID']}"):
                                try:
                                    df = st.session_state.payments
                                    df.loc[df['ID'] == row['ID'], 'Tenant'] = new_tenant
                                    df.loc[df['ID'] == row['ID'], 'Unit'] = new_unit
                                    df.loc[df['ID'] == row['ID'], 'Amount'] = new_amount
                                    df.loc[df['ID'] == row['ID'], 'Status'] = new_status
                                    if new_status == "Paid":
                                        df.loc[df['ID'] == row['ID'], 'Payment_Time'] = new_payment_time
                                    st.session_state.payments = df
                                    save_all_data()
                                    st.success("✅ Payment updated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating payment: {str(e)}")
                        
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
            <p style="color: #888; font-size: 0.8rem;">Rwanda 🇷🇼</p>
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
        
        if isinstance(st.session_state.properties, pd.DataFrame) and not st.session_state.properties.empty:
            total_units = st.session_state.properties['Units'].sum()
            total_occupied = st.session_state.properties['Occupancy'].sum()
            available_units = total_units - total_occupied
            st.metric("Available Units", available_units)
        
        st.markdown("---")
        
        if st.button("🔄 Auto-Generate Payments", use_container_width=True, key="sidebar_auto_gen"):
            with st.spinner("Generating payments..."):
                auto_generate_payments()
        
        st.markdown("---")
        
        st.markdown("### 📧 Email Reports")
        if st.button("📊 Full Report (HTML Table)", use_container_width=True, key="sidebar_full_report_html"):
            with st.spinner("Generating and sending report..."):
                html_content = generate_full_report_html()
                success, message = send_email_report_with_table(
                    EMAIL_RECIPIENT,
                    f"TenantHub Full Report - {datetime.now().strftime('%Y-%m-%d')}",
                    html_content
                )
                if success:
                    st.success("✅ Report sent!")
                else:
                    st.error(f"❌ {message}")
        
        if st.button("📊 Full Report (Text)", use_container_width=True, key="sidebar_full_report_text"):
            with st.spinner("Generating and sending report..."):
                report_text = generate_full_report_text()
                success, message = send_email_report(
                    EMAIL_RECIPIENT,
                    f"TenantHub Full Report - {datetime.now().strftime('%Y-%m-%d')}",
                    report_text
                )
                if success:
                    st.success("✅ Report sent!")
                else:
                    st.error(f"❌ {message}")
        
        st.markdown("---")
        
        if st.button("💾 Save Data Now", use_container_width=True, key="save_data_btn"):
            save_all_data()
            st.success("✅ Data saved successfully!")
        
        if st.button("🔄 Reset to Default Data", use_container_width=True, key="reset_data_btn"):
            reset_to_defaults()
            st.rerun()
        
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
