# merch_app_website_style.py - Website-Style Navigation
import streamlit as st
import uuid

# Same imports as before
try:
    from merchagent.agent import root_agent
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import Runner
    from google.genai import types
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

# ============================================================================
# WEBSITE-STYLE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Chelsea FC Merchandise Agent",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide sidebar completely
)

# Website-style CSS with top navigation
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Hide Streamlit default elements for website look */
.stApp > header {
    background-color: transparent;
}

.stApp > header [data-testid="stHeader"] {
    display: none;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}

/* Website styling */
html, body, [class*="st"] {
    font-family: 'Inter', sans-serif;
    color: #1a1a1a;
}

.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

/* Top Navigation Bar */
.top-nav-container {
    background: white;
    padding: 0;
    margin: -1rem -1rem 2rem -1rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    position: sticky;
    top: 0;
    z-index: 1000;
}

.top-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.nav-logo {
    font-size: 1.8rem;
    font-weight: 700;
    color: #034694;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
}

.nav-links {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.nav-link {
    background: transparent !important;
    color: #64748b !important;
    border: none !important;
    font-weight: 500 !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
    font-size: 1rem !important;
    text-decoration: none !important;
    cursor: pointer !important;
}

.nav-link:hover {
    background: #f1f5f9 !important;
    color: #034694 !important;
    transform: translateY(-1px) !important;
}

.nav-link.active {
    background: #034694 !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(3, 70, 148, 0.3) !important;
}

/* Hero Section */
.hero-section {
    background: linear-gradient(135deg, #034694 0%, #1e3c72 100%);
    color: white;
    padding: 4rem 2rem;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 3rem;
    position: relative;
    overflow: hidden;
}

.hero-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(248,250,252,0.1)"/><circle cx="80" cy="40" r="1.5" fill="rgba(248,250,252,0.1)"/><circle cx="40" cy="80" r="1" fill="rgba(248,250,252,0.1)"/></svg>');
}

.hero-section > * {
    position: relative;
    z-index: 1;
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 800;
    margin-bottom: 1rem;
    text-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.hero-subtitle {
    font-size: 1.3rem;
    opacity: 0.9;
    font-weight: 300;
    max-width: 600px;
    margin: 0 auto 2rem auto;
    line-height: 1.6;
}

.hero-cta {
    background: linear-gradient(135deg, #16a34a 0%, #15803d 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 1rem 2.5rem !important;
    border-radius: 12px !important;
    border: none !important;
    font-size: 1.1rem !important;
    box-shadow: 0 4px 16px rgba(22, 163, 74, 0.3) !important;
    transition: all 0.3s ease !important;
}

.hero-cta:hover {
    background: linear-gradient(135deg, #15803d 0%, #166534 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(22, 163, 74, 0.4) !important;
}

/* Content Cards */
.content-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    margin: 1.5rem 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid #e2e8f0;
    transition: all 0.3s ease;
}

.content-card:hover {
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
    transform: translateY(-2px);
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.feature-card {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    border: 1px solid #e2e8f0;
    transition: all 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}

.feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.feature-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: #034694;
    margin-bottom: 1rem;
}

.feature-description {
    color: #64748b;
    line-height: 1.6;
}

/* Form Styling */
.stTextArea > label > div[data-testid="stMarkdownContainer"] > p,
.stTextInput > label > div[data-testid="stMarkdownContainer"] > p {
    color: #034694;
    font-weight: 600;
    font-size: 1.1rem;
}

.stTextArea textarea,
.stTextInput input {
    border-radius: 12px;
    border: 2px solid #e2e8f0;
    transition: border-color 0.3s ease;
    font-size: 1rem;
}

.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: #16a34a;
    box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.1);
}

/* Button Styling */
.stButton > button {
    background: linear-gradient(135deg, #16a34a 0%, #15803d 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
    border-radius: 12px !important;
    border: none !important;
    transition: all 0.3s ease !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #15803d 0%, #166534 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(22, 163, 74, 0.4) !important;
}

/* Status Pills */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
    margin: 0.25rem 0;
}

.status-success {
    background: linear-gradient(135deg, #d1fae5, #10b981);
    color: #065f46;
    border: 1px solid #059669;
}

.status-warning {
    background: linear-gradient(135deg, #fef3c7, #f59e0b);
    color: #92400e;
    border: 1px solid #d97706;
}

/* Loading Animation */
.loading-animation {
    display: inline-block;
    width: 24px;
    height: 24px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #16a34a;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .top-nav {
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
    }
    
    .nav-links {
        width: 100%;
        justify-content: center;
        flex-wrap: wrap;
    }
    
    .hero-title {
        font-size: 2.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.1rem;
    }
    
    .feature-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SHARED STATE
# ============================================================================

def initialize_state():
    """Initialize session state"""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"

initialize_state()

# ============================================================================
# TOP NAVIGATION
# ============================================================================

def render_navigation():
    """Render the top navigation bar"""
    nav_html = f"""
    <div class="top-nav-container">
        <div class="top-nav">
            <div class="nav-logo">
                ⚽ Chelsea FC Agent
            </div>
            <div class="nav-links">
                <!-- Navigation buttons will be rendered by Streamlit -->
            </div>
        </div>
    </div>
    """
    st.markdown(nav_html, unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        if st.button("🏠 Home", key="nav_home", 
                    help="Home page with audience analysis"):
            st.session_state.current_page = "home"
            st.rerun()
    
    with col2:
        if st.button("🎨 Customize", key="nav_customize",
                    help="Product customization"):
            st.session_state.current_page = "customize"
            st.rerun()
    
    with col3:
        if st.button("📊 Analytics", key="nav_analytics",
                    help="Performance insights"):
            st.session_state.current_page = "analytics"
            st.rerun()
    
    with col4:
        if st.button("ℹ️ About", key="nav_about",
                    help="About this application"):
            st.session_state.current_page = "about"
            st.rerun()
    
    with col5:
        # Status indicator
        if AGENT_AVAILABLE:
            st.markdown('<div class="status-pill status-success">✅ Agent Ready</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-pill status-warning">⚠️ Mock Mode</div>', 
                       unsafe_allow_html=True)

# ============================================================================
# PAGE CONTENT FUNCTIONS
# ============================================================================

def home_page():
    """Home page with hero section and main features"""
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">⚽ Chelsea FC Merchandise Agent</div>
        <div class="hero-subtitle">
            Transform your merchandise strategy with AI-powered audience analysis 
            and cultural intelligence. Get personalized recommendations that resonate 
            with your target fans.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Features Grid
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <div class="feature-title">Audience Analysis</div>
            <div class="feature-description">
                Deep demographic and psychographic analysis to understand your target fans
            </div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🎨</div>
            <div class="feature-title">Product Customization</div>
            <div class="feature-description">
                AI-powered customization based on cultural preferences and lifestyle patterns
            </div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Performance Insights</div>
            <div class="feature-description">
                Real-time analytics and recommendations to optimize your merchandise strategy
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Start
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 🚀 Quick Start")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_area(
            "Describe your target audience:",
            placeholder="e.g., Young Chelsea fans in London aged 25-35 who love technology and fashion",
            height=100,
            help="Be specific about demographics, interests, and preferences"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Analyze Audience", type="primary", use_container_width=True):
            if query.strip():
                st.success("Analysis started! Check results below.")
                # Add your agent logic here
            else:
                st.error("Please enter an audience description!")
    
    st.markdown('</div>', unsafe_allow_html=True)

def customize_page():
    """Product customization page"""
    st.markdown("# 🎨 Product Customization")
    st.markdown("Transform products based on cultural insights and audience preferences")
    
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        product_id = st.text_input(
            "Product ID to customize:",
            placeholder="e.g., prod_129, prod_244",
            help="Enter the ID of the product you want to customize"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🎨 Customize", type="primary", use_container_width=True):
            if product_id:
                st.success(f"Customizing product {product_id}...")
                # Add your customization logic here
            else:
                st.error("Please enter a product ID!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sample customization results
    if product_id:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🎨 Customization Preview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📦 Original Product**")
            st.image("https://via.placeholder.com/300x300/034694/FFFFFF?text=Original+Product")
        
        with col2:
            st.markdown("**✨ Customized Version**")
            st.image("https://via.placeholder.com/300x300/16a34a/FFFFFF?text=Customized+Product")
        
        st.markdown("### 🧠 Customization Reasoning")
        st.info("🤖 AI analysis shows this customization appeals to tech-savvy Chelsea fans by incorporating modern design elements while maintaining team heritage.")
        
        st.markdown('</div>', unsafe_allow_html=True)

def analytics_page():
    """Analytics dashboard"""
    st.markdown("# 📊 Analytics & Insights")
    st.markdown("Performance metrics and strategic insights for your merchandise campaigns")
    
    # Metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Analyses", "1,234", "12%")
    
    with col2:
        st.metric("Success Rate", "94.5%", "2.1%")
    
    with col3:
        st.metric("Avg Response Time", "2.3s", "-0.4s")
    
    with col4:
        st.metric("User Satisfaction", "4.8/5", "0.2")
    
    # Charts and insights
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 📈 Performance Trends")
    st.line_chart({
        "Analyses": [10, 25, 40, 55, 70, 85, 100],
        "Success Rate": [85, 87, 90, 92, 93, 94, 95]
    })
    st.markdown('</div>', unsafe_allow_html=True)

def about_page():
    """About page"""
    st.markdown("# ℹ️ About")
    st.markdown("Learn more about the Chelsea FC Merchandise Agent")
    
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 Mission")
    st.write("""
    Our mission is to revolutionize merchandise strategy through AI-powered 
    cultural intelligence, helping Chelsea FC connect with fans on a deeper level.
    """)
    
    st.markdown("### 🤖 Technology")
    st.write("""
    Built with cutting-edge AI including Gemini 2.0 Flash, Google ADK, 
    and Qloo's cultural intelligence platform.
    """)
    
    st.markdown("### 📞 Session Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption(f"**User ID:** `{st.session_state.user_id}`")
    
    with col2:
        st.caption(f"**Session ID:** `{st.session_state.session_id}`")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# MAIN APP LOGIC
# ============================================================================

def main():
    """Main application logic"""
    # Render navigation
    render_navigation()
    
    # Render current page
    if st.session_state.current_page == "home":
        home_page()
    elif st.session_state.current_page == "customize":
        customize_page()
    elif st.session_state.current_page == "analytics":
        analytics_page()
    elif st.session_state.current_page == "about":
        about_page()

if __name__ == "__main__":
    main()