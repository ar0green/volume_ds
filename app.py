import streamlit as st
import sys
sys.path.append('.')  # Ensure the script can find the memory calculator module
from memory_calculator import DatasetMemoryCalculator

'''
test SQL expression to import
CREATE TABLE customer_orders (
    order_id BIGINT PRIMARY KEY,
    customer_name VARCHAR(100),
    email VARCHAR(255),
    order_date DATETIME,
    total_amount DECIMAL(10, 2),
    is_paid BOOLEAN,
    product_quantity SMALLINT,
    customer_age INT,
    shipping_weight FLOAT,
    order_status VARCHAR(50)
);
'''

def main():
    st.set_page_config(
        page_title="Dataset Memory Size Calculator",
        page_icon="💾",
        layout="wide"
    )

    st.title("📊 Dataset Memory Size Estimator")
    st.markdown("""
    Calculate the estimated memory consumption of your dataset 
    by defining columns and specifying the number of rows.
    """)

    # Initialize session state for columns if not exists
    if 'columns' not in st.session_state:
        st.session_state.columns = []

    # Sidebar for column management
    with st.sidebar:
        st.header("Add Columns")
        
        # Column input fields
        col_name = st.text_input("Column Name")
        data_types = [
            'int8', 'int16', 'int32', 'int64', 
            'float32', 'float64', 'bool', 
            'datetime', 'string'
        ]
        col_type = st.selectbox("Data Type", data_types)
        
        # Optional length for string type
        col_length = None
        if col_type == 'string':
            col_length = st.number_input(
                "Estimated Average String Length", 
                min_value=1, 
                value=50
            )
        
        # Add Column Button
        if st.button("Add Column"):
            if col_name:
                column_details = {
                    'name': col_name, 
                    'type': col_type, 
                    'length': col_length
                }
                st.session_state.columns.append(column_details)
                st.sidebar.success(f"Column '{col_name}' added!")
        
        # SQL Import Section
        st.header("Import from SQL")
        sql_input = st.text_area("Paste CREATE TABLE Statement")
        if st.button("Parse SQL"):
            try:
                calculator = DatasetMemoryCalculator()
                calculator.parse_create_table_sql(sql_input)
                st.session_state.columns = [
                    {'name': col['name'], 'type': col['type'], 'length': col.get('length')} 
                    for col in calculator.columns
                ]
                st.sidebar.success("SQL Parsed Successfully!")
            except Exception as e:
                st.sidebar.error(f"Error parsing SQL: {e}")

    # Main Content Area
    st.header("Defined Columns")
    
    # Display Current Columns
    if st.session_state.columns:
        columns_df = st.dataframe(st.session_state.columns)
        
        # Number of Rows Input
        num_rows = st.number_input(
            "Number of Rows", 
            min_value=1, 
            value=1000,
            help="Estimated number of rows in your dataset"
        )
        
        # Calculate Memory Button
        if st.button("Calculate Memory Consumption"):
            calculator = DatasetMemoryCalculator()
            
            # Add columns to calculator
            for col in st.session_state.columns:
                calculator.add_column(
                    col['name'], 
                    col['type'], 
                    col.get('length')
                )
            
            # Calculate memory
            memory_result = calculator.calculate_total_memory(num_rows)
            
            # Display Results
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Bytes", f"{memory_result['total_bytes']:,.0f}")
            with col2:
                st.metric("Kilobytes", f"{memory_result['total_kb']:,.2f}")
            with col3:
                st.metric("Megabytes", f"{memory_result['total_mb']:,.2f}")
            with col4:
                st.metric("Gigabytes", f"{memory_result['total_gb']:,.2f}")
    else:
        st.info("Add columns using the sidebar to start calculating.")

    # Reset Columns Button
    if st.button("Reset All Columns"):
        # Use clear() instead of setting to empty list
        st.session_state.columns.clear()
        st.rerun()

if __name__ == "__main__":
    main()