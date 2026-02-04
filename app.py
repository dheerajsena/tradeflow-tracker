import streamlit as st
import db_manager as db
import pandas as pd
import plotly.express as px
from datetime import date
import time

# Page Config
st.set_page_config(page_title="TradeFlow Tracker", page_icon="📈", layout="centered", initial_sidebar_state="collapsed")

# Initialize DB
db.init_db()

# Custom CSS for Enterprise Look
st.markdown("""
    <style>
    /* Global Font */
    html, body, [class*="css"]  {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background-color: #f0f2f6; 
    }
    
    /* Input Fields */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1px solid #dfe1e5;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        height: 2.8em; 
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    
    /* Cards */
    .trade-card {
        background-color: white;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 12px;
        border-left: 5px solid #007bff; /* Default Blue */
        transition: transform 0.2s;
    }
    .trade-card:hover {
        transform: scale(1.01);
    }
    .trade-card.loss {
        border-left-color: #ff4b4b; /* Red */
    }
    .trade-card.profit {
        border-left-color: #00cc96; /* Green */
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1f2937;
    }
    </style>
""", unsafe_allow_html=True)

# Session State for Auth
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

# --- AUTHENTICATION ---
def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("TradeFlow 📈")
        st.markdown("##### Professional Trading Journal")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.write("") # Spacer
            username = st.text_input("Username", key="login_user", placeholder="johndoe")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Access Dashboard", type="primary"):
                with st.spinner("Authenticating..."):
                    time.sleep(0.5) # Fake delay for effect
                    uid, uname = db.authenticate_user(username, password)
                    if uid:
                        st.session_state.user_id = uid
                        st.session_state.username = uname
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                
        with tab2:
            st.write("")
            new_user = st.text_input("Choose Username", key="reg_user")
            new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
            if st.button("Create Account"):
                if new_user and new_pass:
                    if db.create_user(new_user, new_pass):
                        st.success("Account created successfully! Please log in.")
                    else:
                        st.error("Username already taken.")
                else:
                    st.warning("Please fill all fields.")

