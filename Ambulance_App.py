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
sheet=client.open_by_url(r'https://docs.google.com/spreadsheets/d/17M6cIpJApxan-h1X9vCILorUlLctMxSSDz1zhJmEo-o/edit?usp=sharing').worksheets()
Districts=[i.title for i in sheet]

def get_data(selected_district,date_range,level_of_detail,sheet):
    start_date=pd.to_datetime(date_range[0])
    end_date=pd.to_datetime(date_range[1])
    level_of_detail=level_of_detail.lower()
    #level_of_detail=f"'{level_of_detail}'"
    a='0'
    if level_of_detail=="month":
        a="%b %Y"
    else:
        a="%Y"
    ambulance_df=pd.DataFrame(sheet[[i.title for i in sheet].index(selected_district)].get_values())
    ambulance_df.columns=ambulance_df.iloc[0]
    ambulance_df=ambulance_df[1:] 
    ambulance_df['Date']=pd.to_datetime(ambulance_df['Date'].replace('',None))
    min_date=ambulance_df['Date'].min().date().strftime('%d-%b-%Y')
    max_date=ambulance_df['Date'].max().date().strftime('%d-%b-%Y')
    ambulance_df=ambulance_df[(ambulance_df['Date']>=start_date) & (ambulance_df['Date']<=end_date)]
    ambulance_df[['Total Distance Covered','Total Patients Served']]=ambulance_df[['Total Distance Covered','Total Patients Served']].replace('','0').fillna(0).astype(int)
    ambulance_df['Day']=ambulance_df['Day'].str.upper()

    Ambulance_By_Day=ambulance_df[ambulance_df['Day'].replace('',None).notnull()][['Total Distance Covered','Total Patients Served','Day']].groupby(by='Day').sum()

    Ambulance_By_Month=ambulance_df[ambulance_df['Date'].notnull()]
    Ambulance_By_Month=Ambulance_By_Month.reset_index(drop=False)
    Ambulance_By_Month['Month']=pd.to_datetime(Ambulance_By_Month['Date']).dt.month.astype(str).str.pad(width=2,side='left',fillchar='0')
    Ambulance_By_Month['Year']=pd.to_datetime(Ambulance_By_Month['Date']).dt.year.astype(str)
    Ambulance_By_Month['Date']=Ambulance_By_Month['Date'].dt.strftime('%b %Y')
    Ambulance_By_Month['Yrmo']=(Ambulance_By_Month['Year']+Ambulance_By_Month['Month']).astype(int)
    Ambulance_By_Month=Ambulance_By_Month.groupby(['Date'])[['Total Distance Covered','Total Patients Served','Yrmo','Year']].agg({'Total Distance Covered':sum,'Total Patients Served':sum,'Yrmo':mean,'Year':mean})
    #Ambulance_By_Month.set_index('Date',inplace=True)
    Ambulance_By_Month=Ambulance_By_Month.sort_values(by='Yrmo')
    Ambulance_By_Month=Ambulance_By_Month[['Total Distance Covered','Total Patients Served']]

    fig=plt.figure()
    
    ax1=fig.add_subplot()
    ax1.bar(Ambulance_By_Month.index,Ambulance_By_Month['Total Distance Covered'],color='cyan',label='Total Distance Covered')
    ax2=ax1.twinx()
    ax2.plot(Ambulance_By_Month.index,Ambulance_By_Month['Total Patients Served'],color='blue',label='Total Patients Served')
    plt.setp(ax1.get_xticklabels(), rotation=90, horizontalalignment='right')
    ax1.set_ylabel('Total Distance Covered')
    ax2.set_ylabel('Total Patients Served')
    plt.title(f'{selected_district} - Ambulance Deployment By Month')
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
    date_range=st.date_input('Enter date range',value=(datetime(2020,1,1),date.today()),key='date_range')
with col3:
    level_of_detail=st.selectbox('Select the level of detail',['Month','Year'])


(val,plt,min_date,max_date)=get_data(selected_district,date_range,level_of_detail,sheet)
if val is True:
    st.pyplot(plt)
else:
    st.write(f"No data to display. Data for '{selected_district}' is present only between '{min_date}' and '{max_date}'")
    


st.sidebar.title("Select page")
page=st.sidebar.radio("",["District level"])
