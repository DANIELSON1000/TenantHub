import streamlit as st
import os
import json
import time
from datetime import datetime, timedelta
import random

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="TenantHub",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CUSTOM CSS ====================
hide_streamlit_style = """
    <style>
    /* Hide Streamlit default UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        margin: 0;
        padding: 0;
    }
    .stApp > header {
        display: none;
    }
    .stApp > div {
        padding: 0;
    }
    
    /* Custom styles */
    .main-header {
        background: linear-gradient(135deg, #006fc7 0%, #0159a1 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    .dashboard-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        border-left: 4px solid #006fc7;
        transition: transform 0.2s;
    }
    .dashboard-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #006fc7;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-active { background: #d4edda; color: #155724; }
    .status-pending { background: #fff3cd; color: #856404; }
    .status-inprogress { background: #cce5ff; color: #004085; }
    .status-new { background: #f8d7da; color: #721c24; }
    .status-completed { background: #d1ecf1; color: #0c5460; }
    
    .tenant-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s;
    }
    .tenant-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    }
    .property-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 0.5rem;
        border-left: 3px solid #006fc7;
    }
    .sidebar-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .btn-primary {
        background: #006fc7;
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        font-weight: 600;
    }
    .btn-primary:hover {
        background: #0159a1;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==================== DATA MANAGEMENT ====================
class TenantHubData:
    """Manage application data"""
    
    def __init__(self):
        self.initialize_data()
    
    def initialize_data(self):
        """Initialize or load data"""
        if 'tenants' not in st.session_state:
            st.session_state.tenants = [
                {"id": 1, "name": "John Smith", "email": "john@email.com", "phone": "(555) 123-4567", 
                 "unit": "3B", "status": "Active", "rent": 1200, "lease_start": "2024-01-01", "lease_end": "2024-12-31"},
                {"id": 2, "name": "Sarah Johnson", "email": "sarah@email.com", "phone": "(555) 234-5678", 
                 "unit": "7C", "status": "Active", "rent": 1400, "lease_start": "2024-03-15", "lease_end": "2025-03-14"},
                {"id": 3, "name": "Mike Davis", "email": "mike@email.com", "phone": "(555) 345-6789", 
                 "unit": "12A", "status": "Pending", "rent": 1600, "lease_start": "2024-06-01", "lease_end": "2025-05-31"},
                {"id": 4, "name": "Emily Brown", "email": "emily@email.com", "phone": "(555) 456-7890", 
                 "unit": "5D", "status": "Active", "rent": 1100, "lease_start": "2023-11-01", "lease_end": "2024-10-31"},
                {"id": 5, "name": "David Wilson", "email": "david@email.com", "phone": "(555) 567-8901", 
                 "unit": "9E", "status": "Active", "rent": 1500, "lease_start": "2024-02-01", "lease_end": "2025-01-31"},
                {"id": 6, "name": "Lisa Anderson", "email": "lisa@email.com", "phone": "(555) 678-9012", 
                 "unit": "2F", "status": "In Progress", "rent": 1300, "lease_start": "2024-05-01", "lease_end": "2025-04-30"},
            ]
        
        if 'properties' not in st.session_state:
            st.session_state.properties = [
                {"id": 1, "address": "123 Main St", "city": "Springfield", "units": 12, "occupancy": 10, "type": "Apartment"},
                {"id": 2, "address": "456 Oak Ave", "city": "Riverside", "units": 8, "occupancy": 7, "type": "Townhouse"},
                {"id": 3, "address": "789 Pine Rd", "city": "Lakewood", "units": 16, "occupancy": 15, "type": "Apartment"},
                {"id": 4, "address": "321 Elm St", "city": "Springfield", "units": 6, "occupancy": 5, "type": "Duplex"},
                {"id": 5, "address": "654 Maple Dr", "city": "Riverside", "units": 4, "occupancy": 4, "type": "Single Family"},
            ]
        
        if 'maintenance' not in st.session_state:
            st.session_state.maintenance = [
                {"id": "M-001", "unit": "3B", "issue": "Leaky faucet in kitchen", "status": "In Progress", 
                 "priority": "Medium", "reported": "2024-10-20", "tenant": "John Smith"},
                {"id": "M-002", "unit": "7C", "issue": "Broken AC unit", "status": "New", 
                 "priority": "High", "reported": "2024-10-22", "tenant": "Sarah Johnson"},
                {"id": "M-003", "unit": "12A", "issue": "Electrical outlet not working", "status": "Active", 
                 "priority": "Low", "reported": "2024-10-21", "tenant": "Mike Davis"},
                {"id": "M-004", "unit": "5D", "issue": "Water heater malfunction", "status": "Completed", 
                 "priority": "High", "reported": "2024-10-18", "tenant": "Emily Brown"},
            ]
        
        if 'payments' not in st.session_state:
            st.session_state.payments = [
                {"id": 1, "tenant": "John Smith", "unit": "3B", "amount": 1200, "date": "2024-10-01", "status": "Paid"},
                {"id": 2, "tenant": "Sarah Johnson", "unit": "7C", "amount": 1400, "date": "2024-10-05", "status": "Paid"},
                {"id": 3, "tenant": "Emily Brown", "unit": "5D", "amount": 1100, "date": "2024-10-10", "status": "Pending"},
                {"id": 4, "tenant": "David Wilson", "unit": "9E", "amount": 1500, "date": "2024-10-15", "status": "Paid"},
            ]

data = TenantHubData()

# ==================== DASHBOARD FUNCTIONS ====================

def show_header():
    """Display the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🏠 TenantHub</h1>
        <p>Property Management Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

