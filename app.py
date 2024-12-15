import json
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
import os
from io import BytesIO
import streamlit_authenticator as stauth
from pathlib import Path

# --- Load Environment Variables ---
load_dotenv()

# --- USER AUTHENTICATION ----

# Load hashed passwords from JSON file
file_path = Path(__file__).parent / "hashed_pw.json"  # Use the JSON file instead of pickle

# Ensure the file exists before trying to open it
if not file_path.exists():
    st.error("The file 'hashed_pw.json' does not exist. Please ensure you have generated the password file.")
    st.stop()

# Load hashed passwords from the JSON file
with file_path.open("r") as file:
    credentials_data = json.load(file)

# Prepare the credentials dictionary with email field included
credentials = {
    "usernames": {
        username: {
            "name": details["name"],
            "password": details["password"],
            "email": details["email"]
        }
        for username, details in credentials_data.items()
    }
}

# Instantiate the authenticator object
authenticator = stauth.Authenticate(
    credentials,  # Pass credentials as a dictionary
    cookie_name="sales_dashboard",  # Cookie name for session management
    key="abcdef",  # Secret key for encryption
    cookie_expiry_days=7  # Expiry days for the cookie
)

# --- Perform the login process ---
login_result = authenticator.login('main')

# Check if login_result is None or contains incorrect values
if login_result is None:
    st.warning("Please enter your username and password")
elif login_result == False:
    st.error("Username/Password is incorrect")
else:
    # When login is successful, unpack the values
    name, authentication_status, username = login_result
    if authentication_status:
        # User is authenticated
        authenticator.logout("Logout", location="main")

        # --- Fetch Gemini API key from secrets or environment variables ---
        api_key = st.secrets.get("GEMINI", {}).get("API_KEY") or os.getenv("GEMINI_API_KEY")

        if not api_key:
            st.error("API Key is missing! Please set the GEMINI_API_KEY in Streamlit Secrets or .env file.")
        else:
            # Configure Gemini API
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("models/gemini-1.5-pro-001")

            # --- Main App ---
            st.title("Cheque Information Extraction with Gemini AI")

            st.markdown("""**Upload a cheque image to extract key details.**
            This tool uses AI to extract:
            - Payee Name
            - Bank Name
            - Account Number
            - Date
            - Cheque Number
            - Amount  

            After extraction, download the data as a CSV file.""")

            # File uploader
            uploaded_file = st.file_uploader("Upload a cheque image", type=["jpg", "jpeg", "png"])

            if uploaded_file:
                # Display uploaded image
                st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

                # Load image function
                def load_image(image):
                    try:
                        return Image.open(image)
                    except Exception as e:
                        st.error(f"Error loading image: {e}")
                        return None

                img = load_image(uploaded_file)

                if img:
                    # Define the prompt for Gemini AI
                    prompt = (
                        "Analyze this cheque image and extract the Payee Name, Bank Name, Account Number, "
                        "Date, Cheque Number, and Amount."
                    )

                    # Call Gemini AI
                    try:
                        result = model.generate_content([img, prompt])

                        if result.text:
                            # Display raw extracted text
                            st.subheader("Extracted Information (Text):")
                            st.write(result.text)

                            # Parse extracted text into structured data
                            def parse_extracted_info(extracted_text):
                                fields = {
                                    "Payee Name": None,
                                    "Bank Name": None,
                                    "Account Number": None,
                                    "Cheque Number": None,
                                    "Amount": None,
                                    "Date": None,
                                }
                                lines = extracted_text.split("\n")
                                for line in lines:
                                    for field in fields.keys():
                                        if field in line:
                                            fields[field] = line.split(":")[-1].strip()
                                return fields

                            extracted_info = parse_extracted_info(result.text)

                            # Convert to DataFrame
                            df = pd.DataFrame([extracted_info])

                            # Display structured data
                            st.subheader("Extracted Information (Table):")
                            st.table(df)

                            # CSV download functionality
                            def convert_df_to_csv(df):
                                csv_buffer = BytesIO()
                                df.to_csv(csv_buffer, index=False)
                                csv_buffer.seek(0)
                                return csv_buffer.getvalue()

                            csv_data = convert_df_to_csv(df)

                            # Add download button
                            st.subheader("Download Extracted Information:")
                            st.download_button(
                                label="Download as CSV",
                                data=csv_data,
                                file_name="cheque_extracted_info.csv",
                                mime="text/csv",
                            )

                            # Footer with copyright notice (shown after the CSV download)
                            footer = """
                                <style>
                                    footer {
                                        position: fixed;
                                        bottom: 0;
                                        width: 100%;
                                        background-color: #f1f1f1;
                                        text-align: center;
                                        padding: 10px;
                                        font-size: 12px;
                                        color: #888;
                                    }
                                </style>
                                <div class="footer">
                                    &copy; 2024 Anshuman Tiwari. All rights reserved.
                                </div>
                            """
                            # Inject the footer HTML at the bottom of the page
                            st.markdown(footer, unsafe_allow_html=True)

                        else:
                            st.warning("The AI did not return any content. Please try again.")
                    except Exception as e:
                        st.error(f"Error generating content: {e}")
                else:
                    st.error("Failed to load the image. Please try again.")
            else:
                st.info("Please upload a cheque image to begin the analysis.")
