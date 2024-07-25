#!/usr/bin/env python
# coding: utf-8

# In[2]:


import gspread
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, date
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from statistics import mean
from oauth2client.service_account import ServiceAccountCredentials

# Set page configuration
st.set_page_config(
    page_title="Ambulance Dashboard",
    page_icon=":chart:",
    layout="wide",  # Wide layout
    initial_sidebar_state="collapsed",  # Collapsed sidebar
)

scope=['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds=ServiceAccountCredentials.from_json_keyfile_name(r'unique-bonbon-304011-585cc22859d3.json',scope)
client=gspread.authorize(creds)
sheet=client.open_by_url(r'https://docs.google.com/spreadsheets/d/1CfLVfjrmV2K6wMEg6G-q2_Im2uP7sZ2GsVw0ZzmiJ0k/edit?usp=sharing').worksheets()
Districts=[i.title for i in sheet[6:]]

# Custom CSS for the boxes
summary_css = """
<style>
.box-container {
    display: flex;
    justify-content: space-between;
    padding: 10px;
    height: 5em;
    width: max-content;
}

.label-box {
    flex: 1;
    background-color: #6b8bc8; /* Gray background color for label box */
    color: white; /* Text color */
    font-weight: bold; /* Bold font weight */
    padding: 8px;
    text-align: center;
    line-height: 1.2;
}

.value-box {
    flex: 1;
    background-color: #fdd1a2; /* Pink background color for value box */
    color: black; /* Text color */
    font-weight: bold; /* Bold font weight */
    padding: 8px;
    display: flex;
    justify-content: center;
    align-items: center;
}
</style>
"""

# Custom CSS for the title
title_css = """
<style>
.title {
    text-align: center; /* Center align text */
    font-size: 36px; /* Larger font size */
    font-weight: bold; /* Bold font weight */
    color: black; /* Black text color */
}
</style>
"""
vertical_space_css = """
<style>
.spacer {
    margin-bottom: 100px;
}
</style>
"""

st.sidebar.title("**Navigate to**")
page=st.sidebar.radio("",["Overall Summary","District Level"])

if page=='District Level':
            # Display styled title using markdown with custom CSS
    st.markdown('<p class="title">DISTRICT LEVEL SUMMARY</p>', unsafe_allow_html=True)
    st.markdown(title_css, unsafe_allow_html=True)
    location_global=None
    def get_data(selected_district,date_range,level_of_detail,sheet,location_global):
        start_date=pd.to_datetime(date_range[0])
        end_date=pd.to_datetime(date_range[1])
        level_of_detail_lower=level_of_detail.lower()
        a='0'
        if level_of_detail_lower=="month":
            a="%b %Y"
        else:
            a="%Y"
        ambulance_df=pd.DataFrame(sheet[[i.title for i in sheet].index(selected_district)].get_values())

        def preprocess_data(ambulance_df):
          # Replace values in the first row starting with 'Ambulance' with values from the rows below
          def replace_values(ambulance_df):
              for col in ambulance_df.columns:
                  # Check if the element is a string before calling startswith
                  if isinstance(ambulance_df.at[0, col], str) and (ambulance_df.at[0, col].startswith('Ambulance') or ambulance_df.at[0, col].startswith('REC')):
                      ambulance_df.at[0, col] = ambulance_df.at[1, col]
              return ambulance_df

          def find_elements_in_another_list(list1, list2):
              for elem in list1:
                  if elem in list2:
                      return elem
              return None  # Return None if no element matches

          ambulance_df = replace_values(ambulance_df)
          # print("column ",ambulance_df)

          first_row_list = ambulance_df.iloc[0].tolist()

          # Find index of 'Total Distance Covered(KM)' in the first row"

          total_distance_list = ["Total Distance Covered", "Total Distance Covered(KM)","Total Distance Covered (KM)", "Total Distance", "Total KM"]
          no_of_patients_list = ["No. of patients served", "Total Patients Served", "Total Patients","Total no of Patients", "Total no of patients", "Total No. of patients served"]

          distance_column = find_elements_in_another_list(first_row_list, total_distance_list)
          patient_column = find_elements_in_another_list(first_row_list, no_of_patients_list)

          total_distance_index = ambulance_df.iloc[0].tolist().index(distance_column)
          # print("total_distance_index  ",total_distance_index)
          no_patients_index = ambulance_df.iloc[0].tolist().index(patient_column)
          # print("no_patients_index  ",no_patients_index)

          # Rearrange the columns
          columns_before_total_distance = ambulance_df.columns[:total_distance_index + 1]
          # print(columns_before_total_distance)
          columns_after_total_distance = ambulance_df.columns[no_patients_index:]
          # print(columns_after_total_distance)

          ambulance_df.iloc[:3, total_distance_index+1:no_patients_index] = ambulance_df.iloc[:3, 3:total_distance_index].values

          for col in ambulance_df.columns[3:total_distance_index]:
            ambulance_df.loc[0, col] = ambulance_df.loc[0, col] + ' (KM)'

          # Function to process the first row and strip till first (KM) from columns 3 to total_distance_index
          def strip_till_first_km(data):
            for i in range(3, total_distance_index):  # Loop through columns
                column_value = data[i]
                index_km = column_value.find("(KM)")
                if index_km != -1:
                    data[i] = column_value[:index_km + len("(KM)")].strip()

          # Function to process the first row and strip till (KM) including deleting (KM)
          def strip_till_km(data):
            for i in range(total_distance_index+1, no_patients_index):  # Loop through columns 3 to 10 (index 2 to 9)
                column_value = data[i]
                index_km = column_value.find("(KM)")
                if index_km != -1:
                    # Find the substring before (KM) and remove (KM) itself
                    data[i] = column_value[:index_km].rstrip()

          strip_till_first_km(ambulance_df.iloc[0])
          strip_till_km(ambulance_df.iloc[0])


          # List of new column names
          # ambulance_df.iloc[0]

          # Assign new column names to DataFrame
          ambulance_df.columns = ambulance_df.iloc[0]
          # Identify columns with empty string as name
          empty_columns = [col for col in ambulance_df.columns if col == '' or col == ' ' or col == 'SN' or col == 'S. No.']

          # Drop columns with empty string as name
          ambulance_df.drop(columns=empty_columns, inplace=True)

          # Drop empty rows
          ambulance_df.dropna(axis=0, how='all', inplace=True)

          def convert_to_datetime(x):
              try:
                  return pd.to_datetime(x)
              except:
                  return pd.NaT

          def remove_trailing_plus(string):
              if string.endswith('+'):
                  return string[:-1]
              return string

          ambulance_df['Admitted in Hospital']=ambulance_df['Admitted in Hospital'].apply(remove_trailing_plus)
          ambulance_df['Discharged from Hospital']=ambulance_df['Discharged from Hospital'].apply(remove_trailing_plus)

          def add_values_with_plus(string):
              a=string.split('+')
              sum_value=sum(int(i) for i in a if i.isnumeric()==True)
              return sum_value

          ambulance_df['Admitted in Hospital']=ambulance_df['Admitted in Hospital'].apply(add_values_with_plus)
          ambulance_df['Discharged from Hospital']=ambulance_df['Discharged from Hospital'].apply(add_values_with_plus)

          ambulance_df.rename(columns={ambulance_df.iloc[:,[no_patients_index-1,total_distance_index-1]].columns[0]:'Total Patients Served',
                                    ambulance_df.iloc[:,[no_patients_index-1,total_distance_index-1]].columns[1]:'Total Distance Covered(KM)'},inplace=True)

          old_col_names=ambulance_df.iloc[:,no_patients_index+5:no_patients_index+10].columns
          new_col_names=['Total Accident Cases', 'Total Pregnancy Cases', 'Any Sickness', 'Other Cases','Eye Camp Patients']

          ambulance_df.rename(columns=dict(zip(old_col_names,new_col_names)),inplace=True)

          ambulance_df.replace('-', '0', inplace=True)
          ambulance_df.replace('--', '0', inplace=True)
          ambulance_df.replace('', 0, inplace=True)
          ambulance_df.fillna(0, inplace=True)

          columns_to_check = ambulance_df.columns[2:no_patients_index]

          for col in columns_to_check:
          # print("col",col)
              ambulance_df[col] = ambulance_df[col].str.replace(r'\D', '', regex=True)
          # ambulance_df[col] = ambulance_df[col].apply(lambda x: x.replace(r'\D', '', regex=True) if isinstance(x, str) else x)
              # Fill empty strings with '0' before converting to integer
              ambulance_df[col] = ambulance_df[col].replace('', '0')  # Add this line
              # Fill NaN values with 0 before converting to integer
              ambulance_df[col] = ambulance_df[col].fillna(0)  # Add this line

          # Convert selected columns to integer type
              #ambulance_df[columns_to_check] = ambulance_df[columns_to_check].astype(int)
              ambulance_df[col] = ambulance_df[col].apply(lambda x: int(x))

          # Check for 0 values in specified columns range
          mask = ambulance_df[columns_to_check].eq(0).all(axis=1)

          # Filter out rows where NaN values exist in specified columns range
          ambulance_df = ambulance_df[~mask]

          ambulance_df['Date']=ambulance_df['Date'].apply(convert_to_datetime)
          ambulance_df = ambulance_df[ambulance_df['Date'].notnull()]
          ambulance_df['Total Distance Covered']=pd.to_numeric(ambulance_df['Total Distance Covered(KM)'])
          ambulance_df['Total Patients Served']=pd.to_numeric(ambulance_df['Total Patients Served'])
          ambulance_df['Total Accident Cases']=pd.to_numeric(ambulance_df['Total Accident Cases'])
          ambulance_df['Total Pregnancy Cases']=pd.to_numeric(ambulance_df['Total Pregnancy Cases'])
          ambulance_df['Any Sickness']=pd.to_numeric(ambulance_df['Any Sickness'])
          ambulance_df['Other Cases']=pd.to_numeric(ambulance_df['Other Cases'])
          ambulance_df['Eye Camp Patients']=pd.to_numeric(ambulance_df['Eye Camp Patients'],errors='coerce')

          #ambulance_df=ambulance_df[(ambulance_df['Date']>=start_date)&(ambulance_df['Date']<=end_date)]

          df_reset = ambulance_df[:-1].reset_index(drop=True)

          df_reset['District']=selected_district.split('-')[0]

          df_reset.columns=df_reset.columns.str.replace('\n','').str.lstrip()

          locations=df_reset.iloc[:,total_distance_index:no_patients_index-1].columns.values

          return df_reset,total_distance_index,no_patients_index,locations

        (ambulance_df1, total_distance_index, no_patients_index, locations)  = preprocess_data(ambulance_df)

        def agg_plots(ambulance_df1):
            if location_global is None:
                ambulance_df1['patients_location_sum']=0
                ambulance_df1['distance_location_sum']=0
                Patients_Pie=ambulance_df1.loc[:,locations].sum()
            else:
                ex_selected_locations_patients=[x for x in locations if x not in location_global]                
                ambulance_df1['patients_location_sum']=ambulance_df1.loc[:,ex_selected_locations_patients].sum(axis=1)
                Patients_Pie=ambulance_df1.loc[:,location_global].sum()
                ex_selected_locations_distance=[i.replace('/n','') +' (KM)' for i in ex_selected_locations_patients]
                ambulance_df1['distance_location_sum']=ambulance_df1.loc[:,ex_selected_locations_distance].sum(axis=1)
            min_date=ambulance_df1['Date'].min().date().strftime('%d-%b-%Y')
            max_date=ambulance_df1['Date'].max().date().strftime('%d-%b-%Y')
            Ambulance_By_Month=ambulance_df1.reset_index(drop=False)
            Ambulance_By_Month['Total Patients Served']=Ambulance_By_Month['Total Patients Served']-Ambulance_By_Month['patients_location_sum']
            Ambulance_By_Month['Total Distance Covered']=Ambulance_By_Month['Total Distance Covered']-Ambulance_By_Month['distance_location_sum']
            Ambulance_By_Month=Ambulance_By_Month[(Ambulance_By_Month['Date']>=start_date)&(Ambulance_By_Month['Date']<=end_date)]
            Ambulance_By_Month['Month']=pd.to_datetime(Ambulance_By_Month['Date']).dt.month.astype(str).str.pad(width=2,side='left',fillchar='0')
            Ambulance_By_Month['Year']=pd.to_datetime(Ambulance_By_Month['Date']).dt.year.astype(str)
            Ambulance_By_Month['Date']=Ambulance_By_Month['Date'].dt.strftime(a)
            Ambulance_By_Month['Yrmo']=(Ambulance_By_Month['Year']+Ambulance_By_Month['Month']).astype(int)
            Ambulance_By_Month['Year']=Ambulance_By_Month['Year'].astype(int)
            Ambulance_By_Month=Ambulance_By_Month.groupby(['Date'])[['Total Distance Covered','Total Patients Served','Admitted in Hospital','Discharged from Hospital','Yrmo','Year']].agg({'Total Distance Covered':sum,'Total Patients Served':sum,'Yrmo':mean,'Year':mean,'Admitted in Hospital':sum,'Discharged from Hospital':sum})
            #Ambulance_By_Month.set_index('Date',inplace=True)
            Ambulance_By_Month=Ambulance_By_Month.sort_values(by='Yrmo')
            Ambulance_By_Month=Ambulance_By_Month[['Total Distance Covered','Total Patients Served','Admitted in Hospital','Discharged from Hospital','Yrmo','Year']]
            Summary_Total=Ambulance_By_Month[['Total Distance Covered','Total Patients Served']].sum()
            return Ambulance_By_Month, Summary_Total, min_date, max_date,Patients_Pie

        (Ambulance_By_Month, Summary_Total,min_date,max_date,Patients_Pie)=agg_plots(ambulance_df1)

        Number_Of_PHC=no_patients_index-total_distance_index-1
        #Patients_Pie=ambulance_df1.iloc[:,total_distance_index:no_patients_index-1].sum()
        Disease_Type_Pie=ambulance_df1.iloc[:,no_patients_index+5:no_patients_index+10].sum()

        fig1 = go.Figure()

        # Bar trace
        fig1.add_trace(go.Bar(
            x=Ambulance_By_Month.index,
            y=Ambulance_By_Month['Total Distance Covered'],
            name='Total Distance Covered',
            marker_color='#ADD8E6'
        ))

        # Line trace
        fig1.add_trace(go.Scatter(
            x=Ambulance_By_Month.index,
            y=Ambulance_By_Month['Total Patients Served'],
            mode='lines',
            name='Total Patients Served',
            yaxis='y2',
            line=dict(color='#0444b0')
        ))

        # Update layout
        fig1.update_layout(
            title=f'Kilometers Driven/Persons Served',
            xaxis=dict(tickangle=45),
            yaxis=dict(title='Total Distance Covered', titlefont=dict(color='black')),
            yaxis2=dict(title='Total Patients Served', titlefont=dict(color='black'), overlaying='y', side='right'),
            legend=dict(x=0, y=1.1, traceorder='normal', font=dict(family='sans-serif', size=12), bgcolor='rgba(0,0,0,0)'),
        )

        if level_of_detail_lower=="year":
            fig1.update_xaxes(tickvals=list(range(int(min(Ambulance_By_Month.index)),int(max(Ambulance_By_Month.index))+1)))

        fig2 = go.Figure()

        # Add traces for 'Admitted in Hospital' and 'Discharged from Hospital'
        fig2.add_trace(go.Scatter(
            x=Ambulance_By_Month.index,
            y=Ambulance_By_Month['Admitted in Hospital'],
            mode='lines',
            name='Admitted in Hospital',
            line=dict(color='#f4921b', width=2)
        ))

        fig2.add_trace(go.Scatter(
            x=Ambulance_By_Month.index,
            y=Ambulance_By_Month['Discharged from Hospital'],
            mode='lines',
            name='Discharged from Hospital',
            line=dict(color='#4979cc', width=2)
        ))

        # Update layout
        fig2.update_layout(
            title=f'Number of Patients Admitted/Discharged',
            xaxis=dict(tickangle=45),
            yaxis=dict(title='Number Of Patients', titlefont=dict(color='black')),
            legend=dict(x=0, y=1.1, traceorder='normal', font=dict(family='sans-serif', size=12), bgcolor='rgba(0,0,0,0)')
        )

        fig3 = go.Figure()
        blue_colors =['#8BC1F7','#004B95','#BDE2B9','#38812F','#F4B678','#C46100','#B8BBBE','#009596','#A2D9D9','#F4C145','#F9E0A2','#B2B0EA','#5752D1','#C9190B']

        # Add pie trace
        fig3.add_trace(go.Pie(
            labels=Patients_Pie.name,
            values=Patients_Pie.values,
            textinfo='percent',
            insidetextorientation='radial',
            marker=dict(colors=blue_colors,line=dict(color='black',width=0.5))
        ))

        #fig3.update_traces(rotation=180)

        if location_global is None:
            # Update layout
            fig3.update_layout(
                title=f'% of Patients Served By Location',
                #title_x=0.2,  # Center align title horizontally
            )
        else:
            # Update layout
            fig3.update_layout(
                title=f'% of Patients Served By Selected Location(s)',
                #title_x=0.2,  # Center align title horizontally
            )

        fig4 = go.Figure()

        # Add pie trace
        fig4.add_trace(go.Pie(
            labels=Disease_Type_Pie.index,
            values=Disease_Type_Pie.values,
            textinfo='percent',
            insidetextorientation='radial',
            marker=dict(colors=['#F4C145','#F9E0A2','#B2B0EA','#5752D1','#C9190B'],line=dict(color='black',width=0.5))
        ))

        #fig4.update_traces(rotation=210)

        # Update layout
        fig4.update_layout(
            title=f'% of Patients Served By Type Of Ailment',
            #title_x=0.2,  # Center align title horizontally
        )

        Patients_Pie=pd.DataFrame(Patients_Pie)
        Patients_Pie.index=Patients_Pie.index.rename('Locations')
        Patients_Pie.columns=['Patients Served']

        Disease_Type_Pie=pd.DataFrame(Disease_Type_Pie)
        Disease_Type_Pie.index=Disease_Type_Pie.index.rename('Ailment Type')
        Disease_Type_Pie.columns=['Patients Served']

        if (Ambulance_By_Month['Total Distance Covered'].count()==0):
           return False, fig1, fig2, fig3, fig4, min_date, max_date,Number_Of_PHC,Summary_Total,locations,location_global, Ambulance_By_Month, Patients_Pie, Disease_Type_Pie
        else:
            return True, fig1, fig2, fig3, fig4, min_date, max_date,Number_Of_PHC,Summary_Total,locations,location_global, Ambulance_By_Month, Patients_Pie, Disease_Type_Pie

    col1,col2,col3,col4=st.columns([1,1,1,1])
    with col1:
        selected_district=st.selectbox('**Select a district**',Districts)
    with col3:
        date_range=st.date_input('**Enter date range**',min_value=datetime(2020,1,1),max_value=date.today(),key='date_range',format='DD/MM/YYYY')
    with col4:
        level_of_detail=st.selectbox('**Select frequency**',['Month','Year'])

    if location_global is None:
        (val,fig1,fig2,fig3,fig4,min_date,max_date,Number_Of_PHC,Summary_Total,locations,location_global,Ambulance_By_Month,Patients_Pie,Disease_Type_Pie)=get_data(selected_district,date_range,level_of_detail,sheet,location_global)

    with col2:
        location=st.selectbox('**Select a location**', locations, placeholder='All locations')
        location_global=location

    if location_global!=[]:
        (val,fig1,fig2,fig3,fig4,min_date,max_date,Number_Of_PHC,Summary_Total,locations,location_global,Ambulance_By_Month,Patients_Pie,Disease_Type_Pie)=get_data(selected_district,date_range,level_of_detail,sheet,location_global)

    if location_global==[]:
        col2,col3,col4=st.columns(3)
        # with col1:
        #     if val is True:
        #         selected_dist = selected_district.split('-')[0]
        #                 # Display boxes using HTML and CSS
        #         col1.markdown('<div class="box-container">'
        #                     f'<div class="label-box"># DISTRICTS</div>'
        #                     f'<div class="value-box">{selected_dist}</div>'
        #                     '</div>', unsafe_allow_html=True)
        #         col1.markdown(summary_css, unsafe_allow_html=True)
        #         # st.write(f"District: {selected_district.split('-')[0]}")
        with col2:
            if val is True:
                # Display boxes using HTML and CSS
                col2.markdown('<div class="box-container">'
                            f'<div class="label-box">Number Of Patients</div>'
                            f'<div class="value-box">{Summary_Total.iloc[1]:,}</div>'
                            '</div>', unsafe_allow_html=True)
                col2.markdown(summary_css, unsafe_allow_html=True)
                # st.write(f"Total Distance Covered (KM): {Summary_Total.iloc[0]}")
        with col3:
            if val is True:
                        # Display boxes using HTML and CSS
                col3.markdown('<div class="box-container">'
                            f'<div class="label-box">Distance Covered (KM)</div>'
                            f'<div class="value-box">{Summary_Total.iloc[0]:,}</div>'
                            '</div>', unsafe_allow_html=True)
                col3.markdown(summary_css, unsafe_allow_html=True)
                # st.write(f"Total Patients Served: {Summary_Total.iloc[1]}")
        with col4:
            if val is True:

                            # Display boxes using HTML and CSS
                col4.markdown('<div class="box-container">'
                            f'<div class="label-box">Number Of Ambulances</div>'
                            f'<div class="value-box">{Number_Of_PHC:,}</div>'
                            '</div>', unsafe_allow_html=True)
                col4.markdown(summary_css, unsafe_allow_html=True)
                # st.write(f"Number Of Ambulances: {Number_Of_PHC}")

        graph1,graph2=st.columns(2)#([1.15,1])
        with graph1:
            if val is True:
                st.plotly_chart(fig1)
            else:
                st.write(f"No data to display. Data for '{selected_district.split('-')[0]}' is present only between '{min_date}' and '{max_date}'")

        with graph2:
            if val is True:
                st.plotly_chart(fig2)
            #else:
                #st.write(f"No data to display. Data for '{selected_district}' is present only between '{min_date}' and '{max_date}'")

        #num_rows=st.slider("Select number of rows to be displayed:",1,len(Ambulance_By_Month),12)
        Ambulance_By_Month.sort_values(by='Yrmo',ascending=False,inplace=True)
        #Ambulance_By_Month['Yrmo']=Ambulance_By_Month['Yrmo'].astype(str).str.replace(',','',regex=True)
        #Ambulance_By_Month['Year']=Ambulance_By_Month['Year'].astype(str).str.replace(',','',regex=True)
        col2,col3,col4=st.columns([0.1,1,0.1])
        with col3:
            st.write(Ambulance_By_Month.iloc[:,0:4])

        graph3,graph4=st.columns(2)
        with graph3:
            if val is True:
                st.plotly_chart(fig3)
                st.write(Patients_Pie)

        with graph4:
            if val is True:
                st.plotly_chart(fig4)
                st.write(Disease_Type_Pie)

    else:
        col2,col3=st.columns(2)
        with col2:
            if val is True:
                # Display boxes using HTML and CSS
                col2.markdown('<div class="box-container">'
                            f'<div class="label-box">Number Of Patients</div>'
                            f'<div class="value-box">{Summary_Total.iloc[1]:,}</div>'
                            '</div>', unsafe_allow_html=True)
                col2.markdown(summary_css, unsafe_allow_html=True)
                # st.write(f"Total Distance Covered (KM): {Summary_Total.iloc[0]}")
        with col3:
            if val is True:
                        # Display boxes using HTML and CSS
                col3.markdown('<div class="box-container">'
                            f'<div class="label-box">Distance Covered (KM)</div>'
                            f'<div class="value-box">{Summary_Total.iloc[0]:,}</div>'
                            '</div>', unsafe_allow_html=True)
                col3.markdown(summary_css, unsafe_allow_html=True)
                # st.write(f"Total Patients Served: {Summary_Total.iloc[1]}")

        if val is True:
            st.plotly_chart(fig1)
            #num_rows=st.slider("Select number of rows to be displayed:",1,len(Ambulance_By_Month),12)
            Ambulance_By_Month.sort_values(by='Yrmo',ascending=False,inplace=True)
            #Ambulance_By_Month['Yrmo']=Ambulance_By_Month['Yrmo'].astype(str).str.replace(',','',regex=True)
            #Ambulance_By_Month['Year']=Ambulance_By_Month['Year'].astype(str).str.replace(',','',regex=True)
            col2,col3,col4=st.columns([0.5,1,0.5])
            with col3:
                st.write(Ambulance_By_Month.iloc[:,0:2])
            st.plotly_chart(fig3)
            col1,col2,col3=st.columns([1,1,1])
            with col2:
                st.write(Patients_Pie)
        else:
            st.write(f"No data to display. Data for {location_global} in {selected_district.split('-')[0]} is present only between '{min_date}' and '{max_date}'")

if page=='Overall Summary':
        # Display styled title using markdown with custom CSS
    st.markdown('<p class="title">OVERALL SUMMARY</p>', unsafe_allow_html=True)
    st.markdown(title_css, unsafe_allow_html=True)
    @st.cache_data(ttl=86400)
    def get_data_full(date_range,level_of_detail,_sheet):
        start_date=pd.to_datetime(date_range[0])
        end_date=pd.to_datetime(date_range[1])
        level_of_detail_lower=level_of_detail.lower()
        a='0'
        if level_of_detail_lower=="month":
            a="%b %Y"
        else:
            a="%Y"
        Districts=[i.title for i in sheet[6:]]
        flag=0
        for y in Districts:
            ambulance_df=pd.DataFrame(sheet[[i.title for i in sheet].index(y)].get_values())
            def preprocess_data_full(ambulance_df):
              # Replace values in the first row starting with 'Ambulance' with values from the rows below
              def replace_values(ambulance_df):
                  for col in ambulance_df.columns:
                      # Check if the element is a string before calling startswith
                      if isinstance(ambulance_df.at[0, col], str) and (ambulance_df.at[0, col].startswith('Ambulance') or ambulance_df.at[0, col].startswith('REC')):
                          ambulance_df.at[0, col] = ambulance_df.at[1, col]
                  return ambulance_df

              def find_elements_in_another_list(list1, list2):
                  for elem in list1:
                      if elem in list2:
                          return elem
                  return None  # Return None if no element matches

              ambulance_df = replace_values(ambulance_df)
              # print("column ",ambulance_df)

              first_row_list = ambulance_df.iloc[0].tolist()

              # Find index of 'Total Distance Covered(KM)' in the first row"

              total_distance_list = ["Total Distance Covered", "Total Distance Covered(KM)","Total Distance Covered (KM)", "Total Distance", "Total KM"]
              no_of_patients_list = ["No. of patients served", "Total Patients Served", "Total Patients","Total no of Patients", "Total no of patients", "Total No. of patients served"]

              distance_column = find_elements_in_another_list(first_row_list, total_distance_list)
              patient_column = find_elements_in_another_list(first_row_list, no_of_patients_list)

              total_distance_index = ambulance_df.iloc[0].tolist().index(distance_column)
              # print("total_distance_index  ",total_distance_index)
              no_patients_index = ambulance_df.iloc[0].tolist().index(patient_column)
              # print("no_patients_index  ",no_patients_index)

              # Rearrange the columns
              columns_before_total_distance = ambulance_df.columns[:total_distance_index + 1]
              # print(columns_before_total_distance)
              columns_after_total_distance = ambulance_df.columns[no_patients_index:]
              # print(columns_after_total_distance)

              ambulance_df.iloc[:3, total_distance_index+1:no_patients_index] = ambulance_df.iloc[:3, 3:total_distance_index].values

              for col in ambulance_df.columns[3:total_distance_index]:
                ambulance_df.loc[0, col] = ambulance_df.loc[0, col] + ' (KM)'

              # Function to process the first row and strip till first (KM) from columns 3 to total_distance_index
              def strip_till_first_km(data):
                for i in range(3, total_distance_index):  # Loop through columns
                    column_value = data[i]
                    index_km = column_value.find("(KM)")
                    if index_km != -1:
                        data[i] = column_value[:index_km + len("(KM)")].strip()

              # Function to process the first row and strip till (KM) including deleting (KM)
              def strip_till_km(data):
                for i in range(total_distance_index+1, no_patients_index):  # Loop through columns 3 to 10 (index 2 to 9)
                    column_value = data[i]
                    index_km = column_value.find("(KM)")
                    if index_km != -1:
                        # Find the substring before (KM) and remove (KM) itself
                        data[i] = column_value[:index_km].rstrip()

              strip_till_first_km(ambulance_df.iloc[0])
              strip_till_km(ambulance_df.iloc[0])


              # List of new column names
              # ambulance_df.iloc[0]

              # Assign new column names to DataFrame
              ambulance_df.columns = ambulance_df.iloc[0]
              # Identify columns with empty string as name
              empty_columns = [col for col in ambulance_df.columns if col == '' or col == ' ' or col == 'SN' or col == 'S. No.']

              # Drop columns with empty string as name
              ambulance_df.drop(columns=empty_columns, inplace=True)

              # Drop empty rows
              ambulance_df.dropna(axis=0, how='all', inplace=True)

              def convert_to_datetime(x):
                  try:
                      return pd.to_datetime(x)
                  except:
                      return pd.NaT

              def remove_trailing_plus(string):
                  if string.endswith('+'):
                      return string[:-1]
                  return string

              ambulance_df['Admitted in Hospital']=ambulance_df['Admitted in Hospital'].apply(remove_trailing_plus)
              ambulance_df['Discharged from Hospital']=ambulance_df['Discharged from Hospital'].apply(remove_trailing_plus)

              def add_values_with_plus(string):
                  a=string.split('+')
                  sum_value=sum(int(i) for i in a if i.isnumeric()==True)
                  return sum_value

              ambulance_df['Admitted in Hospital']=ambulance_df['Admitted in Hospital'].apply(add_values_with_plus)
              ambulance_df['Discharged from Hospital']=ambulance_df['Discharged from Hospital'].apply(add_values_with_plus)

              ambulance_df.rename(columns={ambulance_df.iloc[:,[no_patients_index-1,total_distance_index-1]].columns[0]:'Total Patients Served',
                                        ambulance_df.iloc[:,[no_patients_index-1,total_distance_index-1]].columns[1]:'Total Distance Covered(KM)'},inplace=True)

              old_col_names=ambulance_df.iloc[:,no_patients_index+5:no_patients_index+10].columns
              new_col_names=['Total Accident Cases', 'Total Pregnancy Cases', 'Any Sickness', 'Other Cases','Eye Camp Patients']

              ambulance_df.rename(columns=dict(zip(old_col_names,new_col_names)),inplace=True)

              ambulance_df.replace('-', '0', inplace=True)
              ambulance_df.replace('--', '0', inplace=True)
              ambulance_df.replace('', 0, inplace=True)
              ambulance_df.fillna(0, inplace=True)

              columns_to_check = ambulance_df.columns[2:no_patients_index]

              for col in columns_to_check:
              # print("col",col)
                  ambulance_df[col] = ambulance_df[col].str.replace(r'\D', '', regex=True)
              # ambulance_df[col] = ambulance_df[col].apply(lambda x: x.replace(r'\D', '', regex=True) if isinstance(x, str) else x)
                  # Fill empty strings with '0' before converting to integer
                  ambulance_df[col] = ambulance_df[col].replace('', '0')  # Add this line
                  # Fill NaN values with 0 before converting to integer
                  ambulance_df[col] = ambulance_df[col].fillna(0)  # Add this line

              # Convert selected columns to integer type
              ambulance_df[columns_to_check] = ambulance_df[columns_to_check].astype(int)

              # Check for 0 values in specified columns range
              mask = ambulance_df[columns_to_check].eq(0).all(axis=1)

              # Filter out rows where NaN values exist in specified columns range
              ambulance_df = ambulance_df[~mask]

              ambulance_df['Date']=ambulance_df['Date'].apply(convert_to_datetime)
              ambulance_df = ambulance_df[ambulance_df['Date'].notnull()]

              ambulance_df['Total Distance Covered']=pd.to_numeric(ambulance_df['Total Distance Covered(KM)'])
              ambulance_df['Total Patients Served']=pd.to_numeric(ambulance_df['Total Patients Served'])
              ambulance_df['Total Accident Cases']=pd.to_numeric(ambulance_df['Total Accident Cases'])
              ambulance_df['Total Pregnancy Cases']=pd.to_numeric(ambulance_df['Total Pregnancy Cases'])
              ambulance_df['Any Sickness']=pd.to_numeric(ambulance_df['Any Sickness'])
              ambulance_df['Other Cases']=pd.to_numeric(ambulance_df['Other Cases'])
              ambulance_df['Eye Camp Patients']=pd.to_numeric(ambulance_df['Eye Camp Patients'],errors='coerce')

              #ambulance_df=ambulance_df[(ambulance_df['Date']>=start_date)&(ambulance_df['Date']<=end_date)]

              df_reset = ambulance_df[:-1].reset_index(drop=True)

              df_reset['District']=y.split('-')[0]

              return df_reset,total_distance_index,no_patients_index

            (df_reset,total_distance_index,no_patients_index)=preprocess_data_full(ambulance_df)

            district_df=df_reset[['Date','District','Total Distance Covered(KM)','Total Patients Served','Admitted in Hospital', 'Discharged from Hospital','Total Accident Cases','Total Pregnancy Cases', 'Any Sickness','Other Cases', 'Eye Camp Patients']]

            if flag==0:
                result_df=district_df
                Total_Number_Of_PHC=no_patients_index-total_distance_index-1
            else:
                result_df=pd.concat([result_df,district_df],ignore_index=True)
                Total_Number_Of_PHC=Total_Number_Of_PHC+no_patients_index-total_distance_index-1
            flag=1

            def agg_plots_full(ambulance_df1):
                #Agg_df=ambulance_df[ambulance_df['Date'].notnull()]
                min_date=ambulance_df1['Date'].min().date().strftime('%d-%b-%Y')
                max_date=ambulance_df1['Date'].max().date().strftime('%d-%b-%Y')
                #ambulance_df1['Total Distance Covered']=pd.to_numeric(ambulance_df1['Total Distance Covered'])
                #ambulance_df1['Total Patients Served']=pd.to_numeric(ambulance_df1['Total Patients Served'])

                #Ambulance_By_Month=ambulance_df1[ambulance_df1['Date'].notnull()]
                Ambulance_By_Month=ambulance_df1.reset_index(drop=False)
                Ambulance_By_Month=Ambulance_By_Month[(Ambulance_By_Month['Date']>=start_date)&(Ambulance_By_Month['Date']<=end_date)]
                Ambulance_By_Month['Month']=pd.to_datetime(Ambulance_By_Month['Date']).dt.month.astype(str).str.pad(width=2,side='left',fillchar='0')
                Ambulance_By_Month['Year']=pd.to_datetime(Ambulance_By_Month['Date']).dt.year.astype(str)
                Ambulance_By_Month['Date']=Ambulance_By_Month['Date'].dt.strftime(a)
                Ambulance_By_Month['Yrmo']=(Ambulance_By_Month['Year']+Ambulance_By_Month['Month']).astype(int)
                Ambulance_By_Month['Year']=Ambulance_By_Month['Year'].astype(int)
                Ambulance_By_Disease=Ambulance_By_Month[['Total Accident Cases','Total Pregnancy Cases','Any Sickness','Other Cases','Eye Camp Patients']].sum()
                Ambulance_By_District=Ambulance_By_Month.groupby(['District'])[['Total Distance Covered(KM)','Total Patients Served','Admitted in Hospital','Discharged from Hospital']].agg({'Total Distance Covered(KM)':sum,'Total Patients Served':sum,'Admitted in Hospital':sum,'Discharged from Hospital':sum})
                Ambulance_By_Month=Ambulance_By_Month.groupby(['Date'])[['Total Distance Covered(KM)','Total Patients Served','Admitted in Hospital','Discharged from Hospital','Yrmo','Year']].agg({'Total Distance Covered(KM)':sum,'Total Patients Served':sum,'Yrmo':mean,'Year':mean,'Admitted in Hospital':sum,'Discharged from Hospital':sum})
                Ambulance_By_Month=Ambulance_By_Month.sort_values(by='Yrmo')
                Ambulance_By_Month=Ambulance_By_Month[['Total Distance Covered(KM)','Total Patients Served','Admitted in Hospital','Discharged from Hospital','Yrmo','Year']]
                Ambulance_By_District=Ambulance_By_District[['Total Distance Covered(KM)','Total Patients Served','Admitted in Hospital','Discharged from Hospital']]
                Ambulance_By_District=Ambulance_By_District.sort_values(by='Total Patients Served',ascending=False)
                Total_People_Served_In_Other_Districts=Ambulance_By_District.iloc[10:]['Total Patients Served'].sum()
                Ambulance_By_District_Top_10=Ambulance_By_District['Total Patients Served'].head(10)
                data={'District':['Others'],'Total Patients Served':[Total_People_Served_In_Other_Districts]}
                Others_Row=pd.DataFrame(data,index=data['District'])
                #Others_Row.set_index('District',inplace=True)
                Ambulance_By_District=pd.concat([Ambulance_By_District_Top_10,Others_Row])
                Summary_Total=Ambulance_By_Month[['Total Distance Covered(KM)','Total Patients Served']].sum()
                return Ambulance_By_Month, Ambulance_By_Disease, Ambulance_By_District, Summary_Total, min_date, max_date

            (Ambulance_By_Month_full, Ambulance_By_Disease_full, Ambulance_By_District_full, Summary_Total_full,min_date_full,max_date_full)=agg_plots_full(result_df)

            Patients_Pie_full=Ambulance_By_District_full['Total Patients Served']
            Disease_Pie_full=Ambulance_By_Disease_full

            fig1 = go.Figure()

            # Bar trace
            fig1.add_trace(go.Bar(
                x=Ambulance_By_Month_full.index,
                y=Ambulance_By_Month_full['Total Distance Covered(KM)'],
                name='Total Distance Covered',
                marker_color='#ADD8E6'
            ))

            # Line trace
            fig1.add_trace(go.Scatter(
                x=Ambulance_By_Month_full.index,
                y=Ambulance_By_Month_full['Total Patients Served'],
                mode='lines',
                name='Total Patients Served',
                yaxis='y2',
                line=dict(color='#0444b0')
            ))

            # Update layout
            fig1.update_layout(
                title=f'Kilometers Driven/Persons Served',
                xaxis=dict(tickangle=45),
                yaxis=dict(title='Total Distance Covered', titlefont=dict(color='black')),
                yaxis2=dict(title='Total Patients Served', titlefont=dict(color='black'), overlaying='y', side='right'),
                legend=dict(x=0, y=1.1, traceorder='normal', font=dict(family='sans-serif', size=12), bgcolor='rgba(0,0,0,0)'),
            )

            fig2 = go.Figure()

            # Add traces for 'Admitted in Hospital' and 'Discharged from Hospital'
            fig2.add_trace(go.Scatter(
                x=Ambulance_By_Month_full.index,
                y=Ambulance_By_Month_full['Admitted in Hospital'],
                mode='lines',
                name='Admitted in Hospital',
                line=dict(color='#f4921b', width=2)
            ))

            fig2.add_trace(go.Scatter(
                x=Ambulance_By_Month_full.index,
                y=Ambulance_By_Month_full['Discharged from Hospital'],
                mode='lines',
                name='Discharged from Hospital',
                line=dict(color='#4979cc', width=2)
            ))

            # Update layout
            fig2.update_layout(
                title=f'Number of Patients Admitted/Discharged',
                xaxis=dict(tickangle=45),
                yaxis=dict(title='Number Of Patients',titlefont=dict(color='black')),
                legend=dict(x=0, y=1.1, traceorder='normal', font=dict(family='sans-serif', size=12), bgcolor='rgba(0,0,0,0)')
            )

            fig3 = go.Figure()

            # Add pie trace
            fig3.add_trace(go.Pie(
                labels=Patients_Pie_full.index,
                values=Patients_Pie_full.values,
                textinfo='percent',
                insidetextorientation='radial',
                marker=dict(colors=['#8BC1F7','#004B95','#BDE2B9','#38812F','#F4B678','#C46100','#B8BBBE','#009596','#A2D9D9','#F4C145','#F9E0A2','#B2B0EA','#5752D1','#C9190B'],line=dict(color='black',width=0.5))
            ))

            #fig3.update_traces(rotation=270)

            # Update layout
            fig3.update_layout(
                title=f'% of Patients Served By District',
                #title_x=0.2,  # Center align title horizontally
            )

            fig4 = go.Figure()

            # Add pie trace
            fig4.add_trace(go.Pie(
                labels=Disease_Pie_full.index,
                values=Disease_Pie_full.values,
                textinfo='percent',
                insidetextorientation='radial',
                marker=dict(colors=['#F4C145','#F9E0A2','#B2B0EA','#5752D1','#C9190B'],line=dict(color='black',width=0.5))
            ))

            #fig4.update_traces(rotation=270)

            # Update layout
            fig4.update_layout(
                title=f'% of Patients Served By Type Of Ailment',
                #title_x=0.2,  # Center align title horizontally
            )

            Patients_Pie_full=pd.DataFrame(Patients_Pie_full)
            Patients_Pie_full.index=Patients_Pie_full.index.rename('Districts')
            Patients_Pie_full.columns=['Patients Served']

            Disease_Pie_full=pd.DataFrame(Disease_Pie_full)
            Disease_Pie_full.index=Disease_Pie_full.index.rename('Ailment Type')
            Disease_Pie_full.columns=['Patients Served']

        if (Ambulance_By_Month_full['Total Distance Covered(KM)'].count()==0):
            return False, fig1, fig2, fig3, fig4, Ambulance_By_Month_full,Total_Number_Of_PHC,Summary_Total_full,min_date_full,max_date_full,Ambulance_By_Month_full,Patients_Pie_full,Disease_Pie_full
        else:
            return True, fig1, fig2, fig3, fig4, Ambulance_By_Month_full,Total_Number_Of_PHC,Summary_Total_full,min_date_full,max_date_full,Ambulance_By_Month_full,Patients_Pie_full,Disease_Pie_full

    col1,col2=st.columns([1,1])
    with col1:
        date_range=st.date_input('**Enter date range**',value=(datetime(2020,1,1),date.today()),key='date_range',format='DD/MM/YYYY')
    with col2:
        level_of_detail=st.selectbox('**Select frequency**',['Month','Year'])

    (val,fig5,fig6,fig7,fig8,summary_df,Total_Number_Of_PHC,Summary_Total_full,min_date_full,max_date_full,Ambulance_By_Month_full,Patients_Pie_full,Disease_Pie_full)=get_data_full(date_range,level_of_detail,sheet)

    col2,col3,col4=st.columns(3)
    with col2:
        if val is True:
            # Display boxes using HTML and CSS
            col2.markdown('<div class="box-container">'
                        f'<div class="label-box">Number Of Patients</div>'
                        f'<div class="value-box">{Summary_Total_full.iloc[1]:,}</div>'
                        '</div>', unsafe_allow_html=True)
            col2.markdown(summary_css, unsafe_allow_html=True)
            # st.write(f"Total Distance Covered (KM): {Summary_Total_full.iloc[1]}")
    with col3:
        if val is True:
                    # Display boxes using HTML and CSS
            col3.markdown('<div class="box-container">'
                        f'<div class="label-box">Distance Covered (KM)</div>'
                        f'<div class="value-box">{Summary_Total_full.iloc[0]:,}</div>'
                        '</div>', unsafe_allow_html=True)
            col3.markdown(summary_css, unsafe_allow_html=True)
            # st.write(f"Total Patients Served: {Summary_Total_full.iloc[0]}")
    with col4:
        if val is True:
                        # Display boxes using HTML and CSS
            col4.markdown('<div class="box-container">'
                        f'<div class="label-box">Number Of Ambulances</div>'
                        f'<div class="value-box">{Total_Number_Of_PHC:,}</div>'
                        '</div>', unsafe_allow_html=True)
            col4.markdown(summary_css, unsafe_allow_html=True)
            # st.write(f"Number Of Ambulances: {Total_Number_Of_PHC}")

    graph1,graph2=st.columns(2)
    with graph1:
        if val is True:
            st.plotly_chart(fig5)
        else:
            st.write(f"No data to display. Data is present only between '{min_date_full}' and '{max_date_full}'")

    with graph2:
        if val is True:
            st.plotly_chart(fig6)
        #else:
            #st.write(f"No data to display. Data is present only between '{min_date_full}' and '{max_date_full}'")

    #num_rows=st.slider("Select number of rows to be displayed:",1,len(Ambulance_By_Month_full),12)
    Ambulance_By_Month_full.sort_values(by='Yrmo',ascending=False,inplace=True)
    #Ambulance_By_Month_full['Yrmo']=Ambulance_By_Month_full['Yrmo'].astype(str).str.replace(',','',regex=True)
    #Ambulance_By_Month_full['Year']=Ambulance_By_Month_full['Year'].astype(str).str.replace(',','',regex=True)

    col2,col3,col4=st.columns([0.1,1,0.1])
    with col3:
        st.write(Ambulance_By_Month_full.iloc[:,0:4])

    graph3,graph4=st.columns([1,1])
    with graph3:
        if val is True:
            st.plotly_chart(fig7)
            graph5,graph6=st.columns([0.3,1])
            with graph6:
                st.write(Patients_Pie_full)
        #else:
            #st.write(f"No data to display. Data for '{selected_district}' is present only between '{min_date}' and '{max_date}'")
    with graph4:
        if val is True:
            st.plotly_chart(fig8)
            graph5,graph6=st.columns([0.1,1])
            with graph6:
                st.write(Disease_Pie_full)
        

    #if val is True:
     #   st.plotly_chart(fig7)
      #  #else:
            #st.write(f"No data to display. Data is present only between '{min_date_full}' and '{max_date_full}'")
       # st.plotly_chart(fig8)
