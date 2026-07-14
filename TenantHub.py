import streamlit as st
import pandas as pd
import io
import os
import json
from datetime import datetime
import hashlib

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="TenantHub - Property Management",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SKY BLUE CUSTOM CSS ====================
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #E8F4FD 0%, #B8D8F0 100%);
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #4A90D9 0%, #6CB4EE 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(74,144,217,0.3);
        animation: slideDown 0.5s ease-out;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.8rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
        font-size: 1.2rem;
    }
    
    /* Cards */
    .dashboard-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(74,144,217,0.15);
        margin-bottom: 1rem;
        border-left: 5px solid #4A90D9;
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
    }
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(74,144,217,0.25);
    }
    .dashboard-card.green { border-left-color: #2ECC71; }
    .dashboard-card.orange { border-left-color: #F39C12; }
    .dashboard-card.purple { border-left-color: #9B59B6; }
    .dashboard-card.red { border-left-color: #E74C3C; }
    
    .metric-value {
        font-size: 2.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #4A90D9, #6CB4EE);
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
        background: linear-gradient(135deg, #4A90D9, #6CB4EE);
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
        box-shadow: 0 4px 15px rgba(74,144,217,0.4);
    }
    
    /* Animations */
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: white;
        border-right: 2px solid #D6EAF8;
    }
    
    /* Login box */
    .login-box {
        background: white;
        padding: 3rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(74,144,217,0.2);
        max-width: 400px;
        margin: 2rem auto;
        animation: fadeInUp 0.8s ease-out;
    }
    .login-box h2 {
        text-align: center;
        color: #4A90D9;
        margin-bottom: 2rem;
    }
    
    /* Data tables */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .dataframe thead {
        background: linear-gradient(135deg, #4A90D9, #6CB4EE);
        color: white;
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed #4A90D9;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: #F0F8FF;
        transition: all 0.3s ease;
    }
    .upload-area:hover {
        background: #D6EAF8;
        border-color: #6CB4EE;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #E8F4FD, #D6EAF8);
        border-radius: 10px;
        font-weight: 600;
        color: #4A90D9;
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
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #4A90D9; font-size: 3rem;">🏠 TenantHub</h1>
        <p style="color: #555; font-size: 1.2rem;">Property Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h2>🔐 Admin Login</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.button("Login"):
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Invalid credentials!")
        
        st.markdown("""
        <div style="text-align: center; margin-top: 1rem; color: #999; font-size: 0.9rem;">
            <p>Default: admin / admin123</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

def logout():
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ==================== DATA MANAGEMENT ====================
def init_data():
    """Initialize data with sample records"""
    if 'tenants' not in st.session_state:
        st.session_state.tenants = pd.DataFrame({
            'ID': [1, 2, 3, 4, 5],
            'Name': ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Emily Brown', 'David Wilson'],
            'Email': ['john@email.com', 'sarah@email.com', 'mike@email.com', 'emily@email.com', 'david@email.com'],
            'Phone': ['(555) 123-4567', '(555) 234-5678', '(555) 345-6789', '(555) 456-7890', '(555) 567-8901'],
            'Unit': ['3B', '7C', '12A', '5D', '9E'],
            'Status': ['Active', 'Active', 'Pending', 'Active', 'Active'],
            'Rent': [1200, 1400, 1600, 1100, 1500],
            'Lease_Start': ['2024-01-01', '2024-03-15', '2024-06-01', '2023-11-01', '2024-02-01'],
            'Lease_End': ['2024-12-31', '2025-03-14', '2025-05-31', '2024-10-31', '2025-01-31']
        })
    
    if 'properties' not in st.session_state:
        st.session_state.properties = pd.DataFrame({
            'ID': [1, 2, 3, 4, 5],
            'Address': ['123 Main St', '456 Oak Ave', '789 Pine Rd', '321 Elm St', '654 Maple Dr'],
            'City': ['Springfield', 'Riverside', 'Lakewood', 'Springfield', 'Riverside'],
            'Type': ['Apartment', 'Townhouse', 'Apartment', 'Duplex', 'Single Family'],
            'Units': [12, 8, 16, 6, 4],
            'Occupancy': [10, 7, 15, 5, 4]
        })
    
    if 'maintenance' not in st.session_state:
        st.session_state.maintenance = pd.DataFrame({
            'ID': ['M-001', 'M-002', 'M-003', 'M-004'],
            'Unit': ['3B', '7C', '12A', '5D'],
            'Issue': ['Leaky faucet in kitchen', 'Broken AC unit', 'Electrical outlet not working', 'Water heater malfunction'],
            'Status': ['In Progress', 'New', 'Active', 'Completed'],
            'Priority': ['Medium', 'High', 'Low', 'High'],
            'Reported': ['2024-10-20', '2024-10-22', '2024-10-21', '2024-10-18'],
            'Tenant': ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Emily Brown']
        })
    
    if 'payments' not in st.session_state:
        st.session_state.payments = pd.DataFrame({
            'ID': [1, 2, 3, 4],
            'Tenant': ['John Smith', 'Sarah Johnson', 'Emily Brown', 'David Wilson'],
            'Unit': ['3B', '7C', '5D', '9E'],
            'Amount': [1200, 1400, 1100, 1500],
            'Date': ['2024-10-01', '2024-10-05', '2024-10-10', '2024-10-15'],
            'Status': ['Paid', 'Paid', 'Pending', 'Paid']
        })

def download_csv(df, filename):
    """Create CSV download button"""
    if df is not None and not df.empty:
        csv = df.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {filename}",
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )

def upload_csv(df_type):
    """Handle CSV upload"""
    uploaded_file = st.file_uploader(
        f"📤 Upload {df_type} CSV",
        type=['csv'],
        key=f"upload_{df_type}"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Loaded {len(df)} records!")
            
            if st.button(f"Apply {df_type} Data", key=f"apply_{df_type}"):
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

# ==================== MAIN APP ====================
def show_header():
    """Display header with user info"""
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
    """Display metrics cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    tenants_df = st.session_state.tenants
    properties_df = st.session_state.properties
    maintenance_df = st.session_state.maintenance
    
    total_tenants = len(tenants_df) if not tenants_df.empty else 0
    total_properties = len(properties_df) if not properties_df.empty else 0
    total_revenue = tenants_df['Rent'].sum() if not tenants_df.empty else 0
    active_maintenance = len(maintenance_df[maintenance_df['Status'] != 'Completed']) if not maintenance_df.empty else 0
    
    with col1:
        st.markdown(f"""
        <div class="dashboard-card green">
            <div class="metric-label">👥 Total Tenants</div>
            <div class="metric-value">{total_tenants}</div>
            <div style="font-size: 0.85rem; color: #555;">Active: {len(tenants_df[tenants_df['Status'] == 'Active']) if not tenants_df.empty else 0}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="dashboard-card orange">
            <div class="metric-label">🏠 Properties</div>
            <div class="metric-value">{total_properties}</div>
            <div style="font-size: 0.85rem; color: #555;">Total Units: {properties_df['Units'].sum() if not properties_df.empty else 0}</div>
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
            <div class="metric-label">🔧 Maintenance</div>
            <div class="metric-value">{active_maintenance}</div>
            <div style="font-size: 0.85rem; color: #555;">Open requests</div>
        </div>
        """, unsafe_allow_html=True)

def show_tenants():
    """Display tenants management"""
    st.markdown("### 👥 Tenant Management")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander("➕ Add New Tenant", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                name = st.text_input("Full Name", placeholder="John Doe")
                email = st.text_input("Email", placeholder="john@email.com")
                phone = st.text_input("Phone", placeholder="(555) 123-4567")
            
            with col_b:
                unit = st.text_input("Unit Number", placeholder="3B")
                rent = st.number_input("Monthly Rent ($)", min_value=0, step=50)
                status = st.selectbox("Status", ["Active", "Pending", "In Progress", "New"])
            
            lease_start = st.date_input("Lease Start", datetime.now())
            lease_end = st.date_input("Lease End", datetime.now().replace(year=datetime.now().year + 1))
            
            if st.button("💾 Add Tenant"):
                new_id = len(st.session_state.tenants) + 1
                new_tenant = pd.DataFrame({
                    'ID': [new_id],
                    'Name': [name],
                    'Email': [email],
                    'Phone': [phone],
                    'Unit': [unit],
                    'Status': [status],
                    'Rent': [rent],
                    'Lease_Start': [lease_start.strftime('%Y-%m-%d')],
                    'Lease_End': [lease_end.strftime('%Y-%m-%d')]
                })
                st.session_state.tenants = pd.concat([st.session_state.tenants, new_tenant], ignore_index=True)
                st.success("✅ Tenant added!")
                st.rerun()
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.tenants, 'tenants.csv')
            upload_csv('Tenants')
    
    if not st.session_state.tenants.empty:
        search = st.text_input("🔍 Search tenants", placeholder="Search by name or unit...")
        
        filtered_df = st.session_state.tenants.copy()
        if search:
            filtered_df = filtered_df[
                filtered_df['Name'].str.contains(search, case=False, na=False) | 
                filtered_df['Unit'].str.contains(search, case=False, na=False)
            ]
        
        st.dataframe(filtered_df, use_container_width=True, height=400)
    else:
        st.info("No tenants added yet.")

def show_properties():
    """Display properties management"""
    st.markdown("### 🏠 Property Management")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander("➕ Add New Property", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                address = st.text_input("Address", placeholder="123 Main St")
                city = st.text_input("City", placeholder="Springfield")
            
            with col_b:
                prop_type = st.selectbox("Property Type", ["Apartment", "Townhouse", "Duplex", "Single Family", "Commercial"])
                units = st.number_input("Total Units", min_value=1, step=1)
                occupancy = st.number_input("Occupied Units", min_value=0, max_value=units, step=1)
            
            if st.button("💾 Add Property"):
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
    
    if not st.session_state.properties.empty:
        st.dataframe(st.session_state.properties, use_container_width=True, height=400)
    else:
        st.info("No properties added yet.")

def show_maintenance():
    """Display maintenance management"""
    st.markdown("### 🔧 Maintenance Management")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander("➕ Report New Issue", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                unit = st.text_input("Unit Number", placeholder="3B")
                tenant = st.text_input("Tenant Name", placeholder="John Smith")
                issue = st.text_area("Issue Description", placeholder="Describe the issue...")
            
            with col_b:
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])
                status = st.selectbox("Status", ["New", "Active", "In Progress", "Completed"])
            
            if st.button("💾 Report Issue"):
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
    
    if not st.session_state.maintenance.empty:
        priority_filter = st.selectbox("Filter by priority", ["All", "High", "Medium", "Low"])
        
        filtered_df = st.session_state.maintenance.copy()
        if priority_filter != "All":
            filtered_df = filtered_df[filtered_df['Priority'] == priority_filter]
        
        st.dataframe(filtered_df, use_container_width=True, height=400)
    else:
        st.info("No maintenance issues reported yet.")

def show_payments():
    """Display payments management"""
    st.markdown("### 💰 Payment Management")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        with st.expander("➕ Record Payment", expanded=False):
            col_a, col_b = st.columns(2)
            
            with col_a:
                tenant = st.text_input("Tenant Name", placeholder="John Smith")
                unit = st.text_input("Unit Number", placeholder="3B")
                amount = st.number_input("Amount ($)", min_value=0, step=10)
            
            with col_b:
                payment_date = st.date_input("Payment Date", datetime.now())
                status = st.selectbox("Status", ["Paid", "Pending", "Overdue"])
            
            if st.button("💾 Record Payment"):
                new_id = len(st.session_state.payments) + 1
                new_payment = pd.DataFrame({
                    'ID': [new_id],
                    'Tenant': [tenant],
                    'Unit': [unit],
                    'Amount': [amount],
                    'Date': [payment_date.strftime('%Y-%m-%d')],
                    'Status': [status]
                })
                st.session_state.payments = pd.concat([st.session_state.payments, new_payment], ignore_index=True)
                st.success("✅ Payment recorded!")
                st.rerun()
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.payments, 'payments.csv')
            upload_csv('Payments')
    
    if not st.session_state.payments.empty:
        total_collected = st.session_state.payments[st.session_state.payments['Status'] == 'Paid']['Amount'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Collected", f"${total_collected:,}")
        with col2:
            pending = st.session_state.payments[st.session_state.payments['Status'] == 'Pending']
            st.metric("⏳ Pending", len(pending))
        with col3:
            st.metric("📊 Total Records", len(st.session_state.payments))
        
        st.dataframe(st.session_state.payments, use_container_width=True, height=400)
    else:
        st.info("No payments recorded yet.")

# ==================== SIDEBAR ====================
def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="color: #4A90D9; margin: 0;">🏠</h1>
            <h3 style="color: #4A90D9; margin: 0;">TenantHub</h3>
            <p style="color: #888; font-size: 0.8rem;">v2.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        page = st.radio(
            "📋 Navigation",
            ["📊 Dashboard", "👥 Tenants", "🏠 Properties", "🔧 Maintenance", "💰 Payments"],
            index=0
        )
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("### 📊 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tenants", len(st.session_state.tenants))
        with col2:
            st.metric("Properties", len(st.session_state.properties))
        
        st.markdown("---")
        logout()
        
        return page

# ==================== MAIN ====================
def main():
    """Main application entry point"""
    
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
            <div class="dashboard-card">
                <h3>📋 Recent Activity</h3>
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
            <div class="dashboard-card">
                <h3>📈 Revenue Overview</h3>
            """, unsafe_allow_html=True)
            
            chart_data = {
                'Mon': 1200, 'Tue': 1400, 'Wed': 1100,
                'Thu': 1600, 'Fri': 1800, 'Sat': 900, 'Sun': 700
            }
            st.bar_chart(chart_data, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
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
