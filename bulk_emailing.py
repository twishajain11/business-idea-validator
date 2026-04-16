import streamlit as st
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json
import pandas as pd
import time
import io

# --- Page Setup ---
st.set_page_config(page_title="AI Email Automator", page_icon="📧", layout="centered")

st.title("📧 AI Email Automator")
st.write("Write, send and track emails automatically with AI!")
st.caption("Made by Twisha Jain")

# --- How to Use Guide ---
with st.expander("👋 First time here? Click to get started!"):
    st.markdown("""
    ### Welcome to AI Email Automator!
    
    Before using this app you need **2 things:**
    
    **1. Your Gmail address**
    
    **2. A Gmail App Password** ← not your real password!
    
    ---
    
    ### How to Create Your App Password:
    1. Go to **myaccount.google.com**
    2. Click **Security** on the left
    3. Turn on **2-Step Verification** if not already on
    4. In the search bar type **App Passwords**
    5. Click on it → type any name like `email-automator`
    6. Click **Generate**
    7. Copy the **16 digit password** shown
    8. Paste it in the App Password field below
    
    ---
    
    ⚠️ **Safety Tips:**
    - Always use your **App Password** — never your real Gmail password
    - App Passwords can be deleted anytime from your Google account
    - This app never stores your password anywhere
    - Your emails are only logged in **your own** Google Sheet
    """)

# --- API Key ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- Google Sheets Setup ---
def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client_gs = gspread.authorize(creds)
    sheet = client_gs.open("Email Tracker").sheet1
    return sheet

# --- Send Email Function ---
def send_email(sender_email, app_password, recipient_email, 
               subject, body, attachment=None, attachment_name=None):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    if attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={attachment_name}"
        )
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())

