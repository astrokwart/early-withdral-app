
import pandas as pd
import streamlit as st
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Early Withdrawal Checker", layout="wide")

st.title("🏦 Early Withdrawal Report Generator")
st.markdown("Upload deposit and withdrawal Excel files to identify early withdrawals (within 14 working days).")

# File uploads
deposit_file = st.file_uploader("📥 Upload Deposit File", type=["xlsx"])
withdrawal_file = st.file_uploader("📥 Upload Withdrawal File", type=["xlsx"])

# Helper function to calculate working days
def working_days_between(start_date, end_date):
    days = np.busday_count(start_date.date(), end_date.date())
    return days

if deposit_file and withdrawal_file:
    deposit_df = pd.read_excel(deposit_file)
    withdrawal_df = pd.read_excel(withdrawal_file)

    # Standardize column names
    deposit_df.columns = deposit_df.columns.str.strip().str.lower()
    withdrawal_df.columns = withdrawal_df.columns.str.strip().str.lower()

    # Rename for consistency
    deposit_df.rename(columns={
        "deposit date": "deposit_date",
        "account number": "account_number",
        "customer name": "customer_name",
        "mobile banker": "mobile_banker"
    }, inplace=True)

    withdrawal_df.rename(columns={
        "withdrawal date": "withdrawal_date",
        "account number": "account_number",
        "customer name": "customer_name"
    }, inplace=True)

    # Convert account numbers to string in both files
    deposit_df["account_number"] = deposit_df["account_number"].astype(str)
    withdrawal_df["account_number"] = withdrawal_df["account_number"].astype(str)

    # Convert date columns
    deposit_df["deposit_date"] = pd.to_datetime(deposit_df["deposit_date"])
    withdrawal_df["withdrawal_date"] = pd.to_datetime(withdrawal_df["withdrawal_date"])

    # Merge deposits and withdrawals on account number
    merged_df = pd.merge(deposit_df, withdrawal_df, on="account_number", how="left", suffixes=('', '_withdrawal'))

    # Calculate working days between deposit and withdrawal
    merged_df["working_days"] = merged_df.apply(
        lambda row: working_days_between(row["deposit_date"], row["withdrawal_date"])
        if pd.notnull(row["withdrawal_date"]) else None,
        axis=1
    )

    # Flag early withdrawals (less than 14 working days)
    merged_df["early_withdrawal"] = merged_df["working_days"].apply(lambda x: x is not None and x < 14)

    # Filter early withdrawals only
    early_withdrawals = merged_df[merged_df["early_withdrawal"] == True]

    st.success(f"✅ Found {len(early_withdrawals)} early withdrawals.")

    # Display grouped report
    st.subheader("📊 Early Withdrawal Summary by Mobile Banker")
    summary = early_withdrawals.groupby("mobile_banker")["amount"].sum().reset_index()
    summary.rename(columns={"amount": "Total Early Withdrawal (GHS)"}, inplace=True)
    st.dataframe(summary)

    # Display detailed table
    st.subheader("📄 Detailed Early Withdrawal Report")
    st.dataframe(early_withdrawals[[
        "deposit_date", "customer_name", "account_number",
        "amount", "mobile_banker", "withdrawal_date", "working_days"
    ]])

    # Excel download function
    def to_excel(df):
        from io import BytesIO
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        return output.getvalue()

    # Download button
    st.download_button(
        label="⬇ Download Full Report as Excel",
        data=to_excel(early_withdrawals),
        file_name="early_withdrawals_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
