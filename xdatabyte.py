# XDATABYTE SERIAL NUMBER TEST CYCLE CAPTURING

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import string
from sqlalchemy import create_engine, Column, String, Integer, Float, Date, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
import plotly.express as px


# Database setup
Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True)
    report_date = Column(Date)
    serial_number = Column(String(50), unique=True, nullable=False)
    model = Column(String(50))
    box_type = Column(String(50))
    customer_name = Column(String(100))
    location = Column(String(50))
    in_house = Column(Boolean, default=True)
    is_scrap = Column(Boolean, default=False)
    service_code = Column(String(50))
    storage_days_category = Column(String(20))
    batch_number = Column(String(100))
    ship_date = Column(Date)
    
class Test(Base):
    __tablename__ = 'tests'
    id = Column(Integer, primary_key=True)
    serial_number = Column(String(50))
    model = Column(String(50))
    test_type = Column(String(50))
    test_date = Column(Date)
    test_location = Column(String(50))
    rate = Column(Float)
    tax = Column(Float)
    spare_replacement = Column(String(200))
    notes = Column(String(500))
    is_completed = Column(Boolean, default=False)
    batch_number = Column(String(100))
    
# Initialize database
engine = create_engine('sqlite:///contec_tracks.db')
#engine = create_engine('bsqlite:///contec_tracks.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Helper functions
def generate_batch_number(serial_number, customer_name):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"BATCH-{timestamp}-{serial_number[:4]}-{customer_name[:4].upper()}"

def calculate_storage_days_category(report_date):
    today = datetime.now().date()
    delta = today - report_date
    if delta.days < 30:
        return "Less than 30 days"
    elif 30 <= delta.days < 45:
        return "30 to 45 days"
    elif 45 <= delta.days <= 90:
        return "45 to 90 days"
    else:
        return "Over 90 days"

