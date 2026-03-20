import streamlit as st
import kagglehub
import os
import pandas as pd

@st.cache_resource  
def load_dataset():
    # Download dataset, return the path from the dataset where it can be accessed
    path = kagglehub.dataset_download("hrish4/clash-royale-cards-data")
    csv_file = [file for file in os.listdir(path) if file.endswith('.csv')][0]
    df = pd.read_csv(os.path.join(path, csv_file))

    return df

def dashboard_home():
    df = load_dataset()

    st.title("Clash Royale Cards Dashboard")
    st.markdown(
        """
        Clash Royale Card Collection dashboard, just a fun and mini project to view cards based on specifications.
        """
    )

    # Display data
    st.dataframe(df.head())

    # Form Filter
    st.divider()
    st.write("Filter cards by specifications:")

    # Based on the user, collect their elixirCost, rarity and Card name

    # Create a form
    with st.form("filter_card_form"):

        # Important Filter
        card_name = st.text_input("Card Name")


        # Secondary Filters
        card_elixir_cost = st.slider("Elixir Cost", min_value=0, max_value=10)
        card_rarity = st.selectbox("Card Rarity", options = df['rarity'].unique())
        submit_button = st.form_submit_button("Submit")
    
    if submit_button:
        st.write(f"Filtering cards with name: {card_name}, elixir cost: {card_elixir_cost}, rarity: {card_rarity}")
        
        # Card Name Filter
        if card_name:
            df = df[df['name'].str.contains(card_name, case=False, na=False)]

        # Secondary Filters (Elixir and Rarity)
        df = df[df['elixirCost'] == card_elixir_cost]
        df = df[df['rarity'] == card_rarity]
        st.dataframe(df)

# Page Navigation
dashboard_page = st.Page(dashboard_home, title="Dashboard", icon="🏠")
main_page = st.Page("main_page.py", title="Main Page", icon="📋")
page_2 = st.Page("page_2.py", title="Page 2", icon="📄")
pg = st.navigation([dashboard_page, main_page, page_2])


pg.run()
