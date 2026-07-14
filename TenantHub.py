import streamlit as st
import os
import subprocess
import sys
import json
from pathlib import Path
import time

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="TenantHub",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== HIDE STREAMLIT UI ====================
hide_streamlit_style = """
    <style>
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
    iframe {
        width: 100vw;
        height: 100vh;
        border: none;
        margin: 0;
        padding: 0;
        position: fixed;
        top: 0;
        left: 0;
    }
    /* Custom dashboard styles */
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
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==================== BUILD REACT APP ====================
def build_react_app():
    """Build the React app for production"""
    build_dir = Path("dist")
    
    if build_dir.exists():
        return True
    
    with st.spinner("Building React application... This may take a moment..."):
        # Check for node_modules
        if not Path("node_modules").exists():
            st.info("📦 Installing dependencies...")
            result = subprocess.run(
                ["npm", "install"], 
                capture_output=True, 
                text=True
            )
            if result.returncode != 0:
                st.error(f"Failed to install dependencies: {result.stderr}")
                return False
        
        # Build the app
        st.info("🔨 Building application...")
        result = subprocess.run(
            ["npm", "run", "build"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            st.error(f"Build failed: {result.stderr}")
            return False
        
        st.success("✅ Build completed successfully!")
        return True

# ==================== SERVE REACT APP ====================
def serve_react_app():
    """Serve the built React app"""
    try:
        with open("dist/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Fix asset paths for Streamlit
        import re
        html_content = re.sub(r'"/', './', html_content)
        html_content = re.sub(r'src="/', 'src="./', html_content)
        html_content = re.sub(r'href="/', 'href="./', html_content)
        
        # Read actual assets
        css_files = list(Path("dist/assets").glob("*.css"))
        js_files = list(Path("dist/assets").glob("*.js"))
        
        # Inject CSS and JS
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                css = f.read()
                st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        
        # Display the HTML
        st.components.v1.html(html_content, height=1000, scrolling=True)
        
        # Inject JS
        for js_file in js_files:
            with open(js_file, 'r', encoding='utf-8') as f:
                js = f.read()
                st.markdown(f"<script>{js}</script>", unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Error loading app: {e}")
        return False
    return True

# ==================== DASHBOARD UI (Fallback) ====================
def show_dashboard():
    """Display a fallback dashboard if React app isn't available"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏠 TenantHub</h1>
        <p>Property Management Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("Total Properties", "48", "📊"),
        ("Active Tenants", "92", "👥"),
        ("Monthly Revenue", "$124K", "💰"),
        ("Occupancy Rate", "94%", "📈")
    ]
    
    for col, (label, value, icon) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div class="dashboard-card">
                <div class="metric-label">{icon} {label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👥 Tenants", "🔧 Maintenance", "📅 Calendar"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            <div class="dashboard-card">
                <h3>Recent Activity</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid #eee;">🔵 New tenant signed lease for Unit 3B</li>
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid #eee;">🟢 Maintenance request resolved for Unit 12A</li>
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid #eee;">🟡 Rent payment received from Unit 7C</li>
                    <li style="padding: 0.5rem 0;">🔴 Inspection scheduled for Unit 5D</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Chart
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
        
        with col2:
            st.markdown("""
            <div class="dashboard-card">
                <h4>Quick Stats</h4>
                <div style="margin: 1rem 0;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>💰 Revenue</span>
                        <span><strong>$124,500</strong></span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                        <span>🏠 Properties</span>
                        <span><strong>48</strong></span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                        <span>👥 Tenants</span>
                        <span><strong>92</strong></span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("""
        <div class="dashboard-card">
            <h3>Tenant Directory</h3>
        </div>
        """, unsafe_allow_html=True)
        
        tenants = [
            {"name": "John Smith", "unit": "3B", "status": "Active"},
            {"name": "Sarah Johnson", "unit": "7C", "status": "Active"},
            {"name": "Mike Davis", "unit": "12A", "status": "Pending"},
            {"name": "Emily Brown", "unit": "5D", "status": "Active"},
            {"name": "David Wilson", "unit": "9E", "status": "Active"},
        ]
        
        for tenant in tenants:
            status_class = {
                "Active": "status-active",
                "Pending": "status-pending",
                "In Progress": "status-inprogress",
                "New": "status-new"
            }.get(tenant["status"], "status-active")
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 0.75rem; 
                        border-bottom: 1px solid #eee; align-items: center;">
                <div>
                    <strong>{tenant['name']}</strong>
                    <span style="color: #666; margin-left: 1rem;">Unit {tenant['unit']}</span>
                </div>
                <span class="status-badge {status_class}">{tenant['status']}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("""
        <div class="dashboard-card">
            <h3>Maintenance Requests</h3>
        </div>
        """, unsafe_allow_html=True)
        
        requests = [
            {"id": "M-001", "unit": "3B", "issue": "Leaky faucet", "status": "In Progress"},
            {"id": "M-002", "unit": "7C", "issue": "Broken AC", "status": "New"},
            {"id": "M-003", "unit": "12A", "issue": "Electrical issue", "status": "Active"},
        ]
        
        for req in requests:
            status_class = {
                "Active": "status-active",
                "New": "status-new",
                "In Progress": "status-inprogress",
                "Pending": "status-pending"
            }.get(req["status"], "status-active")
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 0.75rem; 
                        border-bottom: 1px solid #eee; align-items: center;">
                <div>
                    <strong>#{req['id']}</strong>
                    <span style="margin-left: 1rem;">Unit {req['unit']}</span>
                    <span style="color: #666; margin-left: 1rem;">{req['issue']}</span>
                </div>
                <span class="status-badge {status_class}">{req['status']}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("""
        <div class="dashboard-card">
            <h3>Upcoming Events</h3>
            <ul style="list-style: none; padding: 0;">
                <li style="padding: 0.5rem 0; border-bottom: 1px solid #eee;">
                    📅 <strong>Property Inspection</strong> - Unit 5D (Tomorrow)
                </li>
                <li style="padding: 0.5rem 0; border-bottom: 1px solid #eee;">
                    📅 <strong>Maintenance</strong> - Unit 3B (Oct 25)
                </li>
                <li style="padding: 0.5rem 0;">
                    📅 <strong>Tenant Meeting</strong> - Community Hall (Oct 28)
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ==================== MAIN APP ====================
def main():
    """Main application entry point"""
    
    # Check if running in Streamlit Cloud
    if os.getenv("STREAMLIT_CLOUD"):
        # Build and serve React app
        if build_react_app():
            serve_react_app()
        else:
            show_dashboard()
    else:
        # Local development mode
        st.sidebar.title("🚀 TenantHub")
        st.sidebar.markdown("---")
        
        option = st.sidebar.radio(
            "Choose Mode",
            ["📱 React App", "📊 Dashboard View"]
        )
        
        if option == "📱 React App":
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div style="text-align: center; padding: 2rem;">
                    <h2>🏠 TenantHub</h2>
                    <p style="color: #666;">Property Management Platform</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🚀 Build and Launch React App", use_container_width=True):
                    if build_react_app():
                        serve_react_app()
                    else:
                        st.error("Failed to build React app")
                
                st.markdown("---")
                st.info("💡 Tip: Make sure you have Node.js installed")
                
                if st.button("🔄 Start Dev Server", use_container_width=True):
                    try:
                        st.info("Starting development server...")
                        # Run dev server in background
                        import threading
                        import webbrowser
                        
                        def run_dev():
                            subprocess.run(["npm", "run", "dev", "--", "--host"], 
                                         capture_output=False)
                        
                        thread = threading.Thread(target=run_dev, daemon=True)
                        thread.start()
                        time.sleep(3)
                        
                        st.success("✅ Dev server started!")
                        st.info("Access at: http://localhost:5173")
                        st.components.v1.iframe("http://localhost:5173", 
                                               height=800, scrolling=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            show_dashboard()

# ==================== RUN APP ====================
if __name__ == "__main__":
    main()