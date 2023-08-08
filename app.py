import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import glob
import os
import re
from pathlib import Path


data_path = Path("C:/Users/tomom/OneDrive - Cornell University/20_Recruiting/7_Marketing Data Analytics/nSpire_Dashboard/Dashboard")
date_format = "%m%d%Y"

def parse_date(date_string):
    return datetime.strptime(date_string, date_format)


def load_data(today_date_str):
    today_file = data_path / f"SessionTime_{today_date_str}.csv"
    today_data = pd.read_csv(today_file)
    today_data["Date"] = pd.to_datetime(today_data["Date"], format="%m/%d/%Y")
    today_data = today_data.rename(columns={"User ID": "UserID"})
    
    lastlogin_path = data_path / "lastlogin.csv"
    lastlogin = pd.read_csv(lastlogin_path, parse_dates=["LastLoginDate"]) if lastlogin_path.exists() else pd.DataFrame(columns=["UserID", "LastLoginDate"])
    
    userstatus_path = data_path / "userStatus.csv"
    userstatus = pd.read_csv(userstatus_path) if userstatus_path.exists() else pd.DataFrame(columns=["UserID"])
    
    return today_data, lastlogin, userstatus

def update_user_status(today_data, lastlogin, userstatus, today_date_str):
    column_name_for_today = parse_date(today_date_str).strftime('%m%d%Y')

    if column_name_for_today not in userstatus.columns:
        userstatus[column_name_for_today] = "Unknown"

    # First merge userstatus with today_data
    merged1 = userstatus.merge(today_data, on="UserID", how="outer")

    # Now, merge the resultant dataframe, merged1, with lastlogin
    merged_final = merged1.merge(lastlogin, on="UserID", how="outer")

    conditions, choices = get_user_conditions_and_choices(merged_final, today_date_str)
    merged_final[column_name_for_today] = np.select(conditions, choices)

    # Update the last login information for today
    today_login = today_data[["UserID", "Date"]].rename(columns={"Date": "LastLoginDate"})
    lastlogin = lastlogin[~lastlogin["UserID"].isin(today_data["UserID"])]
    lastlogin = pd.concat([lastlogin, today_login])

    # Save the updated user status and last login information
    userstatus = merged_final[["UserID"] + list(userstatus.columns[1:])]
    lastlogin.to_csv(data_path / "lastlogin.csv", index=False)
    userstatus.to_csv(data_path / "userStatus.csv", index=False)

    return merged_final


def get_user_conditions_and_choices(merged, today_date_str):
    # Convert the columns to datetime format and ensure NaNs are NaT
    merged["Date"] = pd.to_datetime(merged["Date"])
    merged["LastLoginDate"] = pd.to_datetime(merged["LastLoginDate"])

    # Get the column name for the date 8 days ago
    eight_days_ago_str = (pd.to_datetime(today_date_str, format="%m%d%Y") - timedelta(days=8)).strftime("%m%d%Y")

    # Get the status from 8 days ago, ensuring to use `get` to avoid KeyError
    status_eight_days_ago = merged.get(eight_days_ago_str, pd.NA)

    is_logged_in_today = merged["Date"].notna()
    last_login_within_7days = (pd.to_datetime(today_date_str, format="%m%d%Y") - merged["LastLoginDate"]).dt.days <= 7
    last_login_out_of_7days = (pd.to_datetime(today_date_str, format="%m%d%Y") - merged["LastLoginDate"]).dt.days > 7
    no_prior_status = pd.isna(status_eight_days_ago)

    # Define conditions based on the provided logic
    conditions = [
        # Non-user
        no_prior_status & is_logged_in_today,
        no_prior_status & ~is_logged_in_today & last_login_within_7days,
        no_prior_status & pd.isna(merged["LastLoginDate"]),

        # New
        (status_eight_days_ago == "New") & last_login_within_7days & is_logged_in_today,
        (status_eight_days_ago == "New") & last_login_within_7days & ~is_logged_in_today,
        (status_eight_days_ago == "New") & last_login_out_of_7days & is_logged_in_today,
        (status_eight_days_ago == "New") & last_login_out_of_7days & ~is_logged_in_today,

        # Inactive
        (status_eight_days_ago == "Inactive") & last_login_within_7days & is_logged_in_today,
        (status_eight_days_ago == "Inactive") & last_login_out_of_7days & is_logged_in_today,
        (status_eight_days_ago == "Inactive") & last_login_out_of_7days & ~is_logged_in_today,
        (status_eight_days_ago == "Inactive") & last_login_within_7days & ~is_logged_in_today,

        # Return
        (status_eight_days_ago == "Return") & last_login_within_7days & ~is_logged_in_today,
        (status_eight_days_ago == "Return") & last_login_out_of_7days & is_logged_in_today,
        (status_eight_days_ago == "Return") & last_login_out_of_7days & ~is_logged_in_today,
        (status_eight_days_ago == "Return") & last_login_within_7days & is_logged_in_today,

        # Engaged
        (status_eight_days_ago == "Engaged") & last_login_within_7days & ~is_logged_in_today,
        (status_eight_days_ago == "Engaged") & last_login_out_of_7days & is_logged_in_today,
        (status_eight_days_ago == "Engaged") & last_login_out_of_7days & ~is_logged_in_today,
        (status_eight_days_ago == "Engaged") & last_login_within_7days & is_logged_in_today,
    ]

    choices = [
        "New", "New", "New",
        "Engaged", "New", "Return", "Inactive",
        "Return", "Return", "Inactive", "Inactive",
        "Engaged", "Return", "Inactive", "Engaged",
        "Engaged", "Return", "Inactive", "Engaged"
    ]

    return conditions, choices


st.title("Under Construction")

date_input = st.text_input('Enter today\'s date in mmddyyyy format:')
if date_input:
    today_data, lastlogin, userstatus = load_data(date_input)
    merged_df = update_user_status(today_data, lastlogin, userstatus, date_input)
    st.success("User status updated!")
    # If you want to display the merged dataframe, you can use:
    # st.write(merged_df)
