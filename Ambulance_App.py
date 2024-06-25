#!/usr/bin/env python
# coding: utf-8

# In[2]:


import gspread
import pandas as pd
import streamlit as st
from datetime import datetime, date
import matplotlib.pyplot as plt
from statistics import mean
from oauth2client.service_account import ServiceAccountCredentials


scope=['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds=ServiceAccountCredentials.from_json_keyfile_name(r'unique-bonbon-304011-585cc22859d3.json',scope)
client=gspread.authorize(creds)
sheet=client.open_by_url(r'https://docs.google.com/spreadsheets/d/1CfLVfjrmV2K6wMEg6G-q2_Im2uP7sZ2GsVw0ZzmiJ0k/edit?usp=sharing').worksheets()
Districts=[i.title for i in sheet]

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
    
      ambulance_df.iloc[:, total_distance_index+1:no_patients_index] = ambulance_df.iloc[:, 3:total_distance_index].values
    
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
    
      ambulance_df.rename(columns={ambulance_df.iloc[:,[no_patients_index-1,total_distance_index-1]].columns[0]:'Total Patients Served',
                                  ambulance_df.iloc[:,[no_patients_index-1,total_distance_index-1]].columns[1]:'Total Distance Covered(KM)'},inplace=True)
    
      ambulance_df.replace('-', '0', inplace=True)
      ambulance_df.replace('--', '0', inplace=True)
      ambulance_df.replace('', 0, inplace=True)
      ambulance_df.fillna(0, inplace=True)
    
      columns_to_check = ambulance_df.columns[2:no_patients_index]
      print(columns_to_check)
    
      # Check for 0 values in specified columns range
      mask = ambulance_df[columns_to_check].eq(0).all(axis=1)
    
      # Filter out rows where NaN values exist in specified columns range
      ambulance_df = ambulance_df[~mask]
    
      ambulance_df['Date']=ambulance_df['Date'].apply(convert_to_datetime)
      ambulance_df = ambulance_df[ambulance_df['Date'].notnull()]
      # ambulance_df['Total Distance Covered']=pd.to_numeric(ambulance_df['Total Distance Covered(KM)'])
      # ambulance_df['Total Patients Served']=pd.to_numeric(ambulance_df['Total Patients Served'])
    
      return ambulance_df[3:], total_distance_index, no_patients_index
    
    
    (ambulance_df1, total_distance_index, no_patients_index)  = preprocess_data(ambulance_df)
    
    ambulance_df1['Date']=pd.to_datetime(ambulance_df1['Date'].replace('',None))
    min_date=ambulance_df1['Date'].min().date().strftime('%d-%b-%Y')
    max_date=ambulance_df1['Date'].max().date().strftime('%d-%b-%Y')
    ambulance_df1['Total Distance Covered']=pd.to_numeric(ambulance_df1['Total Distance Covered'])
		ambulance_df1['Total Patients Served']=pd.to_numeric(ambulance_df1['Total Patients Served'])
		        
		Ambulance_By_Month=ambulance_df1[ambulance_df1['Date'].notnull()]
		Ambulance_By_Month=Ambulance_By_Month.reset_index(drop=False)
		Ambulance_By_Month['Month']=pd.to_datetime(Ambulance_By_Month['Date']).dt.month.astype(str).str.pad(width=2,side='left',fillchar='0')
		Ambulance_By_Month['Year']=pd.to_datetime(Ambulance_By_Month['Date']).dt.year.astype(str)
		Ambulance_By_Month['Date']=Ambulance_By_Month['Date'].dt.strftime('%b %Y')
		Ambulance_By_Month['Yrmo']=(Ambulance_By_Month['Year']+Ambulance_By_Month['Month']).astype(int)
		Ambulance_By_Month['Year']=Ambulance_By_Month['Year'].astype(int)
		Ambulance_By_Month=Ambulance_By_Month.groupby(['Date'])[['Total Distance Covered','Total Patients Served','Yrmo','Year']].agg({'Total Distance Covered':sum,'Total Patients Served':sum,'Yrmo':mean,'Year':mean})
		#Ambulance_By_Month.set_index('Date',inplace=True)
		Ambulance_By_Month=Ambulance_By_Month.sort_values(by='Yrmo')
		Ambulance_By_Month=Ambulance_By_Month[['Total Distance Covered','Total Patients Served','Yrmo','Year']]
		
		fig=plt.figure()
		    
		ax1=fig.add_subplot()
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
		if (Ambulance_By_Month['Total Distance Covered'].count()==0):
		   return False, plt, min_date, max_date
		else:
		    return True, plt, min_date, max_date
        
col1,col2,col3=st.columns([1,1,1])
with col1:
    selected_district=st.selectbox('Select a district',Districts)
with col2:
    date_range=st.date_input('Enter date range',value=(datetime(2020,1,1),date.today()),key='date_range',format='DD/MM/YYYY')
with col3:
    level_of_detail=st.selectbox('Select the level of detail',['Month','Year'])


(val,plt,min_date,max_date)=get_data(selected_district,date_range,level_of_detail,sheet)
col1,col2=st.columns([1,1])
with col1:
    if val is True:
        st.pyplot(plt)
    else:
        st.write(f"No data to display. Data for '{selected_district}' is present only between '{min_date}' and '{max_date}'")
with col2:
    st.write(f"Some chart/data to be added here")

col1,col2=st.columns([1,1])
with col1:
    st.write(f"Some chart/data to be added here")
with col2:
    st.write(f"Some chart/data to be added here")
    
st.sidebar.title("Select page")
page=st.sidebar.radio("",["District level"])
