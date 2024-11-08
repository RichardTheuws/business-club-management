import streamlit as st
import pandas as pd
import io
from utils.database import (
    bulk_import_data,
    validate_import_data,
    verify_data_consistency,
    get_data_templates
)

def data_management():
    st.title("Data Management")
    
    tab1, tab2, tab3 = st.tabs(["Manual Entry", "Bulk Import", "Data Templates"])
    
    with tab1:
        st.subheader("Manual Data Entry")
        
        entry_type = st.selectbox("Select Data Type", ["Members", "Transactions", "Events"])
        
        if entry_type == "Members":
            with st.form("member_entry"):
                name = st.text_input("Member Name")
                email = st.text_input("Email")
                country = st.selectbox("Country", ["Netherlands", "Belgium", "Germany"])
                join_date = st.date_input("Join Date")
                membership_type = st.selectbox("Membership Type", ["Standard", "Premium"])
                active = st.checkbox("Active", value=True)
                
                if st.form_submit_button("Add Member"):
                    data = pd.DataFrame([{
                        'name': name,
                        'email': email,
                        'country': country,
                        'join_date': join_date,
                        'membership_type': membership_type,
                        'active': active
                    }])
                    
                    valid, message = validate_import_data('members', data)
                    if valid:
                        success = bulk_import_data('members', data)
                        if success:
                            st.success("Member added successfully!")
                        else:
                            st.error("Error adding member.")
                    else:
                        st.error(f"Invalid data: {message}")
        
        elif entry_type == "Transactions":
            with st.form("transaction_entry"):
                member_email = st.text_input("Member Email")
                amount = st.number_input("Amount (€)", value=0.0)
                transaction_type = st.selectbox("Type", ["membership_fee", "event_fee"])
                transaction_date = st.date_input("Transaction Date")
                
                if st.form_submit_button("Add Transaction"):
                    data = pd.DataFrame([{
                        'member_email': member_email,
                        'amount': amount,
                        'transaction_type': transaction_type,
                        'transaction_date': transaction_date
                    }])
                    
                    valid, message = validate_import_data('transactions', data)
                    if valid:
                        success = bulk_import_data('transactions', data)
                        if success:
                            st.success("Transaction added successfully!")
                        else:
                            st.error("Error adding transaction.")
                    else:
                        st.error(f"Invalid data: {message}")
        
        else:  # Events
            with st.form("event_entry"):
                name = st.text_input("Event Name")
                date = st.date_input("Event Date")
                country = st.selectbox("Country", ["Netherlands", "Belgium", "Germany"])
                revenue = st.number_input("Revenue (€)", value=0.0)
                costs = st.number_input("Costs (€)", value=0.0)
                
                if st.form_submit_button("Add Event"):
                    data = pd.DataFrame([{
                        'name': name,
                        'date': date,
                        'country': country,
                        'revenue': revenue,
                        'costs': costs
                    }])
                    
                    valid, message = validate_import_data('events', data)
                    if valid:
                        success = bulk_import_data('events', data)
                        if success:
                            st.success("Event added successfully!")
                        else:
                            st.error("Error adding event.")
                    else:
                        st.error(f"Invalid data: {message}")
    
    with tab2:
        st.subheader("Bulk Data Import")
        
        import_type = st.selectbox("Select Import Type", ["Members", "Transactions", "Events"], key="bulk_import")
        
        uploaded_file = st.file_uploader("Upload CSV file", type="csv")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                valid, message = validate_import_data(import_type.lower(), df)
                if valid:
                    if st.button("Import Data"):
                        success = bulk_import_data(import_type.lower(), df)
                        if success:
                            st.success(f"{len(df)} records imported successfully!")
                            
                            # Verify data consistency
                            consistency_issues = verify_data_consistency()
                            if consistency_issues:
                                st.warning("Some consistency issues were found:")
                                for issue in consistency_issues:
                                    st.write(f"- {issue}")
                        else:
                            st.error("Error importing data.")
                else:
                    st.error(f"Invalid data format: {message}")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with tab3:
        st.subheader("Data Import Templates")
        
        template_type = st.selectbox("Select Template Type", ["Members", "Transactions", "Events"])
        
        template_df = get_data_templates(template_type.lower())
        
        st.write(f"Example {template_type} Data Format:")
        st.dataframe(template_df)
        
        csv = template_df.to_csv(index=False)
        st.download_button(
            label=f"Download {template_type} Template",
            data=csv,
            file_name=f"{template_type.lower()}_template.csv",
            mime="text/csv"
        )
        
        st.markdown("""
        ### Data Format Guidelines
        
        #### Members CSV Format:
        - **name**: Full name of the member
        - **email**: Valid email address (unique)
        - **country**: Netherlands, Belgium, or Germany
        - **join_date**: YYYY-MM-DD format
        - **membership_type**: Standard or Premium
        - **active**: true or false
        
        #### Transactions CSV Format:
        - **member_email**: Existing member's email
        - **amount**: Decimal number (e.g., 795.00)
        - **transaction_type**: membership_fee or event_fee
        - **transaction_date**: YYYY-MM-DD format
        
        #### Events CSV Format:
        - **name**: Event name
        - **date**: YYYY-MM-DD format
        - **country**: Netherlands, Belgium, or Germany
        - **revenue**: Decimal number
        - **costs**: Decimal number
        """)

if __name__ == "__main__":
    data_management()
