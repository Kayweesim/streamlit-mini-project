import streamlit as st  
import pandas as pd

st.markdown("<h2 style='color: blue'>Synergy Page Content</h2>", unsafe_allow_html=True)


# Is there data where I can find for a given card, what other cards are used with it?

# Filter the deck win rates, maybe those that are above 50%? then 55%?
# Given a list of decks with 8 cards each, assuming millions of deck data.

# For a given card, find the top card that it used with it.
# The given card should be a winning condition, such as Hog Rider, Royal Giant, etc. because that card is the defining strategy of the deck itself.
# We are trying to find the strategy that is best and what cards work well with it
# Then, for those two cards, find the top card that is used with both of them.
# Iterate until you have the top 4 synergised cards.

# Known as Association Rule Mining

# Step 1 Choose a WC, then filter decks for that WC with a win rate above 50%
# Step 2 Filter decks with that WC.
# Step 3 Iterate and find most used card, then do that again until you get 4.
# Step 4 Display top 4 cards, and find the win rate of those 4 cards.

# https://www.kaggle.com/datasets/amitush/clash-royale-top-battles-decks-results