def show_metrics():
    """Display key metrics"""
    total_properties = len(st.session_state.properties)
    total_units = sum(p["units"] for p in st.session_state.properties)
    occupied_units = sum(p["occupancy"] for p in st.session_state.properties)
    total_tenants = len(st.session_state.tenants)
    total_revenue = sum(t["rent"] for t in st.session_state.tenants if t["status"] == "Active")
    
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("🏠 Properties", total_properties),
        ("👥 Tenants", total_tenants),
        ("💰 Monthly Revenue", f"${total_revenue:,}"),
        ("📊 Occupancy", f"{int((occupied_units/total_units)*100)}%")
    ]
    
    for col, (label, value) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div class="dashboard-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

def show_quick_actions():
    """Display quick action buttons"""
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Add Tenant", use_container_width=True):
            st.session_state.show_add_tenant = True
    
    with col2:
        if st.button("🏠 Add Property", use_container_width=True):
            st.session_state.show_add_property = True
    
    with col3:
        if st.button("🔧 Report Issue", use_container_width=True):
            st.session_state.show_report_issue = True
    
    with col4:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state.show_reports = True

def show_recent_activity():
    """Display recent activity"""
    st.markdown("### 📋 Recent Activity")
    
    activities = [
        {"time": "2 hours ago", "text": "🟢 Maintenance request resolved for Unit 12A"},
        {"time": "5 hours ago", "text": "🔵 New tenant signed lease for Unit 3B"},
        {"time": "1 day ago", "text": "🟡 Rent payment received from Unit 7C"},
        {"time": "2 days ago", "text": "🔴 Inspection scheduled for Unit 5D"},
        {"time": "3 days ago", "text": "🟢 Maintenance request submitted for Unit 9E"},
    ]
    
    for activity in activities:
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; 
                    border-bottom: 1px solid #eee;">
            <span>{activity['text']}</span>
            <span style="color: #999; font-size: 0.9rem;">{activity['time']}</span>
        </div>
        """, unsafe_allow_html=True)

def show_tenants_tab():
    """Display tenants tab"""
    st.markdown("### 👥 Tenant Directory")
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("🔍 Search tenants", placeholder="Search by name or unit...")
    with col2:
        status_filter = st.selectbox("Filter by status", ["All", "Active", "Pending", "In Progress"])
    
    # Display tenants
    filtered_tenants = st.session_state.tenants
    
    if search:
        filtered_tenants = [t for t in filtered_tenants 
                          if search.lower() in t["name"].lower() or search.lower() in t["unit"].lower()]
    
    if status_filter != "All":
        filtered_tenants = [t for t in filtered_tenants if t["status"] == status_filter]
    
    for tenant in filtered_tenants:
        status_class = {
            "Active": "status-active",
            "Pending": "status-pending",
            "In Progress": "status-inprogress",
            "New": "status-new"
        }.get(tenant["status"], "status-active")
        
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.markdown(f"""
            <div>
                <strong>{tenant['name']}</strong>
                <div style="font-size: 0.9rem; color: #666;">{tenant['email']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div>
                <div>Unit: <strong>{tenant['unit']}</strong></div>
                <div style="font-size: 0.9rem; color: #666;">Rent: ${tenant['rent']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div>
                <span class="status-badge {status_class}">{tenant['status']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            if st.button(f"View", key=f"view_{tenant['id']}"):
                st.session_state.selected_tenant = tenant
                st.session_state.show_tenant_detail = True

def show_properties_tab():
    """Display properties tab"""
    st.markdown("### 🏠 Properties")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Property", use_container_width=True):
            st.session_state.show_add_property = True
    
    for prop in st.session_state.properties:
        occupancy_pct = int((prop["occupancy"] / prop["units"]) * 100)
        
        st.markdown(f"""
        <div class="property-card">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h4 style="margin: 0;">{prop['address']}</h4>
                    <div style="color: #666; font-size: 0.9rem;">{prop['city']} • {prop['type']}</div>
                </div>
                <div style="text-align: right;">
                    <div><strong>{prop['occupancy']}/{prop['units']}</strong> units</div>
                    <div style="font-size: 0.9rem; color: #666;">{occupancy_pct}% occupied</div>
                </div>
            </div>
            <div style="margin-top: 0.5rem; background: #e9ecef; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: #006fc7; height: 100%; width: {occupancy_pct}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_maintenance_tab():
    """Display maintenance tab"""
    st.markdown("### 🔧 Maintenance Requests")
    
    col1, col2 = st.columns([2, 1])
    with col2:
        if st.button("➕ Report Issue", use_container_width=True):
            st.session_state.show_report_issue = True
    
    # Filter maintenance
    priority_filter = st.selectbox("Filter by priority", ["All", "High", "Medium", "Low"], key="priority_filter")
    
    filtered_maintenance = st.session_state.maintenance
    if priority_filter != "All":
        filtered_maintenance = [m for m in filtered_maintenance if m["priority"] == priority_filter]
    
    for req in filtered_maintenance:
        status_class = {
            "Active": "status-active",
            "New": "status-new",
            "In Progress": "status-inprogress",
            "Completed": "status-completed",
            "Pending": "status-pending"
        }.get(req["status"], "status-active")
        
        priority_color = {
            "High": "#dc3545",
            "Medium": "#ffc107",
            "Low": "#28a745"
        }.get(req["priority"], "#6c757d")
        
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; 
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 0.5rem;
                    border-left: 4px solid {priority_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>#{req['id']}</strong> - {req['issue']}
                    <div style="font-size: 0.9rem; color: #666;">
                        Unit {req['unit']} • {req['tenant']}
                    </div>
                </div>
                <div style="text-align: right;">
                    <span class="status-badge {status_class}">{req['status']}</span>
                    <div style="font-size: 0.8rem; color: #999; margin-top: 0.25rem;">
                        ⚡ {req['priority']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_payments_tab():
    """Display payments tab"""
    st.markdown("### 💰 Payments")
    
    col1, col2 = st.columns(2)
    with col1:
        total_paid = sum(p["amount"] for p in st.session_state.payments if p["status"] == "Paid")
        st.metric("Total Collected", f"${total_paid:,}")
    with col2:
        pending_payments = [p for p in st.session_state.payments if p["status"] == "Pending"]
        st.metric("Pending Payments", len(pending_payments))
    
    for payment in st.session_state.payments:
        status_color = "#28a745" if payment["status"] == "Paid" else "#ffc107"
        
        st.markdown(f"""
        <div style="background: white; padding: 1rem; border-radius: 8px; 
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{payment['tenant']}</strong>
                    <div style="font-size: 0.9rem; color: #666;">Unit {payment['unit']}</div>
                </div>
                <div style="text-align: right;">
                    <div><strong>${payment['amount']}</strong></div>
                    <div style="font-size: 0.9rem; color: #666;">{payment['date']}</div>
                </div>
                <div>
                    <span style="color: {status_color}; font-weight: 600;">{payment['status']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_tenant_detail():
    """Display tenant detail view"""
    if 'selected_tenant' in st.session_state and st.session_state.selected_tenant:
        tenant = st.session_state.selected_tenant
        
        with st.expander(f"👤 {tenant['name']} - Details", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **Contact Information**
                - 📧 {tenant['email']}
                - 📱 {tenant['phone']}
                - 🏠 Unit {tenant['unit']}
                - 📊 Status: {tenant['status']}
                """)
            
            with col2:
                st.markdown(f"""
                **Lease Information**
                - 💰 Rent: ${tenant['rent']}/month
                - 📅 Lease Start: {tenant['lease_start']}
                - 📅 Lease End: {tenant['lease_end']}
                - 📆 Days Remaining: {calculate_days_remaining(tenant['lease_end'])}
                """)
            
            if st.button("Close", key="close_tenant"):
                st.session_state.show_tenant_detail = False
                st.session_state.selected_tenant = None

def calculate_days_remaining(lease_end):
    """Calculate days remaining on lease"""
    try:
        end_date = datetime.strptime(lease_end, "%Y-%m-%d")
        days = (end_date - datetime.now()).days
        return f"{days} days" if days > 0 else "Expired"
    except:
        return "N/A"

# ==================== SIDEBAR ====================
def show_sidebar():
    """Display sidebar with navigation and quick info"""
    with st.sidebar:
        st.markdown("### 🏠 TenantHub")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "👥 Tenants", "🏠 Properties", "🔧 Maintenance", "💰 Payments"]
        )
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("### 📊 Quick Stats")
        st.markdown(f"""
        <div class="sidebar-card">
            <div>👥 Total Tenants: <strong>{len(st.session_state.tenants)}</strong></div>
            <div>🏠 Properties: <strong>{len(st.session_state.properties)}</strong></div>
            <div>🔧 Open Issues: <strong>{len([m for m in st.session_state.maintenance if m['status'] != 'Completed'])}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Upcoming events
        st.markdown("### 📅 Upcoming")
        st.markdown("""
        <div class="sidebar-card">
            <div>📋 Inspection - Unit 5D</div>
            <div style="font-size: 0.9rem; color: #666;">Tomorrow</div>
            <hr style="margin: 0.5rem 0;">
            <div>🔧 Maintenance - Unit 3B</div>
            <div style="font-size: 0.9rem; color: #666;">Oct 25</div>
        </div>
        """, unsafe_allow_html=True)
        
        return page

# ==================== MAIN APP ====================
def main():
    """Main application entry point"""
    
    # Show header
    show_header()
    
    # Show sidebar and get current page
    page = show_sidebar()
    
    # Handle tenant detail view
    if 'show_tenant_detail' in st.session_state and st.session_state.show_tenant_detail:
        show_tenant_detail()
        return
    
    # Show content based on page
    if page == "📊 Dashboard":
        show_metrics()
        col1, col2 = st.columns([2, 1])
        with col1:
            show_recent_activity()
        with col2:
            st.markdown("### 📈 Revenue Chart")
            # Generate some sample chart data
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
        
        show_quick_actions()
    
    elif page == "👥 Tenants":
        show_tenants_tab()
    
    elif page == "🏠 Properties":
        show_properties_tab()
    
    elif page == "🔧 Maintenance":
        show_maintenance_tab()
    
    elif page == "💰 Payments":
        show_payments_tab()

# ==================== RUN APP ====================
if __name__ == "__main__":
    main()
