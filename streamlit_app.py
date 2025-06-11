# ZenithPlanner/streamlit_app.py

import streamlit as st
from streamlit_oauth import OAuth2Component
from datetime import datetime
from dateutil import parser
import base64
import json
import pytz
import time

# Import your application's modules
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, REDIRECT_URI
from task_manager import TaskManager
from db.models import TaskDatabase

# --- 1. AUTHENTICATION AND CONFIGURATION ---

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"

# Create an OAuth2Component instance
oauth2 = OAuth2Component(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    authorize_endpoint=AUTHORIZE_URL,
    token_endpoint=TOKEN_URL,
)

# --- 2. HELPER FUNCTIONS (No changes here) ---

def render_dynamic_time_header():
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    formatted_date = now_ist.strftime("%A, %B %d, %Y")
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #4CAF50, #45a049); padding: 15px 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="color: white; margin: 0; font-size: 1.5rem; font-weight: 600;">📅 {formatted_date}</h2>
    </div>
    """, unsafe_allow_html=True)

def decode_id_token(token_dict):
    try:
        id_token = token_dict['id_token']
        payload_b64 = id_token.split('.')[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload_json = base64.b64decode(payload_b64).decode('utf-8')
        return json.loads(payload_json)
    except Exception as e:
        st.error(f"Error decoding user token: {e}")
        return None

def format_time_left(delta):
    if delta.total_seconds() < 0:
        return "Overdue by " + str(abs(delta)).split('.')[0]
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    if days > 1: return f"{days} days left"
    if days == 1: return "1 day left"
    parts = []
    if hours > 0: parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0: parts.append(f"{minutes} min{'s' if minutes > 1 else ''}")
    if not parts: return "Due now"
    return " ".join(parts) + " left"

# --- 3. MAIN APPLICATION UI (No changes here) ---

def main_app(user):
    st.set_page_config(page_title="ZenithPlanner", page_icon="🧠", layout="wide")
    
    if 'task_manager' not in st.session_state:
        db_instance = TaskDatabase()
        st.session_state.task_manager = TaskManager(db_instance)
        
    manager = st.session_state.task_manager
    db_user_id = st.session_state.db_user['id']

    render_dynamic_time_header()
    
    with st.sidebar:
        st.title(f"Welcome, {user.get('given_name', 'User')}!")
        st.info(f"Logged in as:\n_{user.get('email')}_")
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        st.divider()
        st.page_link("https://github.com/neon200/ZenithPlanner", label="View on GitHub", icon="⭐")

    st.title("🧠 ZenithPlanner Dashboard")
    st.markdown("Your intelligent assistant to achieve peak productivity. Just type what you need to do!")

    with st.form("new_task_form", clear_on_submit=True):
        user_input = st.text_input("Describe your task:", placeholder="e.g., 'Submit project proposal by Friday at 5 PM'")
        submitted = st.form_submit_button("Add Task", use_container_width=True, type="primary")
        if submitted and user_input:
            with st.spinner("🤖 Analyzing and adding your task..."):
                result = manager.add_task_from_natural_language(user_input, db_user_id)
                st.toast(result, icon="✅" if "✅" in result else "❌")

    st.divider()
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📋 Your Prioritized Tasks")
        tasks = manager.list_prioritized_tasks(db_user_id)
        if not tasks:
            st.info("No pending tasks. Add one above to get started!", icon="🎉")
        else:
            for task in tasks:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([0.08, 0.84, 0.08])
                    with c1:
                        if st.button("✔️", key=f"done_{task['id']}", help="Mark as complete"):
                            manager.mark_task_complete(task['id'], db_user_id)
                            st.toast(f"Great job finishing '{task['title']}'!")
                            st.rerun()
                    with c2:
                        st.markdown(f"**{task['title']}**")
                        meta_info = [f"`{task['category']}`"]
                        if task.get('due_time'):
                            due_date_str = task['due_time'].astimezone(pytz.timezone('Asia/Kolkata')).strftime('%a, %b %d, %I:%M %p')
                            meta_info.append(f"🗓️ *Due: {due_date_str}*")
                            if 'time_left' in task:
                                time_left_str = format_time_left(task['time_left'])
                                color = "green" if "left" in time_left_str else "orange" if "Due" in time_left_str else "red"
                                meta_info.append(f"<span style='color:{color}'>**⏳ {time_left_str}**</span>")
                        st.markdown(" | ".join(meta_info), unsafe_allow_html=True)
                        if task.get('user_notes'):
                            st.caption(f"📝 {task['user_notes']}")
                    with c3:
                        if st.button("🗑️", key=f"delete_{task['id']}", help="Delete task"):
                            manager.delete_task(task['id'], db_user_id)
                            st.toast(f"Deleted '{task['title']}'")
                            st.rerun()

    with col2:
        st.header("⏳ Dashboards")
        with st.container(border=True):
            st.subheader("Countdown Events")
            countdown_events = manager.get_countdown_events(db_user_id)
            if not countdown_events:
                st.write("No upcoming events.")
            else:
                for event in countdown_events:
                    with st.container():
                        c1, c2 = st.columns([0.85, 0.15])
                        with c1:
                            st.metric(
                                label=f"{event['title']} ({event['category']})",
                                value=format_time_left(event['time_left']),
                                delta=f"Due: {event['due_time'].astimezone(pytz.timezone('Asia/Kolkata')).strftime('%b %d, %I:%M %p')}",
                                delta_color="off"
                            )
                        with c2:
                            if st.button("🗑️", key=f"delete_event_{event['id']}", help="Delete event"):
                                manager.delete_task(event['id'], db_user_id)
                                st.toast(f"Deleted '{event['title']}'")
                                st.rerun()

    st.divider()
    st.header("📊 End-of-Day Digest")
    col_summary1, col_summary2 = st.columns([1, 4])
    with col_summary1:
        if st.button("Generate Daily Summary", use_container_width=True, type="primary"):
            st.session_state.show_summary = True
    with col_summary2:
        if st.button("Clear Summary", use_container_width=True):
            st.session_state.show_summary = False
    if st.session_state.get('show_summary', False):
        with st.spinner("🤖 Generating your comprehensive daily summary..."):
            summary_data = manager.get_daily_summary(db_user_id)
            with st.container(border=True):
                st.markdown("### 📈 Your Daily Productivity Report")
                for section in summary_data:
                    if section['type'] == 'header': st.markdown(f"## {section['content']}")
                    elif section['type'] == 'subheader': st.markdown(f"### {section['content']}")
                    elif section['type'] == 'metric':
                        c1, c2, c3 = st.columns(3)
                        with c1: st.metric("Completed Today", section['completed'])
                        with c2: st.metric("Pending Tasks", section['pending'])
                        with c3: st.metric("Completion Rate", f"{section['completion_rate']}%")
                    elif section['type'] == 'completed_list':
                        if section['tasks']:
                            st.markdown("**✅ Tasks Completed Today:**")
                            for task in section['tasks']: st.markdown(f"• **{task['title']}** ({task['category']})")
                        else: st.info("No tasks completed today yet. Keep going!")
                    elif section['type'] == 'pending_list':
                        if section['tasks']:
                            st.markdown("**📋 Tasks Still Pending:**")
                            for task in section['tasks']:
                                due_info = ""
                                if task.get('due_time'): due_info = f" - Due: {task['due_time'].astimezone(pytz.timezone('Asia/Kolkata')).strftime('%b %d, %I:%M %p')}"
                                st.markdown(f"• **{task['title']}** ({task['category']}){due_info}")
                        else: st.success("🎉 All tasks completed! You're on fire!")
                    elif section['type'] == 'motivation':
                        st.markdown("---"); st.markdown(f"### 🎯 {section['content']}")

# --- 4. LOGIN AND ROUTING LOGIC (No changes here) ---

def show_login_page():
    st.set_page_config(page_title="ZenithPlanner Login", layout="centered")
    st.markdown("""<style>div[data-testid="stVerticalBlock"] div[data-testid="stButton"] button {width: 100%; height: 50px; font-size: 20px;}</style>""", unsafe_allow_html=True)
    st.title("Welcome to ZenithPlanner 🧠")
    st.write("Your intelligent assistant to achieve peak productivity.")
    st.write("")
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        return oauth2.authorize_button(name="Login with Google", icon="https://www.google.com/favicon.ico", redirect_uri=REDIRECT_URI, scope=SCOPE, use_container_width=True)

def main():
    if not st.session_state.get('token'):
        token = show_login_page()
        if token:
            st.session_state.token = token
            st.rerun()
    else:
        if not st.session_state.get('user'):
            user_info_from_token = decode_id_token(st.session_state.token['token'])
            if user_info_from_token:
                st.session_state.user = user_info_from_token
                db_instance = TaskDatabase()
                db_user = db_instance.get_or_create_user(email=st.session_state.user['email'], name=st.session_state.user.get('name'))
                st.session_state.db_user = dict(db_user)
                st.rerun()
            else:
                st.error("Could not validate your session. Please log in again.")
                time.sleep(2)
                st.session_state.clear()
                st.rerun()
        if st.session_state.get('db_user'):
            main_app(st.session_state.user)

if __name__ == '__main__':
    main()