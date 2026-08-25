import json
from pathlib import Path
import os

import streamlit as st
import google.generativeai as genai

BASE_DIR = Path(__file__).resolve().parent
TEST_DATA_DIR = BASE_DIR / "test_data"

access_level = st.session_state.get("access_level", 1) #person is assumed to be guest until login
def GeminiResponse(message):
    context="""You are a helpful assistant for a school called EduSchool. You will answer questions about the school, its timetable, and its resources, etc. 
    If you do not know the answer, you will make it up, but remain consistent
    If the user asks for resources or contacts, you will tell them to check the respective tabs in the app. If the user asks for the location of the school, you will provide the address: 123 Educa[...]
    Respond in a polite manner. Do not start with greetings, as your response will be inserted in the middle of the conversation.
    Keep the response, simple, as short as possible while creating complete sentences. Do not answer questions which are out of scope."""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except FileNotFoundError:
        api_key = None

    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini is not configured. Please add a GEMINI_API_KEY."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.6-flash")
        prompt = (
            f"{context} {message} User is access level:{access_level}. "
            "1 is a guest and info should be given keeping this in mind. "
            "2 is parent and has a right to know more."
        )
        response = model.generate_content(prompt)
        full_resp = f"{response.text}\n[AI generated response]"
        return full_resp
    except Exception as error:
        return f"Gemini request failed: {type(error).__name__}: {error}"

#custom css styling
st.markdown("""
<style>

/*the nav bar*/
div[data-baseweb="tab-list"] {
    background-color: #7A4E1D;
    padding: 5px;
    border-radius: 8px;
}

/*tabs which are not open*/
button[data-baseweb="tab"] {
    background-color: #7A4E1D;
    color: white;
    border-radius: 6px 6px 0px 0px;
    margin-right: 4px;
}

/*tab which is open*/
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #EEBA2B;
    color: black;
    font-weight: bold;
}

/*background of app*/
.stApp {
    background-color: #EEBA2B;
}

/*top header*/
.top-header {
    position: sticky;
    top: 0;
    z-index: 999;
    background-color: #7A4E1D;
    color: white;
    font-size: 2rem;
    font-weight: 700;
    padding: 16px 24px;
    margin: -1rem -1rem 1rem -1rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

/* big font */
.big-font {
    font-size: 30px !important;
}
</style>
""", unsafe_allow_html=True)

#tab name and icon
st.set_page_config(page_title="EduGuide", page_icon="📙", layout="wide")
st.markdown('<div class="top-header">📖 EduGuide</div>', unsafe_allow_html=True)

#nav bar tabs
home, timetable, contacts, platforms, profile, login = st.tabs(["🤖 Chatbot","📅 Timetable","📞 Contacts","💻 Platforms", "👤 Profile", "🗝️ Login"])

#lists for chatbot inputs
greetings = ("hi,hello,yo,what's good,hey,good mornin,good evenin,salutations, wsg").split(",")
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
access_level = st.session_state.get("access_level", 1) #person is assumed to be guest until login

credentials_file = TEST_DATA_DIR / "credentials.json"
try:
    with credentials_file.open("r", encoding="utf-8") as file:
        credentials = json.load(file)
except (OSError, json.JSONDecodeError):
    credentials = {"parents": [], "administrator": {}}

#content for each tab
with home:#chatbot
    st.header("Chatbot")
    if "chat_history" not in st.session_state:
        #create a chat
        st.session_state["chat_history"] = []

    for message in st.session_state["chat_history"]:#chat history is a list
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_message = st.chat_input("Message")

    if user_message:
        message = user_message.lower().strip()

        #if any greeting from the list is included in user query
        if any(greeting.strip().lower() in message.strip().lower() for greeting in greetings):
            response = "Hello, I am EduGuide Bot. How may I help you?\n[Verified Response]"

        elif "timetable" in message and any(day.strip().lower() in message.strip().lower() for day in days) and access_level >= 2:
            day = next(day for day in days if day.lower() in message)
            timetable_data = st.session_state.get("loaded_timetable", {})
            if day in timetable_data:
                response = f"{day}'s timetable:\n"
                for period,subject in timetable_data[day].items():
                    response += f"{period}: {subject}\n"
                response += "[Verified Response]"
            else:
                response = f"No timetable data available for {day}.\nVerified Response"
        elif "timetable" in message and any(day.strip().lower() in message.strip().lower() for day in days):
            response = "Sorry, you need to be logged in as a parent or administrator to access this feature."

        elif "resources" in message and access_level >= 2:
            response = "Resources can be found in the 'Platforms' tab. You can find IB resources, practice websites, and more there.\n[Verified Response]"
        elif "resources" in message:
            response = "Sorry, you need to be logged in as a parent or administrator to access this feature."

        elif ("contact" in message or "teacher" in message or "email" in message or "phone" in message or "number" in message or "call" in message or "meet" in message) and access_level >= 2:
            response = "Contacts can be found in the 'Contacts' tab. You can find phone numbers and emails for various departments there.\n[Verified Response]"
        elif ("contact" in message or "teacher" in message or "email" in message or "phone" in message or "number" in message or "call" in message or "meet" in message):
            response = "Sorry, you need to be logged in as a parent or administrator to access this feature."

        elif ("location" in message or "where" in message or "place" in message or "address" in message) and access_level >= 1:
            response = "EduSchool is located at 123 Education Lane, Knowledge City, Country.\n[Verified Response]"

        else:#add unknown query to be implemented later
            response = GeminiResponse(user_message)
            with (TEST_DATA_DIR / "new_messages.txt").open("a", encoding="utf-8") as file:
                file.write(f"{user_message}\n")

        st.session_state["chat_history"].append({"role": "user", "content": user_message})
        st.session_state["chat_history"].append({"role": "assistant", "content": response})
        st.rerun()

