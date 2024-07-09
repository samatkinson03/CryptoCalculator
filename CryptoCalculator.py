import os
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook, load_workbook
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go

def get_token_price(token_name):
    """Retrieve token price from CoinMarketCap."""
    url = f'https://coinmarketcap.com/currencies/{token_name}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        class_names = ['sc-d1ede7e3-0 hSTakI base-text', 'sc-d1ede7e3-0 fsQm base-text']
        for class_name in class_names:
            price_element = soup.find('span', {'class': class_name})
            if price_element:
                price_text = price_element.text.strip().replace('$', '').replace(',', '')
                return float(price_text)
    except (requests.RequestException, ValueError) as e:
        print(f"Error fetching price for {token_name}: {e}")
    return None

tokens = {
    "cardano": 9501.702241,
    "snek": 740803,
    "fren-ada-peepos": 14000000,
    "world-mobile-token": 6073.456088
}

file_name = 'ValueGraph.xlsx'
if not os.path.exists(file_name):
    wb = Workbook()
    ws = wb.active
    ws.append(["DateTime", "TotalValue"] + [token for token in tokens] + [token + ' Last Quantity' for token in tokens])
    wb.save(file_name)

wb = load_workbook(file_name)
ws = wb.active
last_row = ws.max_row

# Fetch previous quantities
last_quantities = {}
if last_row > 1:  # Ensure there's a previous row to fetch data from
    for col_index, token in enumerate(tokens):
        cell_value = ws.cell(row=last_row, column=3 + col_index + len(tokens)).value
        last_quantities[token] = float(cell_value) if cell_value is not None else 0
else:
    for token in tokens:
        last_quantities[token] = 0

current_quantities = tokens.copy()
token_values = {}
hover_texts = []

for token in tokens:
    price = get_token_price(token)
    token_values[token] = price * tokens[token] if price else 0

    last_quantity = last_quantities[token]
    quantity_change_text = ""
    if last_quantity != tokens[token]:
        quantity_change_text = f"{token} quantity change: {last_quantity} -> {tokens[token]}"
        print(f"Quantity change for {token}: was {last_quantity}, now {tokens[token]}")
    elif last_quantity == 0:
        quantity_change_text = f"{token} added with quantity {tokens[token]}"
        print(f"No previous quantity recorded for {token}. Added with quantity {tokens[token]}")
    
    hover_text = f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>Total Value: ${sum(token_values.values()):.2f}<br>{quantity_change_text}"
    hover_texts.append(hover_text)

total_value = sum(token_values.values())
ws.append([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total_value] + list(token_values.values()) + list(current_quantities.values()))
wb.save(file_name)

prospective = input("Do you want to enter prospective prices for your tokens? (yes/no): ").strip().lower()
if prospective == "yes":
    method = input("Do you want to enter a specific value or a multiplier for each token? (value/multiplier): ").strip().lower()
    prospective_values = {}
    for token in tokens:
        try:
            if method == "value":
                prospective_price = float(input(f"Enter prospective price for {token}: "))
            elif method == "multiplier":
                current_price = get_token_price(token) or 0
                multiplier = float(input(f"Enter multiplier for {token}: "))
                prospective_price = current_price * multiplier
            prospective_value = prospective_price * tokens[token]
            prospective_values[token] = prospective_value
            print(f"Prospective value of {token} at {prospective_price}: ${prospective_value:.2f}")
        except ValueError:
            print(f"Invalid input for {token}. Skipping...")

data = pd.read_excel(file_name)

# Adjusting the hover text for historical data
hover_texts = []  # Reset hover_texts to ensure correct alignment
for i, row in data.iterrows():
    hover_text = f"Date: {row['DateTime']}<br>Total Value: ${row['TotalValue']:.2f}"
    for token in tokens:
        token_last_quantity_col = token + ' Last Quantity'
        quantity_change_text = ""
        if token_last_quantity_col in data.columns:
            if i > 0 and row[token_last_quantity_col] != data.iloc[i-1][token_last_quantity_col]:
                quantity_change_text = f"{token} quantity change: {data.iloc[i-1][token_last_quantity_col]} -> {row[token_last_quantity_col]}"
            elif i == 0:
                quantity_change_text = f"{token} added with quantity {row[token_last_quantity_col]}"
        if quantity_change_text:
            hover_text += f"<br>{quantity_change_text}"
    hover_texts.append(hover_text)

fig = go.Figure(data=[go.Scatter(x=data['DateTime'], y=data['TotalValue'], mode='lines+markers', name='Total Value', text=hover_texts, hoverinfo='text')])
fig.update_layout(
    title='Total Value Over Time',
    xaxis_title='Date and Time',
    yaxis_title='Total Value ($)',
    dragmode='zoom',
    xaxis=dict(
        fixedrange=False
    ),
    yaxis=dict(
        fixedrange=False
    )
)
fig.show()
