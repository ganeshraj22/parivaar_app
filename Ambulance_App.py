#!/usr/bin/env python
# coding: utf-8

# In[2]:


import gspread
import pandas as pd
import streamlit as st
from datetime import datetime, date
import matplotlib.pyplot as plt
from oauth2client.service_account import ServiceAccountCredentials


# In[3]:


scope=['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds=ServiceAccountCredentials.from_json_keyfile_name(r'unique-bonbon-304011-585cc22859d3.json',scope)


# In[4]:


client=gspread.authorize(creds)
sheet=client.open_by_url(r'https://docs.google.com/spreadsheets/d/17M6cIpJApxan-h1X9vCILorUlLctMxSSDz1zhJmEo-o/edit?usp=sharing').worksheets()
Districts=[i.title for i in sheet]
selected_district=st.selectbox('District',Districts)
date_range=st.date_input("Enter the date range",value=(datetime('2020,01,01'),max_date),key='date_range')
ambulance_df=pd.DataFrame(sheet[[i.title for i in sheet].index(selected_district)].get_values())
#Selected_District=sheet[[i.title for i in sheet].index(selected_district)].title

# In[6]:

ambulance_df.columns=ambulance_df.iloc[0]
ambulance_df=ambulance_df[1:]

# In[7]:


ambulance_df[['Total Distance Covered','Total Patients Served']]=ambulance_df[['Total Distance Covered','Total Patients Served']].replace('','0').fillna(0).astype(int)
ambulance_df['Day']=ambulance_df['Day'].str.upper()


# In[8]:


Ambulance_By_Day=ambulance_df[ambulance_df['Day'].replace('',None).notnull()][['Total Distance Covered','Total Patients Served','Day']].groupby(by='Day').sum()


# In[26]:


ambulance_df['Date']=pd.to_datetime(ambulance_df['Date'].replace('',None))


# In[79]:


Ambulance_By_Month=ambulance_df[ambulance_df['Date'].notnull()].groupby(ambulance_df['Date'].dt.strftime('%b %Y'))[['Total Distance Covered','Total Patients Served']].sum()


# In[80]:


Ambulance_By_Month=Ambulance_By_Month.reset_index(drop=False)


# In[81]:


Ambulance_By_Month['Month']=pd.to_datetime(Ambulance_By_Month['Date']).dt.month
Ambulance_By_Month['Year']=pd.to_datetime(Ambulance_By_Month['Date']).dt.year


# In[90]:


Ambulance_By_Month=Ambulance_By_Month.sort_values(['Year','Month'])
Ambulance_By_Month=Ambulance_By_Month[['Date','Total Distance Covered','Total Patients Served']]
Ambulance_By_Month.set_index('Date',inplace=True)

# In[91]:
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
ax1.legend(h1+h2, l1+l2, loc=0)
st.pyplot(plt)

st.sidebar.title("Select page")
page=st.sidebar.radio("",["District level"])




