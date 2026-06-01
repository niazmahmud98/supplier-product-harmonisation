# Import Streamlit library for building the web dashboard
import streamlit as st

def main():
    # Set the browser tab title and configure the layout to use full screen width
    st.set_page_config(page_title="Product Harmonisation Dashboard", layout="wide") 

    # Display the main dashboard title at the top of the page
    st.title("Supplier Product Harmonisation System")
    st.subheader("Welcome to the Customer Catalog Dashboard")
    
    st.info("Status: Frontend environment is successfully configured!")
    
   # Create a sidebar panel on the left
    st.sidebar.header("Navigation")
    st.sidebar.success("Phase 1 Local Setup: Done")
    
# Security guard to ensure the main function runs only when this file is executed directly
if __name__ == "__main__":
    main()