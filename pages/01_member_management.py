import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import get_db_connection
from models.member import add_member, get_members_by_country

def member_management():
    st.title("Member Management")
    
    # Member Addition Form
    st.subheader("Add New Member")
    with st.form("new_member_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Member Name")
            email = st.text_input("Email")
            country = st.selectbox("Country", ["Netherlands", "Belgium", "Germany"])
            
        with col2:
            join_date = st.date_input("Join Date")
            membership_type = st.selectbox("Membership Type", ["Standard", "Premium"])
            
        if st.form_submit_button("Add Member"):
            add_member(name, email, country, join_date, membership_type)
            st.success("Member added successfully!")
    
    # Member Overview
    st.subheader("Member Overview")
    
    tab1, tab2, tab3 = st.tabs(["Netherlands", "Belgium", "Germany"])
    
    with tab1:
        nl_members = get_members_by_country("Netherlands")
        if not nl_members.empty:
            st.dataframe(nl_members)
            
        # Growth Chart
        fig = px.line(nl_members.groupby('join_date').size().reset_index(),
                     x='join_date', y=0, title="Member Growth - Netherlands")
        st.plotly_chart(fig)
    
    with tab2:
        be_members = get_members_by_country("Belgium")
        if not be_members.empty:
            st.dataframe(be_members)
            
        # Growth Chart
        fig = px.line(be_members.groupby('join_date').size().reset_index(),
                     x='join_date', y=0, title="Member Growth - Belgium")
        st.plotly_chart(fig)
    
    with tab3:
        de_members = get_members_by_country("Germany")
        if not de_members.empty:
            st.dataframe(de_members)
            
        # Growth Chart
        fig = px.line(de_members.groupby('join_date').size().reset_index(),
                     x='join_date', y=0, title="Member Growth - Germany")
        st.plotly_chart(fig)

if __name__ == "__main__":
    member_management()
