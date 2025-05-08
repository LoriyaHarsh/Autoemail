# Email Sender App

A Streamlit application that allows you to send personalized emails to multiple recipients using Gmail API.

![Email Sender App](https://via.placeholder.com/800x400?text=Email+Sender+App)

## Features

- 📧 Send personalized emails to multiple recipients
- 📊 Upload CSV or Excel files with recipient data
- 🎨 Rich text editor for creating HTML emails
- 📎 Support for file attachments
- 🔄 Template placeholders for personalized content
- 📈 Real-time tracking of email sending progress
- 📝 Detailed success/failure reporting

## Prerequisites

- Python 3.7 or higher
- A Google account with Gmail
- Google Cloud Platform project with Gmail API enabled

## Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/yourusername/email-sender-app.git
cd email-sender-app
```

### Step 2: Create a virtual environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install required packages

```bash
pip install -r requirements.txt
```

If you don't have a requirements.txt file, install the packages directly:

```bash
pip install streamlit pandas google-auth google-auth-oauthlib google-api-python-client pillow
```

### Step 4: Set up Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Navigate to "APIs & Services" > "Library"
4. Search for "Gmail API" and enable it
5. Go to "APIs & Services" > "Credentials"
6. Click "Create Credentials" > "OAuth client ID"
7. Configure the OAuth consent screen:
   - Add the required scopes:
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.readonly`
   - Add your email as a test user
8. Select "Desktop app" as the application type
9. Name your OAuth client and click "Create"
10. Download the JSON file and save it as `credentials.json` in the same directory as your app

## Usage

### Step 1: Start the application

```bash
streamlit run mail.py
```

The application will open in your default web browser. If it doesn't open automatically, navigate to `http://localhost:8501`.

### Step 2: Log in with your Google account

- Click the "Login with Google" button in the sidebar
- This will open a browser window for authentication
- Follow the prompts to allow the application access to your Gmail account

### Step 3: Upload your data

- Navigate to the "Upload Data" tab
- Upload a CSV or Excel file with your recipient information
- The file must contain at least an "Email" column
- Other columns can be used as placeholders in your template

### Step 4: Configure your email

- In the "Configure Email" tab, set up your email subject and content
- Choose between static or personalized content
- Use placeholders like `{{name}}` to personalize your emails
- Choose between plain text or rich HTML formatting
- Add attachments if needed

### Step 5: Send emails

- In the "Send & Results" tab, set the delay between emails
- Enable test mode to send all emails to yourself (recommended for testing)
- Click "Send Emails" to start the process
- Monitor the progress and results in real-time

## Template Personalization

You can customize the email content with placeholders that match the column names in your data file:

- If your file has columns named "name", "company", and "plan"
- You can use `{{name}}`, `{{company}}`, and `{{plan}}` in your email template
- These will be replaced with the corresponding values for each recipient

## Important Notes

- In test mode, all emails will be sent to your own email address (the one you used to log in) instead of the recipients in the file
- The application uses the Gmail API to send emails, so you're limited to Gmail's sending limits (up to 500 emails per day for regular Gmail accounts)
- Make sure your `credentials.json` file is kept secure and not shared publicly

## Troubleshooting

- **Authentication issues**: Try deleting the `token.json` file (if it exists) and logging in again
- **Emails fail to send**: Check that you have the correct permissions and that your Gmail account doesn't have additional security restrictions
- **Missing columns**: Ensure your data file contains all the columns referenced in your template
- **Rich text editor issues**: If the rich text editor doesn't work properly, switch to the plain text mode

## Security Considerations

- The app stores authentication tokens locally in `token.json`
- Never share your `credentials.json` or `token.json` files
- Use test mode first to verify email content before sending to real recipients
- Be mindful of Gmail's sending limits to avoid account restrictions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Uses [Gmail API](https://developers.google.com/gmail/api) for sending emails
- Pandas for data processing
