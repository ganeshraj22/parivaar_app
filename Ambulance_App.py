#!/usr/bin/env python
# coding: utf-8

# In[2]:


import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials


# In[3]:


scope=['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds=ServiceAccountCredentials.from_json_keyfile_name(r'unique-bonbon-304011-585cc22859d3.json',scope)


# In[4]:


client=gspread.authorize(creds)
sheet=client.open_by_url(r'https://docs.google.com/spreadsheets/d/17M6cIpJApxan-h1X9vCILorUlLctMxSSDz1zhJmEo-o/edit?usp=sharing').sheet1


# In[6]:


ambulance_df=pd.DataFrame(sheet.get_all_records())


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
Ambulance_By_Month=Ambulance_By_Month.style.hide(axis="index")


# In[91]:


st.dataframe(Ambulance_By_Month)


# In[ ]:




