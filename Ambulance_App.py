#!/usr/bin/env python
# coding: utf-8

# In[2]:


import gspread
import pandas as pd
import streamlit as st
from datetime import datetime, date
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from statistics import mean
import xlsxwriter
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
}

.label-box {
    flex: 1;
    background-color: #808080; /* Gray background color for label box */
    color: white; /* Text color */
    font-weight: bold; /* Bold font weight */
    padding: 20px;
    text-align: center;

}

.value-box {
    flex: 1;
    background-color: #FFC0CB; /* Pink background color for value box */
    color: black; /* Text color */
    font-weight: bold; /* Bold font weight */
    padding: 20px;
    text-align: center;
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
    def get_data(selected_district,date_range,level_of_detail,sheet):
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
    
          df_reset['District']=selected_district.split('-')[0]
    
          return df_reset,total_distance_index,no_patients_index

        (ambulance_df1, total_distance_index, no_patients_index)  = preprocess_data(ambulance_df)
    
        def agg_plots(ambulance_df1):
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
            Ambulance_By_Month=Ambulance_By_Month.groupby(['Date'])[['Total Distance Covered','Total Patients Served','Admitted in Hospital','Discharged from Hospital','Yrmo','Year']].agg({'Total Distance Covered':sum,'Total Patients Served':sum,'Yrmo':mean,'Year':mean,'Admitted in Hospital':sum,'Discharged from Hospital':sum})
            #Ambulance_By_Month.set_index('Date',inplace=True)
            Ambulance_By_Month=Ambulance_By_Month.sort_values(by='Yrmo')
            Ambulance_By_Month=Ambulance_By_Month[['Total Distance Covered','Total Patients Served','Admitted in Hospital','Discharged from Hospital','Yrmo','Year']]
            Summary_Total=Ambulance_By_Month[['Total Distance Covered','Total Patients Served']].sum()
            return Ambulance_By_Month, Summary_Total, min_date, max_date
    
        (Ambulance_By_Month, Summary_Total,min_date,max_date)=agg_plots(ambulance_df1)
    
        Number_Of_PHC=no_patients_index-total_distance_index-1
        Patients_Pie=ambulance_df1.iloc[:,total_distance_index:no_patients_index-1].sum()
        Disease_Type_Pie=ambulance_df1.iloc[:,no_patients_index+5:no_patients_index+10].sum()
    
        fig1 = go.Figure()
    
        # Bar trace
        fig1.add_trace(go.Bar(
            x=Ambulance_By_Month.index,
            y=Ambulance_By_Month['Total Distance Covered'],
            name='Total Distance Covered',
            marker_color='cyan'
        ))
    
        # Line trace
        fig1.add_trace(go.Scatter(
            x=Ambulance_By_Month.index,
            y=Ambulance_By_Month['Total Patients Served'],
            mode='lines',
            name='Total Patients Served',
            yaxis='y2',
            line=dict(color='blue')
        ))
    
        # Update layout
        fig1.update_layout(
            title=f'Kilometers Driven/Persons Served By {level_of_detail}',
            xaxis=dict(tickangle=45),
            yaxis=dict(title='Total Distance Covered', titlefont=dict(color='cyan')),
            yaxis2=dict(title='Total Patients Served', titlefont=dict(color='blue'), overlaying='y', side='right'),
            legend=dict(x=0, y=1.1, traceorder='normal', font=dict(family='sans-serif', size=12), bgcolor='rgba(0,0,0,0)'),
        )
    
        fig2 = go.Figure()
    
        # Add traces for 'Admitted in Hospital' and 'Discharged from Hospital'
        fig2.add_trace(go.Scatter(
            x=Ambulance_By_Month.index,
            y=Ambulance_By_Month['Admitted in Hospital'],
            mode='lines+markers',
            name='Admitted in Hospital',
            line=dict(color='green', width=2)
        ))
    
        fig2.add_trace(go.Scatter(
            x=Ambulance_By_Month.index,
            y=Ambulance_By_Month['Discharged from Hospital'],
            mode='lines+markers',
            name='Discharged from Hospital',
            line=dict(color='red', width=2)
        ))
    
        # Update layout
        fig2.update_layout(
            title=f'Number of Patients Admitted/Discharged By {level_of_detail}',
            xaxis=dict(tickangle=45),
            yaxis=dict(title='Number Of Patients'),
            legend=dict(x=0, y=1.1, traceorder='normal', font=dict(family='sans-serif', size=12), bgcolor='rgba(0,0,0,0)')
        )
    
        fig3 = go.Figure()
    
        # Add pie trace
        fig3.add_trace(go.Pie(
            labels=Patients_Pie.index,
            values=Patients_Pie.values,
            textinfo='percent+label',
            insidetextorientation='radial',
            marker=dict(line=dict(color='black', width=2)),
        ))
    
        # Update layout
        fig3.update_layout(
            title=f'% of Patients Served By Location',
            title_x=0.2,  # Center align title horizontally
        )
    
        fig4 = go.Figure()
    
        # Add pie trace
        fig4.add_trace(go.Pie(
            labels=Disease_Type_Pie.index,
            values=Disease_Type_Pie.values,
            textinfo='percent+label',
            insidetextorientation='radial',
            marker=dict(line=dict(color='black', width=2)),
        ))
    
        # Update layout
        fig4.update_layout(
            title=f'% of Patients Served By Type Of Ailment',
            title_x=0.2,  # Center align title horizontally
        )
    
        if (Ambulance_By_Month['Total Distance Covered'].count()==0):
           return False, fig1, fig2, fig3, fig4, min_date, max_date,Number_Of_PHC,Summary_Total
        else:
            return True, fig1, fig2, fig3, fig4, min_date, max_date,Number_Of_PHC,Summary_Total

    col1,col2,col3=st.columns([1,1,1])
    with col1:
        selected_district=st.selectbox('**Select a district**',Districts)
    with col2:
        date_range=st.date_input('**Enter date range**',value=(datetime(2020,1,1),date.today()),key='date_range',format='DD/MM/YYYY')
    with col3:
        level_of_detail=st.selectbox('**Select frequency**',['Month','Year'])


    (val,fig1,fig2,fig3,fig4,min_date,max_date,Number_Of_PHC,Summary_Total)=get_data(selected_district,date_range,level_of_detail,sheet)

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
                        f'<div class="label-box"># PATIENTS</div>'
                        f'<div class="value-box">{Summary_Total.iloc[1]}</div>'
                        '</div>', unsafe_allow_html=True)
            col2.markdown(summary_css, unsafe_allow_html=True)
            # st.write(f"Total Distance Covered (KM): {Summary_Total.iloc[0]}")
    with col3:
        if val is True:
                    # Display boxes using HTML and CSS
            col3.markdown('<div class="box-container">'
                        f'<div class="label-box">DISTANCE COVERED</div>'
                        f'<div class="value-box">{Summary_Total.iloc[0]}</div>'
                        '</div>', unsafe_allow_html=True)
            col3.markdown(summary_css, unsafe_allow_html=True)
            # st.write(f"Total Patients Served: {Summary_Total.iloc[1]}")
    with col4:
        if val is True:

                        # Display boxes using HTML and CSS
            col4.markdown('<div class="box-container">'
                        f'<div class="label-box"># Ambulances</div>'
                        f'<div class="value-box">{Number_Of_PHC}</div>'
                        '</div>', unsafe_allow_html=True)
            col4.markdown(summary_css, unsafe_allow_html=True)
            # st.write(f"Number Of Ambulances: {Number_Of_PHC}")

    graph1,graph2=st.columns(2)#([1.15,1])
    with graph1:
        if val is True:
            st.plotly_chart(fig1)
        else:
            st.write(f"No data to display. Data for '{selected_district}' is present only between '{min_date}' and '{max_date}'")

    with graph2:
        if val is True:
            st.plotly_chart(fig2)
        #else:
            #st.write(f"No data to display. Data for '{selected_district}' is present only between '{min_date}' and '{max_date}'")

    graph3,graph4=st.columns(2)#([max((Number_Of_PHC/8.5),0.9),1])
    with graph3:
        if val is True:
            st.plotly_chart(fig3)
        #else:
            #st.write(f"No data to display. Data for '{selected_district}' is present only between '{min_date}' and '{max_date}'")
    with graph4:
        if val is True:
            st.plotly_chart(fig4)