# Streamlit app
def main():
    # Page configuration
    st.set_page_config(
    page_title="xdatabyte",
    page_icon="🌀",
    layout='wide',
    initial_sidebar_state="auto"
    )
    st.markdown(
    """<style>
        MainMenu{visibility:hidden;}
        footer {visibility: hidden;}
       </style>""", unsafe_allow_html=True)
    #st.markdown("""<style>footer {visibility: hidden;}</style>""", unsafe_allow_html=True)
    #st.set_page_config(page_title="Contec Device Tracking", layout="wide", page_icon="🔧")
    
    # Custom CSS
    st.markdown("""
    <style>
        .main {background-color: #f5f5f5;}
        .stButton>button {background-color: #4CAF50; color: white;}
        .stTextInput>div>div>input {background-color: #f9f9f9;}
        .stDateInput>div>div>input {background-color: #f9f9f9;}
        .stSelectbox>div>div>select {background-color: #f9f9f9;}
        .header {color: #2c3e50; font-weight: bold;}
        .subheader {color: #3498db;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(
            '<p style="font-family:sans-serif;text-align:center; color:#3035cf; font-size: 30px;">🧿 XDATABYTE DEVICE SERIAL HISTORY 🧿</p>',
            unsafe_allow_html=True
        )
    # st.title(" Contec Device-Test-Cycle Data")
    st.markdown("---")
    
    # Sidebar navigation
    menu = ["Device Registration", "Testing Management", "Batch Processing", "Reports & Analytics"]
    choice = st.sidebar.selectbox("Navigation", menu)
    
    # Device Registration
    if choice == "Device Registration":
        st.markdown("#### 📝 Device Serial Number Registration")
        
        with st.expander("Register New Device", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                report_date = st.date_input("Report Date", datetime.now())
                serial_number = st.text_input("Device Serial Number*", max_chars=50)
                model = st.text_input("Model*", max_chars=50)
                box_type = st.selectbox("Device Type", ["Select","Modem", "Set-top box", "Remote-Control", "TV", "Hard-disc"])
            with col2:
                customer_name = st.text_input("Customer Name*", max_chars=100)
                location = st.selectbox("Location", ["Select","Charlotte", "Sanjose", "Brownsville", "Other"])
                in_house = st.checkbox("In-House (Warehouse Storage)", value=True)
            
            if st.button("Register Device"):
                if not serial_number or not model or not customer_name:
                    st.error("Please fill all required fields (marked with *)")
                else:
                    # Check if serial number already exists
                    existing_report_date = session.query(Device).filter_by(report_date=report_date).first()
                    if existing_report_date:
                        st.error(f"Device with report_date {report_date} already exists!")
                    else:
                        # Create new device
                        new_device = Device(
                            report_date=report_date,
                            serial_number=serial_number,
                            model=model,
                            box_type=box_type,
                            customer_name=customer_name,
                            location=location,
                            in_house=in_house,
                            storage_days_category=calculate_storage_days_category(report_date)
                        )
                        session.add(new_device)
                        session.commit()
                        st.success(f"report_date {report_date} registered successfully!")
        
        st.subheader("Registered Devices")
        devices = session.query(Device).all()
        if devices:
            devices_data = [{
                "Report Date": device.report_date.strftime('%Y-%m-%d') if device.report_date else "",
                "Serial Number": device.serial_number,
                "Model": device.model,
                "Device Type": device.box_type,
                "Customer": device.customer_name,
                "Location": device.location,
                "In-House": "Yes" if device.in_house else "No",
                "Batch Number": device.batch_number if device.batch_number else "Not assigned",
                "Status": "Scrap" if device.is_scrap else "Active"
            } for device in devices]
            
            df_devices = pd.DataFrame(devices_data)
            
            gb = GridOptionsBuilder.from_dataframe(df_devices)
            gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
            gb.configure_selection('single', use_checkbox=True)
            gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=False)
            grid_options = gb.build()
            
            grid_response = AgGrid(
                df_devices,
                gridOptions=grid_options,
                height=400,
                width='100%',
                data_return_mode='FILTERED_AND_SORTED',
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                fit_columns_on_grid_load=True,
                theme='streamlit'
            )
        else:
            st.info("No devices registered yet.")
    
    # Testing Management
    elif choice == "Testing Management":
        st.header("🧪 Testing Management")
        
        tab1, tab2 = st.tabs(["Add New Test", "View/Edit Tests"])
        
        with tab1:
            st.subheader("Add New Test")
            
            # Get all registered devices
            devices = session.query(Device).filter(Device.is_scrap == False).all()
            device_choices = {f"{d.serial_number} - {d.model} - {d.customer_name}": d.serial_number for d in devices}
            
            if not devices:
                st.warning("No active devices available for testing. Please register devices first.")
            else:
                selected_device_key = st.selectbox("Select Device", options=list(device_choices.keys()))
                serial_number = device_choices[selected_device_key]
                
                device = session.query(Device).filter_by(serial_number=serial_number).first()
                
                col1, col2 = st.columns(2)
                with col1:
                    test_date = st.date_input("Test Date", datetime.now())
                    test_type = st.selectbox("Test Type", [
                        "SQT", "SUMT", "SCL", "SCOSLAB", "SCOSCLEAN", "SPRETS", 
                        "SPPOSTTS", "SPOERUP", "SCOMPLETE", "SSCAN", "SPRO", 
                        "SFAILCOS", "SFAILTEST", "SDETSCAN", "SKIT", "SPACK", 
                        "SSTORE", "SSHIP"
                    ])
                    test_location = st.selectbox("Test Location", ["Charlotte", "Sanjose", "Brownsville"])
                with col2:
                    rate = st.number_input("Rate ($)", min_value=0.0, format="%.2f")
                    tax = st.number_input("Tax ($)", min_value=0.0, format="%.2f", value=0.0)
                    spare_replacement = st.text_area("Spare Replacement (BOM if required)", height=70)
                
                notes = st.text_area("Test Notes")
                
                if st.button("Submit Test"):
                    new_test = Test(
                        serial_number=serial_number,
                        model=device.model,
                        test_type=test_type,
                        test_date=test_date,
                        test_location=test_location,
                        rate=rate,
                        tax=tax,
                        spare_replacement=spare_replacement,
                        notes=notes
                    )
                    session.add(new_test)
                    session.commit()
                    st.success("Test record added successfully!")
        
        with tab2:
            st.subheader("Test Records")
            
            # Get all tests
            tests = session.query(Test).all()
            if tests:
                tests_data = [{
                    "Test Date": test.test_date.strftime('%Y-%m-%d') if test.test_date else "",
                    "Serial Number": test.serial_number,
                    "Model": test.model,
                    "Test Type": test.test_type,
                    "Location": test.test_location,
                    "Rate": f"${test.rate:.2f}",
                    "Tax": f"${test.tax:.2f}",
                    "Spare Parts": test.spare_replacement,
                    "Completed": "Yes" if test.is_completed else "No",
                    "Batch Number": test.batch_number if test.batch_number else "Not assigned"
                } for test in tests]
                
                df_tests = pd.DataFrame(tests_data)
                
                gb = GridOptionsBuilder.from_dataframe(df_tests)
                gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
                gb.configure_selection('single', use_checkbox=True)
                gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=False)
                grid_options = gb.build()
                
                grid_response = AgGrid(
                    df_tests,
                    gridOptions=grid_options,
                    height=400,
                    width='100%',
                    data_return_mode='FILTERED_AND_SORTED',
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    fit_columns_on_grid_load=True,
                    theme='streamlit'
                )
            else:
                st.info("No test records available.")
    
    # Batch Processing
    elif choice == "Batch Processing":
        st.header("📦 Batch Processing")
        
        tab1, tab2 = st.tabs(["Create Batch", "Ship Devices"])
        
        with tab1:
            st.subheader("Create Batch for Completed Tests")
            
            # Get devices with completed tests but no batch number
            devices_with_tests = session.query(Device).filter(
                Device.batch_number == None,
                Device.is_scrap == False
            ).all()
            
            if not devices_with_tests:
                st.info("No devices available for batch creation.")
            else:
                device_list = [f"{d.serial_number} - {d.model} - {d.customer_name}" for d in devices_with_tests]
                selected_device = st.selectbox("Select Device", device_list)
                serial_number = selected_device.split(" - ")[0]
                
                # Get all tests for this device
                tests = session.query(Test).filter_by(serial_number=serial_number, is_completed=False).all()
                
                if not tests:
                    st.info("No pending tests for this device.")
                else:
                    st.markdown(f"**Pending Tests for {serial_number}**")
                    for test in tests:
                        st.write(f"- {test.test_type} (Rate: ${test.rate:.2f}, Tax: ${test.tax:.2f})")
                    
                    if st.button(f"Mark Tests as Completed and Create Batch for {serial_number}"):
                        device = session.query(Device).filter_by(serial_number=serial_number).first()
                        batch_number = generate_batch_number(serial_number, device.customer_name)
                        
                        # Update device with batch number
                        device.batch_number = batch_number
                        
                        # Update all tests for this device
                        for test in tests:
                            test.is_completed = True
                            test.batch_number = batch_number
                        
                        session.commit()
                        st.success(f"Batch {batch_number} created successfully for device {serial_number}!")
        
        with tab2:
            st.subheader("Ship Devices")
            
            # Get devices with batch numbers but not shipped
            devices_to_ship = session.query(Device).filter(
                Device.batch_number != None,
                Device.ship_date == None,
                Device.is_scrap == False
            ).all()
            
            if not devices_to_ship:
                st.info("No devices available for shipping.")
            else:
                device_list = [f"{d.serial_number} - {d.model} - Batch: {d.batch_number}" for d in devices_to_ship]
                selected_device = st.selectbox("Select Device to Ship", device_list)
                serial_number = selected_device.split(" - ")[0]
                
                ship_date = st.date_input("Shipping Date", datetime.now())
                
                if st.button(f"Mark Device {serial_number} as Shipped"):
                    device = session.query(Device).filter_by(serial_number=serial_number).first()
                    device.ship_date = ship_date
                    session.commit()
                    st.success(f"Device {serial_number} shipped on {ship_date.strftime('%Y-%m-%d')}!")
    
    # Reports & Analytics
    elif choice == "Reports & Analytics":
        st.header("📊 Reports & Analytics")
        
        tab1, tab2, tab3 = st.tabs(["Device Statistics", "Test Statistics", "Financial Summary"])
        
        with tab1:
            st.subheader("Device Statistics")
            
            # Get all devices
            devices = session.query(Device).all()
            
            if devices:
                df_devices = pd.DataFrame([{
                    "Serial Number": d.serial_number,
                    "Model": d.model,
                    "Customer": d.customer_name,
                    "Location": d.location,
                    "Status": "Scrap" if d.is_scrap else ("Shipped" if d.ship_date else "In Process"),
                    "Days in System": (datetime.now().date() - d.report_date).days if d.report_date else 0,
                    "Batch Number": d.batch_number if d.batch_number else "Not assigned"
                } for d in devices])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Devices by Model**")
                    model_counts = df_devices['Model'].value_counts().reset_index()
                    model_counts.columns = ['Model', 'Count']
                    fig1 = px.bar(model_counts, x='Model', y='Count', color='Model')
                    st.plotly_chart(fig1, use_container_width=True)
                    
                    st.markdown("**Devices by Status**")
                    status_counts = df_devices['Status'].value_counts().reset_index()
                    status_counts.columns = ['Status', 'Count']
                    fig2 = px.pie(status_counts, values='Count', names='Status')
                    st.plotly_chart(fig2, use_container_width=True)
                
                with col2:
                    st.markdown("**Devices by Customer**")
                    customer_counts = df_devices['Customer'].value_counts().reset_index()
                    customer_counts.columns = ['Customer', 'Count']
                    fig3 = px.bar(customer_counts, x='Customer', y='Count', color='Customer')
                    st.plotly_chart(fig3, use_container_width=True)
                    
                    st.markdown("**Days in System Distribution**")
                    fig4 = px.histogram(df_devices, x='Days in System', nbins=20)
                    st.plotly_chart(fig4, use_container_width=True)
                
                st.markdown("**Detailed Device Data**")
                st.dataframe(df_devices)
            else:
                st.info("No device data available for analysis.")
        
        with tab2:
            st.subheader("Test Statistics")
            
            # Get all tests
            tests = session.query(Test).all()
            
            if tests:
                df_tests = pd.DataFrame([{
                    "Test Type": t.test_type,
                    "Model": t.model,
                    "Location": t.test_location,
                    "Rate": t.rate,
                    "Completed": "Yes" if t.is_completed else "No",
                    "Batch Number": t.batch_number if t.batch_number else "Not assigned"
                } for t in tests])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Tests by Type**")
                    test_counts = df_tests['Test Type'].value_counts().reset_index()
                    test_counts.columns = ['Test Type', 'Count']
                    fig1 = px.bar(test_counts, x='Test Type', y='Count', color='Test Type')
                    st.plotly_chart(fig1, use_container_width=True)
                    
                    st.markdown("**Test Completion Status**")
                    completion_counts = df_tests['Completed'].value_counts().reset_index()
                    completion_counts.columns = ['Completed', 'Count']
                    fig2 = px.pie(completion_counts, values='Count', names='Completed')
                    st.plotly_chart(fig2, use_container_width=True)
                
                with col2:
                    st.markdown("**Tests by Model**")
                    model_test_counts = df_tests.groupby(['Model', 'Test Type']).size().reset_index(name='Count')
                    fig3 = px.bar(model_test_counts, x='Model', y='Count', color='Test Type', barmode='stack')
                    st.plotly_chart(fig3, use_container_width=True)
                    
                    st.markdown("**Average Rate by Test Type**")
                    avg_rates = df_tests.groupby('Test Type')['Rate'].mean().reset_index()
                    fig4 = px.bar(avg_rates, x='Test Type', y='Rate', color='Test Type')
                    st.plotly_chart(fig4, use_container_width=True)
                
                st.markdown("**Detailed Test Data**")
                st.dataframe(df_tests)
            else:
                st.info("No test data available for analysis.")
        
        with tab3:
            st.subheader("Financial Summary")
            
            # Get completed tests with rates
            tests = session.query(Test).filter(Test.is_completed == True).all()
            
            if tests:
                df_financial = pd.DataFrame([{
                    "Batch Number": t.batch_number,
                    "Test Type": t.test_type,
                    "Model": t.model,
                    "Rate": t.rate,
                    "Tax": t.tax,
                    "Total": t.rate + t.tax
                } for t in tests])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Revenue by Test Type**")
                    revenue_by_test = df_financial.groupby('Test Type')['Total'].sum().reset_index()
                    fig1 = px.bar(revenue_by_test, x='Test Type', y='Total', color='Test Type')
                    st.plotly_chart(fig1, use_container_width=True)
                    
                    st.markdown("**Total Revenue by Model**")
                    revenue_by_model = df_financial.groupby('Model')['Total'].sum().reset_index()
                    fig2 = px.pie(revenue_by_model, values='Total', names='Model')
                    st.plotly_chart(fig2, use_container_width=True)
                
                with col2:
                    st.markdown("**Revenue by Batch**")
                    revenue_by_batch = df_financial.groupby('Batch Number')['Total'].sum().reset_index()
                    fig3 = px.bar(revenue_by_batch, x='Batch Number', y='Total', color='Batch Number')
                    st.plotly_chart(fig3, use_container_width=True)
                    
                    st.markdown("**Tax vs Rate Comparison**")
                    fig4 = px.scatter(df_financial, x='Rate', y='Tax', color='Test Type', size='Total')
                    st.plotly_chart(fig4, use_container_width=True)
                
                total_revenue = df_financial['Total'].sum()
                avg_rate = df_financial['Rate'].mean()
                total_tax = df_financial['Tax'].sum()
                
                st.metric("Total Revenue", f"${total_revenue:,.2f}")
                st.metric("Average Test Rate", f"${avg_rate:,.2f}")
                st.metric("Total Tax Collected", f"${total_tax:,.2f}")
                
                st.markdown("**Detailed Financial Data**")
                st.dataframe(df_financial)
            else:
                st.info("No financial data available for completed tests.")

if __name__ == "__main__":
    main()
