import streamlit as st
import sqlalchemy
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pymysql
import altair as alt
import plotly.express as px

query = """
    WITH base AS (
    	SELECT
    		DATE_ADD(cbd.date, INTERVAL(-WEEKDAY(cbd.date)) DAY) week_monday,
    		country,
    		confirmed,
    		deaths,
    		recovered
    	FROM covid19_basic_differences cbd
    	WHERE cbd.date >= '2021-01-01'
        GROUP BY
            1,2
    )
    SELECT
    	b.week_monday,
    	b.country,
    	b.confirmed,
    	b.deaths,
    	b.recovered,
    	c.iso3
    FROM base b
    LEFT JOIN countries c
    	ON c.country = b.country
    WHERE 1=1
    	AND c.continent = 'Europe'
"""
## connection
user = "student"
password = "p7%40vw7MCatmnKjy7"
conn_string = f"mysql+pymysql://{user}:{password}@data.engeto.com/data"
alchemy_conn = sqlalchemy.create_engine(conn_string)

query_result = pd.read_sql(query, alchemy_conn)

## settings
st.set_page_config(layout='wide', initial_sidebar_state='expanded')

## filters
country_filter = st.sidebar.multiselect('Country filter:', query_result['country'].unique())
dates_options = query_result.week_monday.unique()

date_filter = st.sidebar.slider('Select date range:', min(dates_options), max(dates_options), (min(dates_options),max(dates_options)))

measure_filter = st.sidebar.radio('Select measure', ['confirmed', 'deaths', 'recovered'])
measure_columns = ['week_monday', 'country'] + [measure_filter]
query_result = query_result[measure_columns]
# st.write(query_result)

# ## chart matplotlib
# st.markdown(f"<h1 style='text-align: center; color: black;'>{measure_filter.title()} cases</h1>", unsafe_allow_html=True)
# figure, ax = plt.subplots(1,1, figsize=(20,5))
# for country in country_filter:
#     filt_country_df = query_result[(query_result['country'] == country)
#                                     & (query_result['week_monday'] >= date_filter[0] )
#                                     & (query_result['week_monday'] <= date_filter[1] )]
#     xax= filt_country_df['week_monday']
#     yax= filt_country_df[f'{measure_filter}']
#
#     ax.plot(xax,yax, label = f"{country}")
#     ax.set_xlabel('Week_monday')
#     ax.set_ylabel('Confirmed cases')
#     ax.set_xticklabels(xax,rotation=90)
#     ax.legend(loc='upper right',ncol=4)
#
# st.pyplot(figure)

## dataframe for altair chart
df_altair = query_result[(query_result['country'].isin(country_filter))
                                & (query_result['week_monday'] >= date_filter[0] )
                                & (query_result['week_monday'] <= date_filter[1] )]

## altair chart definition
selection = alt.selection_multi(fields=['country'], bind='legend')
brush = alt.selection(type='interval', encodings=['x'])
chart = alt.Chart(df_altair).mark_line(point=True).encode(
    x='week_monday',
    y=f'{measure_filter}',
    color='country',
    opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
    tooltip=['week_monday', f'{measure_filter}']
).add_selection(selection).add_selection(brush)

barchart = alt.Chart(df_altair).mark_bar(size=20).transform_aggregate(
    measure=f'sum({measure_filter}):Q',
    groupby=['week_monday']
).encode(
    x='week_monday:T',
    y='measure:Q'
).transform_filter(brush)

col1, col2 = st.columns((3,1))

ch = alt.vconcat(chart, barchart).resolve_scale(color='independent')
col1.altair_chart(ch, use_container_width=True)

table_df = query_result[query_result['week_monday'] == query_result['week_monday'].max()]
table_df = table_df[['country',f'{measure_filter}']].sort_values(f'{measure_filter}', ascending=False).head(10)
col2.table(table_df)

## plotly Chart
query_result = pd.read_sql(query, alchemy_conn)
df_plotly = query_result.copy()

st.write(df_plotly)

df_plotly.week_monday = df_plotly.week_monday.astype(str)
df_plotly = df_plotly[(df_plotly['confirmed'] >= 0) & (df_plotly['deaths'] >= 0) & (df_plotly['recovered'] >= 0)]


fig = px.scatter_geo(
    df_plotly,
    locations='iso3',
    color='country',
    hover_name='country',
    size=f'{measure_filter}',
    projection='orthographic',
    animation_frame='week_monday'
)

st.plotly_chart(fig)