if page=='Overall Summary':
    def get_data_full(date_range,level_of_detail,sheet):
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
            if y=='Jhabua-8':
                continue
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
                Ambulance_By_Month=Ambulance_By_Month.groupby(['Date'])[['Total Distance Covered(KM)','Total Patients Served','Admitted in Hospital','Discharged from Hospital','Yrmo','Year']].agg({'Total Distance Covered(KM)':sum,'Total Patients Served':sum,'Yrmo':mean,'Year':mean,'Admitted in Hospital':sum,'Discharged from Hospital':sum})
                #Ambulance_By_Month.set_index('Date',inplace=True)
                Ambulance_By_Month=Ambulance_By_Month.sort_values(by='Yrmo')
                Ambulance_By_Month=Ambulance_By_Month[['Total Distance Covered(KM)','Total Patients Served','Admitted in Hospital','Discharged from Hospital','Yrmo','Year']]
                Summary_Total=Ambulance_By_Month[['Total Distance Covered(KM)','Total Patients Served']].sum()
                return Ambulance_By_Month, Summary_Total, min_date, max_date
    
            (Ambulance_By_Month_full, Summary_Total_full,min_date_full,max_date_full)=agg_plots_full(result_df)
            
            fig1 = go.Figure()
    
            # Bar trace
            fig1.add_trace(go.Bar(
                x=Ambulance_By_Month.index,
                y=Ambulance_By_Month['Total Distance Covered'],
                name='Total Distance Covered',
                marker_color='cyan'
            ))
        
            # Line trace
            fig1.add_trace(go.Scatter(
                x=Ambulance_By_Month.index,
                y=Ambulance_By_Month['Total Patients Served'],
                mode='lines',
                name='Total Patients Served',
                yaxis='y2',
                line=dict(color='blue')
            ))
        
            # Update layout
            fig1.update_layout(
                title=f'Kilometers Driven/Persons Served By {level_of_detail}',
                xaxis=dict(tickangle=45),
                yaxis=dict(title='Total Distance Covered', titlefont=dict(color='cyan')),
                yaxis2=dict(title='Total Patients Served', titlefont=dict(color='blue'), overlaying='y', side='right'),
                legend=dict(x=0, y=1.1, traceorder='normal', font=dict(family='sans-serif', size=12), bgcolor='rgba(0,0,0,0)'),
            )
        
            fig2 = go.Figure()
        
            # Add traces for 'Admitted in Hospital' and 'Discharged from Hospital'
            fig2.add_trace(go.Scatter(
                x=Ambulance_By_Month.index,
                y=Ambulance_By_Month['Admitted in Hospital'],
                mode='lines+markers',
                name='Admitted in Hospital',
                line=dict(color='green', width=2)
            ))
        
            fig2.add_trace(go.Scatter(
                x=Ambulance_By_Month.index,
                y=Ambulance_By_Month['Discharged from Hospital'],
                mode='lines+markers',
                name='Discharged from Hospital',
                line=dict(color='red', width=2)
            ))
        
            # Update layout            
            fig2.update_layout(
                title=f'Number of Patients Admitted/Discharged By {level_of_detail}',
                xaxis=dict(tickangle=45),
                yaxis=dict(title='Number Of Patients'),
                legend=dict(x=0, y=1.1, traceorder='normal', font=dict(family='sans-serif', size=12), bgcolor='rgba(0,0,0,0)')
            )
                    
            if (Ambulance_By_Month['Total Distance Covered'].count()==0):
                   return False, Ambulance_By_Month_full, Total_Number_Of_PHC, fig1, fig2, min_date_full, max_date_full, Summary_Total_full
            else:
                   return True, Ambulance_By_Month_full, Total_Number_Of_PHC, fig1, fig2, min_date_full, max_date_full, Summary_Total_full
    
        col1,col2=st.columns([1,1])
        with col1:
            date_range=st.date_input('**Enter date range**',value=(datetime(2020,1,1),date.today()),key='date_range',format='DD/MM/YYYY')
        with col2:
            level_of_detail=st.selectbox('**Select frequency**',['Month','Year'])
    
        (val,summary_df,Total_Number_Of_PHC, fig1, fig2, min_date_full, max_date_full, Summary_Total_full)=get_data_full(date_range,level_of_detail,sheet)
    
        st.write("**WORK IN PROGRESS")
        st.write(f"{summary_df}")
