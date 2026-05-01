import streamlit as st
import sqlite3
import pandas as pd

# =========================
# DATABASE CONNECTION
# =========================
def connect_db():
    conn = sqlite3.connect("TA.db3", check_same_thread=False)
    return conn

conn = connect_db()
cursor = conn.cursor()

# =========================
# LOGIN TABLE CREATE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS login (
    login_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")
conn.commit()

# =========================
# AUTH FUNCTIONS
# =========================
def register_user(username, password):
    try:
        cursor.execute("INSERT INTO login (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    cursor.execute("SELECT * FROM login WHERE username=? AND password=?", (username, password))
    return cursor.fetchone()

# =========================
# GENERIC DB FUNCTIONS
# =========================
def fetch_tables():
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    return tables['name'].tolist()

def fetch_data(table):
    return pd.read_sql(f"SELECT * FROM {table}", conn)

def insert_data(table, data):
    cols = ','.join(data.keys())
    placeholders = ','.join(['?'] * len(data))
    query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    cursor.execute(query, list(data.values()))
    conn.commit()

def update_data(table, data, pk, pk_val):
    set_clause = ','.join([f"{k}=?" for k in data.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {pk}=?"
    cursor.execute(query, list(data.values()) + [pk_val])
    conn.commit()

def delete_data(table, pk, pk_val):
    cursor.execute(f"DELETE FROM {table} WHERE {pk}=?", (pk_val,))
    conn.commit()

# =========================
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =========================
# LOGIN PAGE
# =========================
def login_page():
    st.title("🌍 Travel Agency System")

    option = st.radio("Select Option", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Register":
        if st.button("Register"):
            if register_user(username, password):
                st.success("User Registered Successfully")
            else:
                st.error("Username already exists")

    if option == "Login":
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid Credentials")

# =========================
# DASHBOARD
# =========================
def dashboard():
    st.title("📊 Dashboard")

    try:
        customers = fetch_data("Customer")
        bookings = fetch_data("Booking")
        packages = fetch_data("Package")

        col1, col2, col3 = st.columns(3)
        col1.metric("Customers", len(customers))
        col2.metric("Bookings", len(bookings))
        col3.metric("Packages", len(packages))

        st.subheader("Recent Data")
        st.dataframe(bookings.head())

    except:
        st.warning("Some tables not found in DB")

# =========================
# CRUD UI GENERATOR
# =========================
def crud_page(table):
    st.title(f"📂 {table} Management")

    df = fetch_data(table)
    st.dataframe(df)

    if len(df.columns) == 0:
        st.warning("No columns found")
        return

    columns = df.columns.tolist()
    pk = columns[0]

    st.subheader("Add / Update Record")

    form_data = {}
    for col in columns:
        form_data[col] = st.text_input(col)

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("ADD"):
        try:
            insert_data(table, form_data)
            st.success("Added Successfully")
        except Exception as e:
            st.error(str(e))

    if col2.button("UPDATE"):
        try:
            update_data(table, form_data, pk, form_data[pk])
            st.success("Updated Successfully")
        except Exception as e:
            st.error(str(e))

    if col3.button("DELETE"):
        try:
            delete_data(table, pk, form_data[pk])
            st.warning("Deleted Successfully")
        except Exception as e:
            st.error(str(e))

    if col4.button("CLEAR"):
        st.rerun()

# =========================
# MAIN APP
# =========================
def main_app():
    st.sidebar.title(f"👤 {st.session_state.user}")

    menu = [
        "Dashboard",
        "Customer",
        "Package",
        "Destination",
        "Hotel",
        "Transport",
        "Booking",
        "Payment",
        "Review",
        "Logout"
    ]

    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Dashboard":
        dashboard()

    elif choice == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    else:
        try:
            crud_page(choice)
        except:
            st.error(f"{choice} table not found")

# =========================
# RUN APP
# =========================
if not st.session_state.logged_in:
    login_page()
else:
    main_app()