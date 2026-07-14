import streamlit as st
import os
import subprocess
import json
from pathlib import Path
import time
import sys

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
    .status-completed { background: #d1ecf1; color: #0c5460; }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==================== CHECK AND INSTALL NPM ====================
def check_npm_installed():
    """Check if npm is installed"""
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_npm_dependencies():
    """Install npm dependencies"""
    with st.spinner("📦 Installing npm dependencies..."):
        try:
            # Check if package.json exists
            if not Path("package.json").exists():
                st.error("package.json not found!")
                return False
            
            # Install dependencies
            result = subprocess.run(
                ["npm", "install"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                st.error(f"Failed to install dependencies: {result.stderr}")
                return False
            
            st.success("✅ npm dependencies installed successfully!")
            return True
        except Exception as e:
            st.error(f"Error installing dependencies: {str(e)}")
            return False

def build_react_app():
    """Build the React app"""
    build_dir = Path("dist")
    
    if build_dir.exists():
        return True
    
    with st.spinner("🔨 Building React application..."):
        try:
            # Install dependencies if needed
            if not Path("node_modules").exists():
                if not install_npm_dependencies():
                    return False
            
            # Build the app
            result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                st.error(f"Build failed: {result.stderr}")
                return False
            
            st.success("✅ Build completed successfully!")
            return True
        except Exception as e:
            st.error(f"Error building app: {str(e)}")
            return False

def serve_react_app():
    """Serve the built React app"""
    try:
        # Check if dist/index.html exists
        if not Path("dist/index.html").exists():
            st.warning("⚠️ Build not found. Please build the app first.")
            return False
        
        # Read the HTML file
        with open("dist/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Fix asset paths for Streamlit
        import re
        # Replace relative paths with absolute paths
        html_content = re.sub(r'src="/', 'src="./', html_content)
        html_content = re.sub(r'href="/', 'href="./', html_content)
        
        # Read and inject CSS files
        css_files = list(Path("dist/assets").glob("*.css"))
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                css = f.read()
                st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        
        # Display the HTML
        st.components.v1.html(html_content, height=1000, scrolling=True)
        
        # Read and inject JS files
        js_files = list(Path("dist/assets").glob("*.js"))
        for js_file in js_files:
            with open(js_file, 'r', encoding='utf-8') as f:
                js = f.read()
                st.markdown(f"<script>{js}</script>", unsafe_allow_html=True)
        
        return True
    except Exception as e:
        st.error(f"Error serving app: {str(e)}")
        return False

# ==================== DASHBOARD UI ====================
def show_dashboard():
    """Display the dashboard UI"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏠 TenantHub</h1>
        <p>Property Management Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics
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

# ==================== REACT APP INTERFACE ====================
def react_app_interface():
    """Interface for React app"""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 React App Mode</h1>
        <p>Build and deploy your React application</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if npm is installed
    if not check_npm_installed():
        st.error("❌ npm is not installed! Please ensure packages.txt is configured.")
        st.info("📝 Add 'nodejs' and 'npm' to packages.txt file in your repository.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🛠️ Build Options")
        
        if st.button("📦 Install Dependencies", use_container_width=True):
            install_npm_dependencies()
        
        if st.button("🔨 Build React App", use_container_width=True):
            build_react_app()
    
    with col2:
        st.markdown("### 📊 Status")
        
        # Check package.json
        if Path("package.json").exists():
            st.success("✅ package.json found")
        else:
            st.warning("⚠️ package.json not found")
        
        # Check node_modules
        if Path("node_modules").exists():
            st.success("✅ node_modules installed")
        else:
            st.warning("⚠️ node_modules not found")
        
        # Check build
        if Path("dist").exists():
            st.success("✅ Build exists")
        else:
            st.warning("⚠️ Build not found")
    
    # Try to serve the app if build exists
    if Path("dist").exists():
        st.markdown("---")
        st.markdown("### 🚀 Serving React App")
        if st.button("📱 Launch React App", use_container_width=True):
            serve_react_app()

# ==================== MAIN APP ====================
def main():
    """Main application entry point"""
    
    # Check if running in Streamlit Cloud
    is_cloud = os.getenv("STREAMLIT_CLOUD") is not None
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🏠 TenantHub")
        st.markdown("---")
        
        mode = st.radio(
            "Select Mode",
            ["📊 Dashboard", "🚀 React App"]
        )
        
        st.markdown("---")
        
        # Show environment info
        if is_cloud:
            st.info("☁️ Running on Streamlit Cloud")
        else:
            st.info("💻 Running locally")
        
        # Show npm status
        if check_npm_installed():
            st.success("✅ npm available")
        else:
            st.warning("⚠️ npm not available")
    
    # Main content
    if mode == "📊 Dashboard":
        show_dashboard()
    else:  # React App mode
        react_app_interface()

# ==================== RUN APP ====================
if __name__ == "__main__":
    main()
