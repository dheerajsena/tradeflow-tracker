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
        st.title("TradeFlow Pro 🏢")
        st.write(f"Identity: **{st.session_state.username}**")
        st.markdown("---")
        
        # Navigation
        page = st.radio("Enterprise Navigation", ["Active Dashboard", "Advanced Analytics", "Trade History"])
        
        st.markdown("---")
        if st.button("Logout System"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
    
    # FETCH DATA
    df = db.get_user_trades(st.session_state.user_id)
    if not df.empty:
        df['date_dt'] = pd.to_datetime(df['date'])
        df['month_period'] = df['date_dt'].dt.to_period('M')
        df['month_year'] = df['date_dt'].dt.strftime('%b %Y')

    if page == "Active Dashboard":
        st.title("Trading Floor")
        
        # 1. NEW ENTRY SECTION
        with st.expander("🆕 Register New Transaction", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                trade_date = st.date_input("Execution Date", date.today())
                
                # Dynamic Event Dropdown Logic - CLEAN (NO DEFAULTS)
                user_events = db.get_unique_events(st.session_state.user_id)
                all_options = sorted(user_events) + ["<Add New Entry Type>"]
                
                # Default selection logic
                index = (len(all_options)-1) # Default to Add New
                if not df.empty:
                    last_event = df.iloc[0]['event']
                    if last_event in all_options:
                        index = all_options.index(last_event)
                
                event_choice = st.selectbox("Symbol / Market Group", all_options, index=index)
                
                final_event = event_choice
                if event_choice == "<Add New Entry Type>":
                    final_event = st.text_input("Enter Label (e.g. BTC, ASX, NYSE)").upper()
            
            with col2:
                spent = st.number_input("Capital Deployed ($)", min_value=0.0, step=100.0)
                earned = st.number_input("Gross Return ($)", min_value=0.0, step=100.0)
            
            if st.button("Commit to Ledger", type="primary", use_container_width=True):
                if final_event and final_event != "<Add New Entry Type>":
                    db.add_trade(st.session_state.user_id, trade_date, final_event, spent, earned)
                    st.toast(f"Ledger Updated: {final_event}", icon="🚀")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Please define the market type.")

        # Quick Health Check
        if not df.empty:
            st.markdown("### Portfolio Pulse")
            tot_s = df['spent'].sum()
            tot_p = df['pnl'].sum()
            tot_roi = (tot_p / tot_s * 100) if tot_s > 0 else 0
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Lifetime Investment", f"${tot_s:,.2f}")
            m2.metric("Net Yield", f"${tot_p:,.2f}", delta=f"{tot_roi:.1f}%")
            m3.metric("Entry Count", f"{len(df)}")

    elif page == "Advanced Analytics":
        st.title("Enterprise Reporting Engine")
        
        if df.empty:
            st.warning("No data found. Please log trades to view analytics.")
        else:
            # 1. MARKET SELECTOR
            all_markets = sorted(df['event'].unique().tolist())
            market_filter = st.selectbox("Market Segmentation View", ["🌍 Global Portfolio"] + all_markets)
            
            report_df = df if market_filter == "🌍 Global Portfolio" else df[df['event'] == market_filter]
            
            # 2. SECTOR SPECIFIC STATS
            st.markdown(f"#### Performance Parameters: {market_filter}")
            s1, s2, s3, s4 = st.columns(4)
            r_s = report_df['spent'].sum()
            r_e = report_df['earned'].sum()
            r_p = report_df['pnl'].sum()
            r_roi = (r_p / r_s * 100) if r_s > 0 else 0
            
            s1.metric("Total Deployment", f"${r_s:,.2f}")
            s2.metric("Gross Revenue", f"${r_e:,.2f}")
            s3.metric("Net Profit/Loss", f"${r_p:,.2f}", delta=f"{r_roi:.2f}%")
            s4.metric("Avg Trade Size", f"${report_df['spent'].mean():,.2f}")

            st.markdown("---")

            # 3. MONTHLY SEGMENTATION (P&L Reporting)
            st.markdown("### 📊 Monthly Enterprise Reports")
            
            # Aggregate Monthly Stats
            monthly_agg = report_df.groupby('month_period').agg({
                'spent': 'sum',
                'earned': 'sum',
                'pnl': 'sum'
            }).reset_index().sort_values('month_period')
            
            monthly_agg['month_label'] = monthly_agg['month_period'].dt.strftime('%b %Y')
            monthly_agg['cumulative_pnl'] = monthly_agg['pnl'].cumsum()
            
            # Monthly Visualization
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("**Individual Monthly P&L**")
                fig_m_bar = px.bar(
                    monthly_agg, x='month_label', y='pnl',
                    color='pnl', color_continuous_scale=['#ff4b4b', '#00cc96'],
                    labels={'pnl': 'Net P&L ($)', 'month_label': 'Reporting Period'}
                )
                fig_m_bar.update_layout(template="plotly_white", showlegend=False, height=350)
                st.plotly_chart(fig_m_bar, use_container_width=True)

            with col_right:
                st.markdown("**Cumulative Monthly Growth**")
                fig_c_line = px.line(
                    monthly_agg, x='month_label', y='cumulative_pnl',
                    markers=True, labels={'cumulative_pnl': 'Cumul. P&L ($)'}
                )
                fig_c_line.update_traces(line_color='#007bff', line_width=4, fill='tozeroy')
                fig_c_line.update_layout(template="plotly_white", height=350)
                st.plotly_chart(fig_c_line, use_container_width=True)

            # 4. DATA TABLE
            with st.expander("📄 Export Monthly Ledger Data"):
                table_out = monthly_agg[['month_label', 'spent', 'earned', 'pnl', 'cumulative_pnl']].copy()
                table_out.columns = ['Period', 'Total Spent', 'Total Earned', 'Monthly P&L', 'Cumulative Growth']
                st.dataframe(table_out, hide_index=True, use_container_width=True)

    elif page == "Trade History":
        st.title("Transaction History")
        if df.empty:
            st.info("No records to display.")
        else:
            search_query = st.text_input("Search Assets...", placeholder="e.g. BTC")
            display_df = df[df['event'].str.contains(search_query, case=False)] if search_query else df
            
            for _, row in display_df.iterrows():
                sts = "profit" if row['pnl'] >= 0 else "loss"
                p_col = "#00cc96" if row['pnl'] >= 0 else "#ff4b4b"
                
                card_html = f"""
                <div class="trade-card {sts}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:bold; color:#333;">{row['event']}</span>
                            <div style="font-size:0.8em; color:#888;">{row['date']}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1.1em; font-weight:bold; color:{p_col};">
                                {'+' if row['pnl'] > 0 else ''}${row['pnl']:,.2f}
                            </div>
                            <div style="font-size:0.75em; color:#999;">S: ${row['spent']:,.2f} | E: ${row['earned']:,.2f}</div>
                        </div>
                    </div>
                </div>
                """
                
                c_data, c_del = st.columns([0.9, 0.1])
                with c_data:
                    st.markdown(card_html, unsafe_allow_html=True)
                with c_del:
                    st.write("")
                    if st.button("✕", key=f"del_{row['id']}"):
                        db.delete_trade(row['id'], st.session_state.user_id)
                        st.rerun()

# --- DISPATCHER ---
if st.session_state.user_id:
    main_app()
else:
    login_page()

