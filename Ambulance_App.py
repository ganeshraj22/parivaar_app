#!/usr/bin/env python
# coding: utf-8

# In[2]:


import gspread
import pandas as pd
import streamlit as st
from datetime import datetime, date
import matplotlib.pyplot as plt
from statistics import mean
import xlsxwriter
from oauth2client.service_account import ServiceAccountCredentials


scope=['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds=ServiceAccountCredentials.from_json_keyfile_name(r'unique-bonbon-304011-585cc22859d3.json',scope)
client=gspread.authorize(creds)
sheet=client.open_by_url(r'https://docs.google.com/spreadsheets/d/1CfLVfjrmV2K6wMEg6G-q2_Im2uP7sZ2GsVw0ZzmiJ0k/edit?usp=sharing').worksheets()
Districts=[i.title for i in sheet[6:]]

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
      ambulance_df['Eye Camp Patients']=pd.to_numeric(ambulance_df['Eye Camp Patients'])

      #ambulance_df=ambulance_df[(ambulance_df['Date']>=start_date)&(ambulance_df['Date']<=end_date)]
      
      df_reset = ambulance_df[:-1].reset_index(drop=True)
        
      return df_reset,total_distance_index,no_patients_index
    
    
    (ambulance_df1, total_distance_index, no_patients_index)  = preprocess_data(ambulance_df)
    
    #ambulance_df1['Date']=pd.to_datetime(ambulance_df1['Date'].replace('',None))
    Agg_df=ambulance_df[ambulance_df['Date'].notnull()] 
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

    Number_Of_PHC=no_patients_index-total_distance_index-1
    Patients_Pie=ambulance_df1.iloc[:,total_distance_index:no_patients_index-1].sum()
    Disease_Type_Pie=ambulance_df1.iloc[:,no_patients_index+5:no_patients_index+10].sum()

    fig1=plt.figure()    
    ax1=fig1.add_subplot()
    ax1.bar(Ambulance_By_Month.index,Ambulance_By_Month['Total Distance Covered'],color='cyan',label='Total Distance Covered')
    ax2=ax1.twinx()
    ax2.plot(Ambulance_By_Month.index,Ambulance_By_Month['Total Patients Served'],color='blue',label='Total Patients Served')
    plt.setp(ax1.get_xticklabels(), rotation=90, horizontalalignment='right')
    ax1.set_ylabel('Total Distance Covered')
    ax2.set_ylabel('Total Patients Served')
    plt.title(f'{selected_district} - Kilometers Driven/Persons Served By {level_of_detail}')
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1+h2, l1+l2)

    fig2,ax=plt.subplots()
    ax.plot(Ambulance_By_Month.index,Ambulance_By_Month['Admitted in Hospital'],color='green',label='Admitted in Hospital')
    ax.plot(Ambulance_By_Month.index,Ambulance_By_Month['Discharged from Hospital'],color='red',label='Discharged from Hospital')
    plt.setp(ax.get_xticklabels(), rotation=90, horizontalalignment='right')
    ax.set_ylabel('Number Of Patients')
    plt.title(f'{selected_district} - Number of Patients Admitted/Discharged By {level_of_detail}')
    ax.legend()

    fig3,ax3=plt.subplots()
    ax3.pie(Patients_Pie,labels=Patients_Pie.index,autopct='%1.1f%%')
    #fig3.legend(Patients_Pie.index,loc='right')

    plt.figure(figsize=(160,120))
    fig4,ax4=plt.subplots()
    ax4.pie(Disease_Type_Pie,labels=Disease_Type_Pie.index,autopct='%1.1f%%',startangle=100)
    #fig4.legend(Disease_Type_Pie_Pie.index,loc='right')
   
    if (Ambulance_By_Month['Total Distance Covered'].count()==0):
       return False, fig1, fig2, fig3, fig4, min_date, max_date,Number_Of_PHC
    else:
        return True, fig1, fig2, fig3, fig4, min_date, max_date,Number_Of_PHC
        
col1,col2,col3=st.columns([1,1,1])
with col1:
    selected_district=st.selectbox('Select a district',Districts)
with col2:
    date_range=st.date_input('Enter date range',value=(datetime(2020,1,1),date.today()),key='date_range',format='DD/MM/YYYY')
with col3:
    level_of_detail=st.selectbox('Select the level of detail',['Month','Year'])


(val,fig1,fig2,fig3,fig4,min_date,max_date,Number_Of_PHC)=get_data(selected_district,date_range,level_of_detail,sheet)

col1,col2=st.columns([1.15,1])
with col1:
    if val is True:
        st.pyplot(fig1)
    else:
        st.write(f"No data to display. Data for '{selected_district}' is present only between '{min_date}' and '{max_date}'")
with col2:
    if val is True:
        st.pyplot(fig2)
    #else:
        #st.write(f"No data to display. Data for '{selected_district}' is present only between '{min_date}' and '{max_date}'")

col1,col2=st.columns([max((Number_Of_PHC/8),0.9),1])
with col1:
    if val is True:
        st.pyplot(fig3)
    #else:
        #st.write(f"No data to display. Data for '{selected_district}' is present only between '{min_date}' and '{max_date}'")
with col2:
    if val is True:
        st.pyplot(fig4)
    
st.sidebar.title("Select page")
page=st.sidebar.radio("",["District level"])
