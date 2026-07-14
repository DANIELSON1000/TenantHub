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

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    /* Main styling */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #006fc7 0%, #00a8ff 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,111,199,0.3);
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
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        border-left: 5px solid #006fc7;
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
    }
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    .dashboard-card.green { border-left-color: #00b894; }
    .dashboard-card.orange { border-left-color: #fdcb6e; }
    .dashboard-card.purple { border-left-color: #6c5ce7; }
    .dashboard-card.red { border-left-color: #e17055; }
    
    .metric-value {
        font-size: 2.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #006fc7, #00a8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
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
        animation: pulse 2s infinite;
    }
    .status-active { background: #d4edda; color: #155724; border: 2px solid #28a745; }
    .status-pending { background: #fff3cd; color: #856404; border: 2px solid #ffc107; }
    .status-inprogress { background: #cce5ff; color: #004085; border: 2px solid #007bff; }
    .status-new { background: #f8d7da; color: #721c24; border: 2px solid #dc3545; }
    .status-completed { background: #d1ecf1; color: #0c5460; border: 2px solid #17a2b8; }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #006fc7, #00a8ff);
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(0,111,199,0.4);
    }
    .stButton > button:active {
        transform: scale(0.95);
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
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: white;
        border-right: 2px solid #e9ecef;
    }
    
    /* Login box */
    .login-box {
        background: white;
        padding: 3rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        max-width: 400px;
        margin: 2rem auto;
        animation: fadeInUp 0.8s ease-out;
    }
    .login-box h2 {
        text-align: center;
        color: #006fc7;
        margin-bottom: 2rem;
    }
    
    /* Data tables */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .dataframe thead {
        background: linear-gradient(135deg, #006fc7, #00a8ff);
        color: white;
    }
    
    /* File upload */
    .upload-area {
        border: 2px dashed #006fc7;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: #f8f9fa;
        transition: all 0.3s ease;
    }
    .upload-area:hover {
        background: #e3f2fd;
        border-color: #00a8ff;
    }
</style>
""", unsafe_allow_html=True)

# ==================== AUTHENTICATION ====================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
        <h1 style="color: #006fc7; font-size: 3rem;">🏠 TenantHub</h1>
        <p style="color: #666; font-size: 1.2rem;">Property Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h2>🔐 Admin Login</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.button("Login", use_container_width=True):
            # Simple authentication (change these credentials)
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Invalid credentials! Please try again.")
        
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
        st.session_state.username = None
        st.rerun()

# ==================== DATA MANAGEMENT ====================
def load_data():
    """Load data from session state or CSV files"""
    if 'tenants' not in st.session_state:
        # Sample data
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

def save_to_csv(df, filename):
    """Save DataFrame to CSV"""
    try:
        # Create data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
        df.to_csv(f'data/{filename}', index=False)
        return True
    except Exception as e:
        st.error(f"Error saving {filename}: {str(e)}")
        return False

def load_from_csv(filename):
    """Load DataFrame from CSV"""
    try:
        if os.path.exists(f'data/{filename}'):
            return pd.read_csv(f'data/{filename}')
        return None
    except Exception as e:
        st.error(f"Error loading {filename}: {str(e)}")
        return None

def download_csv(df, filename):
    """Create CSV download button"""
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
        f"Upload {df_type} CSV",
        type=['csv'],
        key=f"upload_{df_type}"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Successfully loaded {len(df)} records!")
            
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
            st.error(f"Error loading CSV: {str(e)}")

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
    
    total_tenants = len(st.session_state.tenants)
    total_properties = len(st.session_state.properties)
    total_revenue = st.session_state.tenants['Rent'].sum() if not st.session_state.tenants.empty else 0
    active_maintenance = len(st.session_state.maintenance[st.session_state.maintenance['Status'] != 'Completed']) if not st.session_state.maintenance.empty else 0
    
    with col1:
        st.markdown(f"""
        <div class="dashboard-card green">
            <div class="metric-label">👥 Total Tenants</div>
            <div class="metric-value">{total_tenants}</div>
            <div style="font-size: 0.85rem; color: #666;">Active: {len(st.session_state.tenants[st.session_state.tenants['Status'] == 'Active']) if not st.session_state.tenants.empty else 0}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="dashboard-card orange">
            <div class="metric-label">🏠 Properties</div>
            <div class="metric-value">{total_properties}</div>
            <div style="font-size: 0.85rem; color: #666;">Total Units: {st.session_state.properties['Units'].sum() if not st.session_state.properties.empty else 0}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="dashboard-card purple">
            <div class="metric-label">💰 Monthly Revenue</div>
            <div class="metric-value">${total_revenue:,}</div>
            <div style="font-size: 0.85rem; color: #666;">From {total_tenants} tenants</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="dashboard-card red">
            <div class="metric-label">🔧 Maintenance</div>
            <div class="metric-value">{active_maintenance}</div>
            <div style="font-size: 0.85rem; color: #666;">Open requests</div>
        </div>
        """, unsafe_allow_html=True)

def show_tenants():
    """Display tenants management"""
    st.markdown("### 👥 Tenant Management")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Add tenant form
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
            
            if st.button("💾 Add Tenant", use_container_width=True):
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
                save_to_csv(st.session_state.tenants, 'tenants.csv')
                st.success("✅ Tenant added successfully!")
                st.rerun()
    
    with col2:
        # CSV actions
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.tenants, 'tenants.csv')
            upload_csv('Tenants')
    
    # Display tenants table
    if not st.session_state.tenants.empty:
        # Search and filter
        col_search, col_filter = st.columns([2, 1])
        with col_search:
            search = st.text_input("🔍 Search tenants", placeholder="Search by name or unit...")
        with col_filter:
            status_filter = st.selectbox("Filter by status", ["All"] + list(st.session_state.tenants['Status'].unique()))
        
        # Apply filters
        filtered_df = st.session_state.tenants.copy()
        if search:
            filtered_df = filtered_df[filtered_df['Name'].str.contains(search, case=False, na=False) | 
                                      filtered_df['Unit'].str.contains(search, case=False, na=False)]
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['Status'] == status_filter]
        
        # Display with colors
        def color_status(val):
            colors = {
                'Active': 'background-color: #d4edda; color: #155724',
                'Pending': 'background-color: #fff3cd; color: #856404',
                'In Progress': 'background-color: #cce5ff; color: #004085',
                'New': 'background-color: #f8d7da; color: #721c24'
            }
            return colors.get(val, '')
        
        styled_df = filtered_df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Delete functionality
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Delete Selected", use_container_width=True):
                st.warning("Select records to delete")
    else:
        st.info("No tenants added yet. Click 'Add New Tenant' to get started.")

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
            
            if st.button("💾 Add Property", use_container_width=True):
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
                save_to_csv(st.session_state.properties, 'properties.csv')
                st.success("✅ Property added successfully!")
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
            
            if st.button("💾 Report Issue", use_container_width=True):
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
                save_to_csv(st.session_state.maintenance, 'maintenance.csv')
                st.success("✅ Issue reported successfully!")
                st.rerun()
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.maintenance, 'maintenance.csv')
            upload_csv('Maintenance')
    
    if not st.session_state.maintenance.empty:
        # Filter
        priority_filter = st.selectbox("Filter by priority", ["All", "High", "Medium", "Low"])
        
        filtered_df = st.session_state.maintenance.copy()
        if priority_filter != "All":
            filtered_df = filtered_df[filtered_df['Priority'] == priority_filter]
        
        def color_priority(val):
            colors = {
                'High': 'background-color: #f8d7da; color: #721c24; font-weight: bold',
                'Medium': 'background-color: #fff3cd; color: #856404',
                'Low': 'background-color: #d4edda; color: #155724'
            }
            return colors.get(val, '')
        
        styled_df = filtered_df.style.applymap(color_priority, subset=['Priority'])
        st.dataframe(styled_df, use_container_width=True, height=400)
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
            
            if st.button("💾 Record Payment", use_container_width=True):
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
                save_to_csv(st.session_state.payments, 'payments.csv')
                st.success("✅ Payment recorded successfully!")
                st.rerun()
    
    with col2:
        with st.expander("📊 Data Management", expanded=False):
            download_csv(st.session_state.payments, 'payments.csv')
            upload_csv('Payments')
    
    if not st.session_state.payments.empty:
        # Summary
        total_collected = st.session_state.payments[st.session_state.payments['Status'] == 'Paid']['Amount'].sum()
        pending_total = st.session_state.payments[st.session_state.payments['Status'] == 'Pending']['Amount'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Collected", f"${total_collected:,}")
        with col2:
            st.metric("⏳ Pending", f"${pending_total:,}")
        with col3:
            st.metric("📊 Total Records", len(st.session_state.payments))
        
        def color_status(val):
            colors = {
                'Paid': 'background-color: #d4edda; color: #155724',
                'Pending': 'background-color: #fff3cd; color: #856404',
                'Overdue': 'background-color: #f8d7da; color: #721c24'
            }
            return colors.get(val, '')
        
        styled_df = st.session_state.payments.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.info("No payments recorded yet.")

# ==================== SIDEBAR ====================
def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="color: #006fc7; margin: 0;">🏠</h1>
            <h3 style="color: #006fc7; margin: 0;">TenantHub</h3>
            <p style="color: #666; font-size: 0.8rem;">v2.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
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
            st.metric("Tenants", len(st.session_state.tenants), delta="+2")
        with col2:
            st.metric("Properties", len(st.session_state.properties))
        
        st.markdown("---")
        
        # Logout
        logout()
        
        return page

# ==================== MAIN APP ====================
def main():
    """Main application entry point"""
    
    # Check authentication
    if not check_auth():
        return
    
    # Load data
    load_data()
    
    # Show header
    show_header()
    
    # Show sidebar and get current page
    page = show_sidebar()
    
    # Show content based on page
    if page == "📊 Dashboard":
        show_metrics()
        
        # Additional dashboard content
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="dashboard-card">
                <h3>📋 Recent Activity</h3>
            """, unsafe_allow_html=True)
            
            activities = [
                "🔵 New tenant signed lease for Unit 3B",
                "🟢 Maintenance request resolved for Unit 12A",
                "🟡 Rent payment received from Unit 7C",
                "🔴 Inspection scheduled for Unit 5D",
                "🟢 New property added: 654 Maple Dr"
            ]
            for activity in activities:
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; 
                            border-bottom: 1px solid #eee;">
                    <span>{activity}</span>
                    <span style="color: #999; font-size: 0.8rem;">{datetime.now().strftime('%H:%M')}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="dashboard-card">
                <h3>📈 Revenue Overview</h3>
            """, unsafe_allow_html=True)
            
            # Sample chart
            chart_data = {
                'Mon': 1200,
                'Tue': 1400,
                'Wed': 1100,
                'Thu': 1600,
                'Fri': 1800,
                'Sat': 900,
                'Sun': 700
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

# ==================== RUN APP ====================
if __name__ == "__main__":
    main()
