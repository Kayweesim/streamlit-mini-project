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


    # Important Filter
    card_name = st.text_input("Card Name")

    # Secondary Filters
    card_elixir_cost = st.slider("Elixir Cost", min_value=0, max_value=10)
    card_rarity = st.selectbox("Card Rarity", options = df['rarity'].unique()) 
    card_win_rate = st.slider("Card Win Rate", min_value = df['Win Rate'].min(), max_value = df['Win Rate'].max(), step=0.1)  

    # print(df['Win Rate'].min(), df['Win Rate'].max())

    mask = pd.Series([True] * len(df))

    mask &= df['Card'].str.contains(card_name, case=False, na=False)

    if (card_elixir_cost != 0):
        mask &= df['elixirCost'] == card_elixir_cost

    mask &= df['rarity'] == card_rarity
    mask &= df['Win Rate'] >= card_win_rate
    

    filtered_df = df[mask]

    # Order by win rate ascending
    filtered_df = filtered_df.sort_values(by = 'Win Rate', ascending = True)

    # Display filtered data
    st.dataframe(filtered_df)

    # Inefficient method

    # if submit_button:
    #     st.write(f"Filtering cards with name: {card_name}, elixir cost: {card_elixir_cost}, rarity: {card_rarity}")
        
    #     # Card Name Filter
    #     if card_name:
    #         df = df[df['Card'].str.contains(card_name, case=False, na=False)]

    #     # Secondary Filters (Elixir and Rarity)
    #     df = df[df['elixirCost'] == card_elixir_cost]
    #     df = df[df['rarity'] == card_rarity]
    #     st.dataframe(df)


# Page Navigation
dashboard_page = st.Page(dashboard_home, title="Dashboard", icon="🏠")
synergy = st.Page("synergy.py", title="Synergy Page", icon="📋")
page_2 = st.Page("page_2.py", title="Page 2", icon="📄")
pg = st.navigation([dashboard_page, synergy, page_2])


pg.run()