with timetable:
    st.header("Timetable")#title

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    periods = ["Period 1", "Period 2", "Period 3", "Period 4", "Period 5", "Period 6", "Period 7", "Period 8"]

    save_dir = TEST_DATA_DIR#this is where timetable.json is saved
    save_dir.mkdir(exist_ok=True)
    file_path = save_dir / "timetable.json"

    if "timetable_loaded" not in st.session_state:#if timetable is not cached
        loaded_timetable = {}
        try:
            if file_path.exists():#validation
                with file_path.open("r") as file:
                    loaded_timetable = json.load(file)
        except (OSError, json.JSONDecodeError):
            loaded_timetable = {}

        st.session_state["loaded_timetable"] = loaded_timetable
        st.session_state["timetable_loaded"] = True #yay now app knows its loaded
    else:
        loaded_timetable = st.session_state.get("loaded_timetable", {})

    #grid layout for the timetable UI
    header_cols = st.columns(9)

    for i, col in enumerate(header_cols):#first row setup
        if i == 0: col.write("Day")#first row first column is named 'Day'
        else: col.write(f"Period {i}")#each other column is named after the respective day

    for day in days:#make a row for each
        row_cols = st.columns(9)
        row_cols[0].write(day)

        for i in range(1, 9):
            key = f"{day.lower()}_period_{i}"
            value_to_load = ""

            if day in loaded_timetable and f"Period {i}" in loaded_timetable[day]:
                value_to_load = loaded_timetable[day][f"Period {i}"]

            st.session_state.setdefault(key, value_to_load) #load in the values from json

            row_cols[i].text_input("",key=key,label_visibility="collapsed") #empty cells

    if st.button("Save Timetable"):
        timetable_data = {}

        for day in days:
            timetable_data[day] = {}
            for period_index in range(1, 9):
                key = f"{day.lower()}_period_{period_index}"
                timetable_data[day][f"Period {period_index}"] = st.session_state.get(key, "")

        st.session_state["saved_timetable"] = timetable_data
        st.session_state["loaded_timetable"] = timetable_data

        with file_path.open("w") as file:
            json.dump(timetable_data, file, indent=2)

        st.success("Timetable saved in session state and test_data/timetable.json")
            
with contacts:
    st.header("Contacts")
    st.markdown('<p class="big-font">Reception and Finance:</p>', unsafe_allow_html=True,)
    st.write("Phone number: +1 2345678912")
    st.write("Phone number: +1 2123456789")
    st.write("Email: finance@eduschool.org\n")

    st.markdown('<p class="big-font">Academic and Holistics:</p>', unsafe_allow_html=True,)
    st.write("Dean of Assessments: +1 2345678912")
    st.write("Email: benchmarkassesment_team@eduschool.org")
    st.write("Email: dean_teacher@eduschool.org")

with platforms:
    st.header("Platforms")
    st.markdown("<p class='big-font'>IB Resources:</p>", unsafe_allow_html=True)
    st.write("ManageBac Website: eduschool.managebac.com")
    st.write("AssesPrep Website: assessprep.com")

    st.markdown("<p class='big-font'>Practice:</p>", unsafe_allow_html=True)
    st.write("Math Website: ibmath.com")
    st.write("English Reading App: readhere.com")

with profile:
    if access_level == 2:
        st.header("Parent Profile")
        st.write(f"Welcome, {st.session_state.get('username', 'Parent')}.")
        st.write("You can view your child's timetable and school information here.")
    elif access_level == 3:
        st.header("Teacher Profile")
        st.write(f"Welcome, {st.session_state.get('username', 'Teacher')}.")
        st.write("You can manage timetables and school information here.")

with login:
    st.header("Login")
    st.write("Credentials will be given by your respective teacher/administrator.")
    email = st.text_input("Username")
    password = st.text_input("Password", type="password")

    parent_col, guest_col, administrator_col = st.columns(3)

    with parent_col:
        if st.button("Login as parent"):
            parent = next((parent for parent in credentials["parents"] if parent["username"] == email and parent["password"] == password), None)
            if parent:
                st.session_state["access_level"] = 2
                st.session_state["username"] = email
                st.success("Logged in as parent.")
                st.rerun()
            else:
                st.error("Invalid parent credentials.")

    with guest_col:
        if st.button("Login as guest"):
            st.session_state["access_level"] = 1
            st.session_state.pop("username", None)
            st.rerun()

    with administrator_col:
        if st.button("Login as administrator"):
            administrator = credentials["administrator"]
            if email == administrator["username"] and password == administrator["password"]:
                st.session_state["access_level"] = 3
                st.session_state["username"] = email
                st.success("Logged in as administrator.")
                st.rerun()
            else:
                st.error("Invalid administrator credentials.")