# --- MAIN APP ---
def main_app():
    # Sidebar
    with st.sidebar:
        st.title("TradeFlow")
        st.write(f"Logged in as **{st.session_state.username}**")
        st.markdown("---")
        if st.button("Log Out"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
    
    st.title("Dashboard")
    
    # FETCH DATA
    df = db.get_user_trades(st.session_state.user_id)
    
    # 1. NEW ENTRY SECTION
    with st.expander("➕ Log New Trade", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            trade_date = st.date_input("Date", date.today())
            
            # Dynamic Event Dropdown Logic
            user_events = db.get_unique_events(st.session_state.user_id)
            default_events = ["ASX", "NASDAQ", "CRYPTO", "FOREX"] 
            # Merge and Dedup, keeping user preferences
            all_events = sorted(list(set(default_events + user_events)))
            
            # Default to last used if available, otherwise first item
            # We don't have explicit 'last used' storage but we can infer from last trade
            index = 0
            if not df.empty:
                last_event = df.iloc[0]['event']
                if last_event in all_events:
                    index = all_events.index(last_event)
            
            event_choice = st.selectbox(
                "Event / Market", 
                all_events + ["Add New..."],
                index=index
            )
            
            final_event = event_choice
            if event_choice == "Add New...":
                final_event = st.text_input("Enter new Event Name (e.g. NYSE)").upper()
        
        with col2:
            spent = st.number_input("Amount Spent ($)", min_value=0.0, step=50.0)
            earned = st.number_input("Amount Earned ($)", min_value=0.0, step=50.0)
        
        if st.button("Add Trade Entry", type="primary"):
            if final_event and final_event != "Add New...":
                db.add_trade(st.session_state.user_id, trade_date, final_event, spent, earned)
                st.toast(f"Trade for {final_event} saved!", icon="✅")
                time.sleep(1) # Let toast show
                st.rerun() 
            else:
                st.warning("Please define a valid Event name.")

    # 2. ANALYTICS
    st.markdown("### Performance Overview")
    if not df.empty:
        total_spent = df['spent'].sum()
        total_earned = df['earned'].sum()
        total_pnl = df['pnl'].sum()
        roi = (total_pnl / total_spent * 100) if total_spent > 0 else 0
        
        # Determine Color for KPIs
        roi_color = "normal" 
        if roi > 0: roi_color = "off" # Streamlit metric delta colors handled automatically
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Net P&L", f"${total_pnl:,.2f}", delta=f"{roi:.1f}% ROI")
        m2.metric("Total Invested", f"${total_spent:,.2f}")
        m3.metric("Total Return", f"${total_earned:,.2f}")
        m4.metric("Total Trades", len(df))
        
        # Charts
        tab_chart1, tab_chart2 = st.tabs(["📈 Cumulative Growth", "🥧 Market Exposure"])
        
        with tab_chart1:
            # Pnl over time
            df['date_dt'] = pd.to_datetime(df['date'])
            daily_agg = df.groupby('date_dt')['pnl'].sum().reset_index().sort_values('date_dt')
            daily_agg['cumulative_pnl'] = daily_agg['pnl'].cumsum()
            
            fig_line = px.line(
                daily_agg, x='date_dt', y='cumulative_pnl', 
                labels={'cumulative_pnl': 'Net P&L ($)', 'date_dt': 'Date'},
                markers=True
            )
            fig_line.update_traces(line_color='#007bff', line_width=3, fill='tozeroy')
            fig_line.update_layout(xaxis_title="", yaxis_title="", template="plotly_white", height=300)
            st.plotly_chart(fig_line, use_container_width=True)
            
        with tab_chart2:
            # PnL by Event
            # Aggregate spent by event
            event_agg = df.groupby('event')[['spent', 'earned']].sum().reset_index()
            fig_pie = px.pie(event_agg, values='spent', names='event', donut=0.4) 
            fig_pie.update_layout(template="plotly_white", height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    else:
        st.info("No trades data available. Log your first trade above to see analytics.")

    # 3. HISTORY CARDS
    st.markdown("### Recent Activity")
    
    if df.empty:
         st.write("Nothing to show.")
    else:
        for index, row in df.iterrows():
            # Clean PnL styling
            pnl_val = row['pnl']
            color_class = "loss" if pnl_val < 0 else "profit" # CSS Classes
            pnl_str = f"${pnl_val:,.2f}"
            if pnl_val > 0: pnl_str = f"+{pnl_str}"
            
            # HTML Card Structure
            card_html = f"""
            <div class="trade-card {color_class}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="flex-grow:1;">
                        <span style="background-color:#eee; padding:2px 8px; border-radius:4px; font-size:0.8em; font-weight:bold; color:#555;">{row['event']}</span>
                        <div style="margin-top:4px; font-size:0.9em; color:#666;">📅 {row['date']}</div>
                    </div>
                    
                    <div style="text-align:right; margin-right: 15px;">
                        <div style="font-size:1.1em; font-weight:bold; color: {'#00cc96' if pnl_val >= 0 else '#ff4b4b'};">
                            {pnl_str}
                        </div>
                        <div style="font-size:0.8em; color:#888;">
                            Roi: {((row['earned']-row['spent'])/row['spent']*100) if row['spent']>0 else 0:.1f}%
                        </div>
                    </div>
                </div>
            </div>
            """
            
            # Container to hold card + delete button
            c1, c2 = st.columns([0.9, 0.1])
            with c1:
                st.markdown(card_html, unsafe_allow_html=True)
            with c2:
                # Vertical alignment spacer
                st.write("")
                st.write("")
                if st.button("✕", key=f"del_{row['id']}", help="Delete Entry"):
                    db.delete_trade(row['id'], st.session_state.user_id)
                    st.rerun()

# --- DISPATCHER ---
if st.session_state.user_id:
    main_app()
else:
    login_page()
