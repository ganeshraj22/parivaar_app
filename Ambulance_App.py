# -*- coding: utf-8 -*-
import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

scope=['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds=ServiceAccountCredentials.from_json_keyfile_name(r'unique-bonbon-304011-585cc22859d3.json',scope)

client=gspread.authorize(creds)
sheet=client.open_by_url(r'https://docs.google.com/spreadsheets/d/1sJDmGeanUxdKd-2z_rxgWgTNwgXCd9t28iLtDbwKlkM/edit').sheet1
sheet2=client.open_by_url(r'https://docs.google.com/spreadsheets/d/1sJDmGeanUxdKd-2z_rxgWgTNwgXCd9t28iLtDbwKlkM/edit').sheet1

ambulance_df=pd.DataFrame(sheet.get_all_records())
ambulance_df_2=pd.DataFrame(sheet2.get_all_records())
st.dataframe(ambulance_df)
st.dataframe(ambulance_df_2)