# --- Generate Email with AI ---
def generate_email(purpose, email_type, tone, recipient_name):
    prompt = f"""
    Write a {tone.lower()} email for the following purpose:
    
    EMAIL TYPE: {email_type}
    PURPOSE: {purpose}
    RECIPIENT NAME: {recipient_name}
    
    Write ONLY the email with:
    - Subject line starting with "Subject:"
    - A blank line
    - The email body
    
    Keep it concise, compelling and {tone.lower()}.
    Do not add any extra commentary.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- Log to Google Sheets ---
def log_email(sheet, recipient_name, recipient_email, 
              purpose, content, followup_days):
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    followup_date = (datetime.now() + 
                    timedelta(days=followup_days)).strftime("%Y-%m-%d")
    sheet.append_row([
        date, recipient_name, recipient_email,
        purpose, content, "Sent", followup_date
    ])

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "✍️ Single Email",
    "📨 Bulk Email",
    "📊 Email Tracker",
    "🔔 Follow Up Reminders"
])

# =====================
# TAB 1 - SINGLE EMAIL
# =====================
with tab1:
    st.header("✍️ Write & Send Single Email")

    st.subheader("Your Email Details")
    st.info("⚠️ Use your **App Password** — not your real Gmail password!")

    col1, col2 = st.columns(2)
    with col1:
        sender_email = st.text_input("Your Gmail",
                       placeholder="yourname@gmail.com",
                       key="single_sender")
    with col2:
        app_password = st.text_input("App Password",
                       type="password",
                       placeholder="16 digit app password",
                       key="single_password")

    with st.expander("📖 How to get your App Password"):
        st.markdown("""
        1. Go to **myaccount.google.com**
        2. Click **Security**
        3. Turn on **2-Step Verification**
        4. Search for **App Passwords**
        5. Name it anything → click **Generate**
        6. Copy the 16 digit password → paste above ✅
        """)

    st.markdown("---")
    st.subheader("Recipient Details")

    col1, col2 = st.columns(2)
    with col1:
        recipient_name = st.text_input("Recipient Name",
                          placeholder="John Smith",
                          key="single_name")
    with col2:
        recipient_email_single = st.text_input("Recipient Email",
                                 placeholder="john@company.com",
                                 key="single_email")

    st.markdown("---")
    st.subheader("Email Details")

    email_type = st.selectbox("Email Type", [
        "Internship Application",
        "Job Application",
        "Follow Up",
        "Cold Outreach",
        "Thank You Email",
        "Meeting Request",
        "Custom"
    ], key="single_type")

    purpose = st.text_area("Describe the purpose", height=100,
                placeholder="e.g. Apply for data analyst internship at Google...",
                key="single_purpose")

    col1, col2 = st.columns(2)
    with col1:
        tone = st.selectbox("Tone", [
            "Professional", "Friendly", "Formal", "Casual"
        ], key="single_tone")
    with col2:
        followup_days = st.number_input(
            "Follow up reminder (days)",
            min_value=1, max_value=30, value=3,
            key="single_followup")

    # PDF Attachment
    st.markdown("---")
    st.subheader("📎 Add Attachment (Optional)")
    uploaded_pdf = st.file_uploader("Upload PDF (resume, project, proposal)",
                    type="pdf", key="single_pdf")
    if uploaded_pdf:
        st.success(f"✅ {uploaded_pdf.name} ready to attach!")

    # Generate Button
    if st.button("✨ Generate Email", key="single_generate"):
        if not purpose:
            st.warning("Please describe the purpose!")
        else:
            with st.spinner("AI is writing your email..."):
                email_content = generate_email(
                    purpose, email_type, tone, recipient_name)
                st.session_state["single_email_content"] = email_content
                st.session_state["single_subject"] = email_content.split(
                    "\n")[0].replace("Subject:", "").strip()

    # Show Generated Email
    if "single_email_content" in st.session_state:
        st.markdown("---")
        st.subheader("📝 Your Generated Email")
        st.info("💡 You can edit before sending!")

        edited_email = st.text_area("Edit if needed",
                          value=st.session_state["single_email_content"],
                          height=300,
                          key="single_edited")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Send Email", key="single_send"):
                if not sender_email or not app_password:
                    st.warning("Please enter your Gmail and App Password!")
                elif not recipient_email_single:
                    st.warning("Please enter recipient email!")
                else:
                    try:
                        with st.spinner("Sending..."):
                            subject = st.session_state["single_subject"]
                            body = "\n".join(edited_email.split("\n")[2:])

                            attachment_data = None
                            attachment_name = None
                            if uploaded_pdf:
                                attachment_data = uploaded_pdf.read()
                                attachment_name = uploaded_pdf.name

                            send_email(
                                sender_email, app_password,
                                recipient_email_single, subject, body,
                                attachment_data, attachment_name
                            )

                            try:
                                sheet = get_sheet()
                                log_email(sheet, recipient_name,
                                         recipient_email_single,
                                         purpose, edited_email,
                                         followup_days)
                                st.success("✅ Email sent and logged!")
                            except Exception:
                                st.success("✅ Email sent successfully!")
                                st.warning("Could not log to Google Sheets.")
                            st.balloons()

                    except smtplib.SMTPAuthenticationError:
                        st.error("❌ Wrong App Password! Check and try again.")
                    except Exception as e:
                        st.error(f"❌ Failed: {e}")

        with col2:
            st.download_button(
                label="💾 Save as Draft",
                data=edited_email,
                file_name="email_draft.txt",
                mime="text/plain"
            )

# =====================
# TAB 2 - BULK EMAIL
# =====================
with tab2:
    st.header("📨 Bulk Email Sender")
    st.write("Send personalized or same emails to multiple people at once!")

    st.subheader("Your Email Details")
    st.info("⚠️ Use your **App Password** — not your real Gmail password!")

    col1, col2 = st.columns(2)
    with col1:
        bulk_sender = st.text_input("Your Gmail",
                      placeholder="yourname@gmail.com",
                      key="bulk_sender")
    with col2:
        bulk_password = st.text_input("App Password",
                        type="password",
                        placeholder="16 digit app password",
                        key="bulk_password")

    st.markdown("---")
    st.subheader("Upload Contact List")

    with st.expander("📖 How should my CSV look?"):
        st.markdown("""
        Your CSV file should have these exact columns:
        ```
        Name, Email
        John Smith, john@google.com
        Sarah Lee, sarah@amazon.com
        HR Manager, hr@microsoft.com
        ```
        First row must be the headers!
        """)

    csv_file = st.file_uploader("Upload CSV with Name and Email columns",
                type="csv", key="bulk_csv")

    if csv_file:
        df_contacts = pd.read_csv(csv_file)
        st.success(f"✅ {len(df_contacts)} contacts loaded!")
        st.dataframe(df_contacts.head(), use_container_width=True)

    st.markdown("---")
    st.subheader("Email Details")

    bulk_type = st.selectbox("Email Type", [
        "Internship Application",
        "Job Application",
        "Follow Up",
        "Cold Outreach",
        "Thank You Email",
        "Meeting Request",
        "Custom"
    ], key="bulk_type")

    bulk_purpose = st.text_area("Describe the purpose", height=100,
                    placeholder="e.g. Reach out to companies for data analyst internship...",
                    key="bulk_purpose")

    bulk_tone = st.selectbox("Tone", [
        "Professional", "Friendly", "Formal", "Casual"
    ], key="bulk_tone")

    bulk_followup = st.number_input(
        "Follow up reminder (days)",
        min_value=1, max_value=30, value=3,
        key="bulk_followup")

    # Personalization option
    personalized = st.radio(
        "Email Style",
        ["Same email for everyone", "Personalized for each person"],
        key="bulk_style"
    )

    # PDF Attachment
    st.markdown("---")
    st.subheader("📎 Add Attachment (Optional)")
    bulk_pdf = st.file_uploader("Upload PDF to attach to all emails",
               type="pdf", key="bulk_pdf")
    if bulk_pdf:
        st.success(f"✅ {bulk_pdf.name} will be attached to all emails!")

    # Send Bulk Emails
    if st.button("🚀 Send Bulk Emails", key="bulk_send"):
        if not csv_file:
            st.warning("Please upload a CSV file!")
        elif not bulk_purpose:
            st.warning("Please describe the purpose!")
        elif not bulk_sender or not bulk_password:
            st.warning("Please enter your Gmail and App Password!")
        else:
            df_contacts = pd.read_csv(csv_file)
            total = len(df_contacts)
            success_count = 0
            fail_count = 0

            st.markdown("---")
            st.subheader("📤 Sending Progress")
            progress_bar = st.progress(0)
            status_text = st.empty()

            attachment_data = None
            attachment_name = None
            if bulk_pdf:
                attachment_data = bulk_pdf.read()
                attachment_name = bulk_pdf.name

            # Generate one email if same for everyone
            if personalized == "Same email for everyone":
                with st.spinner("AI generating email..."):
                    base_email = generate_email(
                        bulk_purpose, bulk_type,
                        bulk_tone, "there")
                    base_subject = base_email.split(
                        "\n")[0].replace("Subject:", "").strip()
                    base_body = "\n".join(base_email.split("\n")[2:])

            results = []

            for i, row in df_contacts.iterrows():
                name = row.get("Name", "there")
                email = row.get("Email", "")

                if not email:
                    continue

                try:
                    status_text.text(f"Sending to {name} ({i+1}/{total})...")

                    if personalized == "Personalized for each person":
                        with st.spinner(f"Generating email for {name}..."):
                            email_content = generate_email(
                                bulk_purpose, bulk_type, bulk_tone, name)
                            subject = email_content.split(
                                "\n")[0].replace("Subject:", "").strip()
                            body = "\n".join(email_content.split("\n")[2:])
                    else:
                        subject = base_subject
                        body = base_body.replace("there", name)
                        email_content = base_email

                    send_email(
                        bulk_sender, bulk_password,
                        email, subject, body,
                        attachment_data, attachment_name
                    )

                    results.append({
                        "Name": name,
                        "Email": email,
                        "Status": "✅ Sent"
                    })
                    success_count += 1

                    try:
                        sheet = get_sheet()
                        log_email(sheet, name, email,
                                 bulk_purpose, email_content,
                                 bulk_followup)
                    except Exception:
                        pass

                except Exception as e:
                    results.append({
                        "Name": name,
                        "Email": email,
                        "Status": f"❌ Failed: {e}"
                    })
                    fail_count += 1

                progress_bar.progress((i + 1) / total)
                time.sleep(1)

            status_text.text("Done!")

            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total", total)
            col2.metric("✅ Sent", success_count)
            col3.metric("❌ Failed", fail_count)

            results_df = pd.DataFrame(results)
            st.dataframe(results_df, use_container_width=True)

            if success_count > 0:
                st.balloons()
                st.success(f"🎉 Successfully sent {success_count} emails!")

# =====================
# TAB 3 - TRACKER
# =====================
with tab3:
    st.header("📊 Email Tracker")
    st.write("All your sent emails logged automatically!")

    if st.button("🔄 Load My Emails", key="load"):
        try:
            with st.spinner("Loading from Google Sheets..."):
                sheet = get_sheet()
                data = sheet.get_all_records()

                if not data:
                    st.info("No emails logged yet!")
                else:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Sent", len(df))
                    col2.metric("Pending Follow Ups",
                               len(df[df["Status"] == "Sent"]))
                    col3.metric("Replied",
                               len(df[df["Status"] == "Replied"]))

        except Exception as e:
            st.error(f"Could not load: {e}")

# =====================
# TAB 4 - REMINDERS
# =====================
with tab4:
    st.header("🔔 Follow Up Reminders")
    st.write("Never forget to follow up on an important email!")

    if st.button("🔍 Check My Reminders", key="reminders"):
        try:
            with st.spinner("Checking..."):
                sheet = get_sheet()
                data = sheet.get_all_records()

                if not data:
                    st.info("No emails logged yet!")
                else:
                    df = pd.DataFrame(data)
                    today = datetime.now().strftime("%Y-%m-%d")

                    due = df[df["Follow Up Date"] <= today]
                    due = due[due["Status"] == "Sent"]

                    overdue = df[df["Follow Up Date"] < today]
                    overdue = overdue[overdue["Status"] == "Sent"]

                    upcoming = df[df["Follow Up Date"] == today]
                    upcoming = upcoming[upcoming["Status"] == "Sent"]

                    if due.empty:
                        st.success("🎉 No follow ups needed today!")
                    else:
                        if not overdue.empty:
                            st.error(f"🚨 {len(overdue)} overdue follow up(s)!")
                        if not upcoming.empty:
                            st.warning(f"⚠️ {len(upcoming)} due today!")

                        for _, row in due.iterrows():
                            with st.expander(
                                f"📧 {row['Recipient Name']} — {row['Purpose']}"
                            ):
                                st.write(f"**Sent on:** {row['Date']}")
                                st.write(f"**Follow up due:** {row['Follow Up Date']}")
                                st.write(f"**Email:** {row['Recipient Email']}")
                                if st.button("✅ Mark as Replied",
                                            key=f"reply_{row['Recipient Email']}"):
                                    st.success("Marked as replied!")

        except Exception as e:
            st.error(f"Could not load: {e}")

st.markdown("---")
st.markdown("<center>Made with ❤️ by Twisha Jain | AI Email Automator</center>",
            unsafe_allow_html=True)