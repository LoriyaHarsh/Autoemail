import streamlit as st
import pandas as pd
import base64
import os
import json
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import re
import datetime
import io
from PIL import Image
import uuid

# Set page configuration
st.set_page_config(
    page_title="Email Sender App",
    page_icon="📧",
    layout="wide",
)

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']

# Path for storing credentials
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Add custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success {
        background-color: #d4edda;
        color: #155724;
    }
    .error {
        background-color: #f8d7da;
        color: #721c24;
    }
    .info {
        background-color: #e2f0fd;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

def get_gmail_service():
    """Get authenticated Gmail API service."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_info(
            json.loads(open(TOKEN_FILE).read()), SCOPES)
    
    # If credentials don't exist or are invalid, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                st.error("Missing credentials.json file. Please create it first.")
                st.stop()
                
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    # Return Gmail API service
    return build('gmail', 'v1', credentials=creds)

def create_message(sender, to, subject, message_text, is_html=False, attachments=None):
    """Create a message for an email with optional attachments."""
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    if is_html:
        message.attach(MIMEText(message_text, 'html'))
    else:
        message.attach(MIMEText(message_text, 'plain'))
    
    # Add attachments if any
    if attachments:
        for attachment in attachments:
            attach_name = attachment.name
            content_type = attachment.type
            file_data = attachment.getvalue()
            
            part = MIMEApplication(file_data)
            part.add_header('Content-Disposition', 'attachment', filename=attach_name)
            message.attach(part)
        
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

def send_message(service, user_id, message):
    """Send an email message."""
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        return True, message['id']
    except Exception as e:
        return False, str(e)

def parse_file(uploaded_file):
    """Parse the uploaded file (CSV or Excel) into a pandas DataFrame."""
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:
        st.error("Unsupported file format. Please upload a CSV or Excel file.")
        return None
    
    # Check if 'Email' column exists
    if 'Email' not in df.columns and 'email' not in df.columns:
        st.error("The file must contain an 'Email' column.")
        return None
    
    # Standardize column names
    df.columns = [col.lower() for col in df.columns]
    
    return df

def replace_placeholders(text, row):
    """Replace placeholders in the text with values from the row."""
    pattern = r'\{\{(.*?)\}\}'
    
    def replace(match):
        field = match.group(1).strip().lower()
        if field in row:
            return str(row[field])
        return match.group(0)
    
    return re.sub(pattern, replace, text)

def main():
    st.title("📧 Email Sender App")
    
    # Authentication state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = os.path.exists(TOKEN_FILE)
    
    # User data state
    if 'user_email' not in st.session_state:
        st.session_state.user_email = ""
    
    # Sidebar for authentication
    with st.sidebar:
        st.header("Authentication")
        
        if st.session_state.authenticated:
            st.success(f"Authenticated as: {st.session_state.user_email}")
            if st.button("Logout"):
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                st.session_state.authenticated = False
                st.session_state.user_email = ""
                st.rerun()
        else:
            st.warning("Not authenticated")
            if st.button("Login with Google"):
                try:
                    service = get_gmail_service()
                    # Get user email
                    user_info = service.users().getProfile(userId='me').execute()
                    st.session_state.user_email = user_info['emailAddress']
                    st.session_state.authenticated = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Authentication failed: {str(e)}")
    
    # Main content
    if not st.session_state.authenticated:
        st.info("Please login with your Google account to use this app.")
    else:
        tabs = st.tabs(["Upload Data", "Configure Email", "Send & Results"])
        
        # Tab 1: Upload Data
        with tabs[0]:
            st.header("Step 1: Upload Your Data")
            
            uploaded_file = st.file_uploader("Upload CSV or Excel file", type=['csv', 'xlsx', 'xls'])
            
            if uploaded_file is not None:
                df = parse_file(uploaded_file)
                
                if df is not None:
                    st.session_state.df = df
                    st.success(f"Successfully loaded file with {len(df)} records.")
                    
                    # Preview the data
                    st.subheader("Data Preview")
                    st.dataframe(df.head(5))
                    
                    # Show available fields for personalization
                    st.subheader("Available Fields for Personalization")
                    st.info("You can use these fields in your email template with {{field_name}} syntax")
                    st.write(", ".join([f"{{{{**{col}**}}}}" for col in df.columns]))
        
        # Tab 2: Configure Email
        with tabs[1]:
            st.header("Step 2: Configure Your Email")
            
            if 'df' not in st.session_state:
                st.info("Please upload a data file first.")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    email_type = st.radio(
                        "Email Content Type",
                        ["Static (Same for all recipients)", "Personalized (Using template tags)"]
                    )
                
                with col2:
                    sender_name = st.text_input("Sender Name (optional)")
                    if sender_name:
                        sender = f"{sender_name} <{st.session_state.user_email}>"
                    else:
                        sender = st.session_state.user_email
                    
                    st.write(f"From: {sender}")
                
                subject = st.text_input("Email Subject", "Your Subject Here")
                
                st.subheader("Email Content")
                
                # Add rich text editor toggle
                use_rich_editor = st.checkbox("Use Rich Text Editor", value=True)
                
                if use_rich_editor:
                    # Create HTML template with rich text editor
                    rich_editor_html = """
                    <div style="border: 1px solid #ccc; padding: 5px; margin-bottom: 10px;">
                        <button type="button" onclick="document.execCommand('bold');" style="margin: 2px;">Bold</button>
                        <button type="button" onclick="document.execCommand('italic');" style="margin: 2px;">Italic</button>
                        <button type="button" onclick="document.execCommand('underline');" style="margin: 2px;">Underline</button>
                        <button type="button" onclick="document.execCommand('formatBlock', false, 'h2');" style="margin: 2px;">H2</button>
                        <button type="button" onclick="document.execCommand('formatBlock', false, 'h3');" style="margin: 2px;">H3</button>
                        <button type="button" onclick="document.execCommand('formatBlock', false, 'p');" style="margin: 2px;">P</button>
                        <button type="button" onclick="document.execCommand('insertUnorderedList');" style="margin: 2px;">List</button>
                        <select onchange="document.execCommand('fontName', false, this.value); this.selectedIndex=0;">
                            <option value="">Font</option>
                            <option value="Arial">Arial</option>
                            <option value="Helvetica">Helvetica</option>
                            <option value="Times New Roman">Times New Roman</option>
                            <option value="Courier New">Courier New</option>
                        </select>
                        <select onchange="document.execCommand('fontSize', false, this.value); this.selectedIndex=0;">
                            <option value="">Size</option>
                            <option value="1">Small</option>
                            <option value="3">Normal</option>
                            <option value="5">Large</option>
                            <option value="7">X-Large</option>
                        </select>
                        <input type="color" onchange="document.execCommand('foreColor', false, this.value);" style="margin: 2px;">
                        <button type="button" onclick="document.execCommand('insertHTML', false, '{{name}}');" style="margin: 2px;">Insert {{name}}</button>
                        <button type="button" onclick="document.execCommand('insertHTML', false, '{{email}}');" style="margin: 2px;">Insert {{email}}</button>
                    </div>
                    <div id="editor" contenteditable="true" style="border: 1px solid #ccc; min-height: 200px; padding: 10px; margin-bottom: 10px;">
                    Dear {{name}},<br><br>This is a test email.<br><br>Best regards,<br>Your Name
                    </div>
                    <script>
                        const editor = document.getElementById('editor');
                        editor.addEventListener('input', function() {
                            const event = new CustomEvent('content-changed', { detail: editor.innerHTML });
                            window.parent.document.dispatchEvent(event);
                        });
                        
                        // Function to set content from Python
                        function setContent(content) {
                            editor.innerHTML = content;
                        }
                    </script>
                    """
                    
                    # Create a unique key for this component
                    editor_key = "rich_editor_" + str(uuid.uuid4())
                    
                    # Display the editor (without the key parameter which causes issues in older Streamlit versions)
                    st.components.v1.html(rich_editor_html, height=300)
                    
                    # Hidden field to store the HTML content
                    if 'email_html_content' not in st.session_state:
                        st.session_state.email_html_content = "Dear {{name}},<br><br>This is a test email.<br><br>Best regards,<br>Your Name"
                    
                    email_content = st.text_area("HTML Source (Advanced)", st.session_state.email_html_content, height=150)
                    st.session_state.email_html_content = email_content
                    is_html = True
                else:
                    email_content = st.text_area(
                        "Email Body (You can use {{field_name}} for personalization)",
                        "Dear {{name}},\n\nThis is a test email.\n\nBest regards,\nYour Name",
                        height=200
                    )
                    is_html = False
                
                # File attachments
                st.subheader("Attachments")
                uploaded_files = st.file_uploader("Add attachments", type=['pdf', 'docx', 'xlsx', 'jpg', 'png', 'txt'], accept_multiple_files=True)
                
                if uploaded_files:
                    st.info(f"Added {len(uploaded_files)} attachment(s)")
                    for file in uploaded_files:
                        st.write(f"- {file.name} ({file.size} bytes)")
                
                if email_type == "Personalized (Using template tags)" and st.session_state.df is not None:
                    st.subheader("Preview with first recipient")
                    try:
                        first_row = st.session_state.df.iloc[0].to_dict()
                        preview_subject = replace_placeholders(subject, first_row)
                        preview_content = replace_placeholders(email_content, first_row)
                        
                        st.text_input("Preview Subject", preview_subject, disabled=True)
                        
                        if is_html:
                            st.markdown("**Preview Content (HTML):**")
                            st.components.v1.html(preview_content, height=200)
                        else:
                            st.text_area("Preview Content", preview_content, height=200, disabled=True)
                    except Exception as e:
                        st.error(f"Preview error: {str(e)}")
                
                st.session_state.email_config = {
                    "sender": sender,
                    "subject": subject,
                    "content": email_content,
                    "type": email_type,
                    "is_html": is_html,
                    "attachments": uploaded_files if uploaded_files else None
                }
        
        # Tab 3: Send & Results
        with tabs[2]:
            st.header("Step 3: Send Emails")
            
            if 'df' not in st.session_state or 'email_config' not in st.session_state:
                st.info("Please complete the previous steps first.")
            else:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.metric("Recipients", len(st.session_state.df))
                
                with col2:
                    delay = st.number_input("Delay between emails (seconds)", min_value=0, value=1)
                
                with col3:
                    test_mode = st.checkbox("Test Mode (send to yourself)", value=True)
                
                if st.button("Send Emails"):
                    config = st.session_state.email_config
                    df = st.session_state.df
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_placeholder = st.empty()
                    results_placeholder = st.empty()
                    
                    # Results tracking
                    results = []
                    
                    try:
                        # Get Gmail service
                        service = get_gmail_service()
                        
                        # Send emails
                        for i, (_, row) in enumerate(df.iterrows()):
                            row_dict = row.to_dict()
                            
                            # Get recipient email
                            recipient = row_dict.get('email', '')
                            if not recipient or not isinstance(recipient, str) or '@' not in recipient:
                                results.append({
                                    "recipient": recipient,
                                    "status": "Failed",
                                    "error": "Invalid email address",
                                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                                continue
                            
                            # In test mode, send to the user's email instead
                            if test_mode:
                                actual_recipient = st.session_state.user_email
                                status_placeholder.info(f"TEST MODE: Sending to {actual_recipient} instead of {recipient}")
                            else:
                                actual_recipient = recipient
                            
                            # Personalize content if needed
                            if config["type"] == "Personalized (Using template tags)":
                                email_subject = replace_placeholders(config["subject"], row_dict)
                                email_body = replace_placeholders(config["content"], row_dict)
                            else:
                                email_subject = config["subject"]
                                email_body = config["content"]
                            
                            # Create and send message
                            message = create_message(
                                config["sender"],
                                actual_recipient,
                                email_subject,
                                email_body,
                                is_html=config["is_html"],
                                attachments=config["attachments"]
                            )
                            
                            status_placeholder.info(f"Sending email to {actual_recipient if test_mode else recipient} ({i+1}/{len(df)})...")
                            success, message_id = send_message(service, 'me', message)
                            
                            # Record result
                            results.append({
                                "recipient": recipient,
                                "status": "Success" if success else "Failed",
                                "message_id": message_id if success else None,
                                "error": None if success else message_id,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            
                            # Update progress
                            progress_bar.progress((i + 1) / len(df))
                            
                            # Add delay between emails
                            if i < len(df) - 1 and delay > 0:
                                time.sleep(delay)
                        
                        # Show results
                        success_count = sum(1 for r in results if r["status"] == "Success")
                        fail_count = len(results) - success_count
                        
                        status_class = "success" if fail_count == 0 else "error" if success_count == 0 else "info"
                        status_message = f"Completed: {success_count} succeeded, {fail_count} failed"
                        
                        status_placeholder.markdown(f"<div class='status-box {status_class}'>{status_message}</div>", unsafe_allow_html=True)
                        
                        # Display results dataframe
                        results_df = pd.DataFrame(results)
                        results_placeholder.dataframe(results_df)
                        
                        # Option to download results
                        csv = results_df.to_csv(index=False)
                        b64 = base64.b64encode(csv.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="email_results.csv">Download Results as CSV</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        
                    except Exception as e:
                        status_placeholder.error(f"Error: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("📧 Email Sender App | Built with Streamlit")

if __name__ == "__main__":
    main()