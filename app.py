import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import random
import plotly.express as px

sns.set_style("darkgrid")

# Set page configuration for landscape orientation
st.set_page_config(layout="wide")

# Load data
geojson_file = 'dom_level1.geojson'
general_info_file = 'municipality_cards_v2.csv'
age_distribution_file = 'municipality_cards_v3.csv'

# Data
df = pd.read_csv("scoring.csv")

# Load GeoJSON data
gdf = gpd.read_file(geojson_file)

# Load CSV data
general_info_df = pd.read_csv(general_info_file)
age_distribution_df = pd.read_csv(age_distribution_file)

# Format general information data
general_info_df['Population'] = general_info_df['Population'].apply(lambda x: f"{x:,}")
general_info_df['Poor population impacted by shock'] = general_info_df['Poor population impacted by shock'].apply(lambda x: f"{x:,}")
general_info_df['Unemployed after shock'] = general_info_df['Unemployed after shock'].apply(lambda x: f"{x:,}")
general_info_df['Women-headed HH'] = general_info_df['Women-headed HH'].apply(lambda x: f"{x:,}")
general_info_df['HH with People with Disabilities'] = general_info_df['HH with People with Disabilities'].apply(lambda x: f"{x:,}")
general_info_df['Poverty line'] = general_info_df['Poverty line'].apply(lambda x: f"US$ {x:,}")

# Dropdown for selecting region_c
default_region_c = 'mun1'
selected_region_c = st.selectbox('Select Municipality', general_info_df['region_c'].unique(), index=general_info_df['region_c'].tolist().index(default_region_c))

# Create a Folium map
map_center = [gdf['geometry'].centroid.y.mean(), gdf['geometry'].centroid.x.mean()]
m = folium.Map(location=map_center, zoom_start=8)

category_colors = {
    "mun1": "green",
    "mun2": "blue",
    "mun3": "red",
    "mun4": "yellow",
    "mun5": "purple",
    "mun6": "orange",
    "mun7": "brown",
    "mun8": "magenta",
    "mun9": "grey",
    "mun10": "darblue"
}

# Add polygons for each municipality
folium.GeoJson(
    gdf,
    name='Municipalities',
    tooltip=folium.features.GeoJsonTooltip(fields=['region_n'], aliases=['Municipality: ']),
    style_function = lambda feature: {
        "fillColor": category_colors.get(feature["properties"]["region_c"].lower(), "#ffff00"),
        "color": "black",
        "weight": 2,
        "dashArray": "5, 5",
    }
).add_to(m)

# Display the map
# st_folium(m, width=700, height=500, key="map_display")

# Filter the data based on the selected municipality
municipality_data_gen = general_info_df[general_info_df['region_c'] == selected_region_c]
municipality_data_gen = municipality_data_gen.drop(columns = "region_c")
municipality_data_gen = municipality_data_gen.T 
municipality_data_gen.columns = [" "]
municipality_data_age = age_distribution_df[age_distribution_df['region_c'] == selected_region_c]

# Define initial values for program inputs
initial_values = {
    'Program 1': {'beneficiaries': 100, 'value': 100.0},
    'Program 2': {'beneficiaries': 60, 'value': 120.0},
    'Program 3': {'beneficiaries': 10, 'value': 100.0},
    'Program 4': {'beneficiaries': 80, 'value': 25.0},
    'Program 5': {'beneficiaries': 90, 'value': 50.0},
    'Program 6': {'beneficiaries': 100, 'value': 25.0},
}

# Layout for row 1
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader('Map')
    st_folium(m, width = 600, height=400, key="map_display_2")

with col2:
    st.subheader('Age Distribution')
    age_distribution = municipality_data_age
    fig = px.bar(age_distribution, x='Population', y='Age Group', orientation='h', height=400)
    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.subheader('General Information')
    st.write(municipality_data_gen)

# Layout for row 2
col4, col5 = st.columns((2, 1))

with col4:
    st.subheader('Program Inputs')

    # Create a table for program inputs
    programs = ['Program 1', 'Program 2', 'Program 3', 'Program 4', 'Program 5', 'Program 6']
    input_data = pd.DataFrame(columns=['Program', '% de elegibles (hogares)', 'Monto asignado por hogares (en USD)'])
    input_rows = []

    col1, col2, col3 = st.columns([1, 2, 2])
    with st.form(key='program_inputs'):
        form = st.container()
        form.markdown('<div class="compact-form">', unsafe_allow_html=True)
        for idx, program in enumerate(programs):
            col1, col2, col3 = form.columns([1, 2, 2])
            with col1:
                st.write(program)
            with col2:
                beneficiaries = st.number_input(f'Beneficiaries for {program}', min_value=0, value=initial_values[program]['beneficiaries'], key=f'beneficiary_{program}_{selected_region_c}_{idx}_beneficiaries', label_visibility="collapsed")
            with col3:
                values = st.number_input(f'Value for {program}', min_value=0.0, value=initial_values[program]['value'], key=f'value_{program}_{selected_region_c}_{idx}_value', label_visibility="collapsed")
            input_rows.append({'Program': program, '% de elegibles (hogares)': beneficiaries, 'Monto asignado por hogares (en USD)': values})
        form.markdown('</div>', unsafe_allow_html=True)

        submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        input_data = pd.concat([input_data, pd.DataFrame(input_rows)], ignore_index=True)

with col5:
    st.subheader('Score')
    
    # Beneficiaries
    temp  = df[df.region_c == selected_region_c].copy()
    temp  = temp.reset_index(drop = True)
    names = [i for i in temp.columns if "benef" in i][:-2]
    name_ = []
    for name in names:
        temp[f"{name}_"] = temp[name] * temp.factor_ch * temp.afectados
        name_.append(f"{name}_")
        
    benef = temp[name_].sum().reset_index()
    benef.columns = ['Programa','Benef']
    
    temp['costo'] = temp.factor_ch * temp.afectados * temp.shock
    
    
    if not input_data.empty and sum(input_data['% de elegibles (hogares)']) > 0:
        num = benef.Benef * (input_data['% de elegibles (hogares)'] / 100) * input_data['Monto asignado por hogares (en USD)']
        num = num.sum()
        den = temp['costo'].sum()
        score = (num/den)*100
        
        #score = (sum(input_data['Monto asignado por hogares (en USD)']) / sum(input_data['% de elegibles (hogares)'])) * 100
    else:
        score = 0
    
    fig = px.pie(values=[score, 100 - score], names=[f'{score:.2f}%', ''], hole=0.7)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False, height=500)
    st.plotly_chart(fig, use_container_width=True)
