import os
from dotenv import load_dotenv
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

def get_df():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']


    credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)

    gc = gspread.authorize(credentials)
    wks = gc.open("MyOrchard").sheet1

    data = wks.get_all_values()
    headers = data.pop(0)

    df = pd.DataFrame(data, columns=headers)
    return df


def create_google_sheet(client, sheet_name):
    google_sheet = None
    try:
        google_sheet = client.create(sheet_name)
        google_sheet.share(
            "smallniels@gmail.com",
            perm_type='user',
            role='writer'
        )
        sheet = client.open(sheet_name).sheet1
        sheet.append_row(["День недели", "Название дерева", "Количество фруктов"])
        print("Success")
    except Exception as e:
        print(e)
        return google_sheet


client = gspread.service_account(filename="creds.json")


def add_row(client, sheet_name, row):
    sheet = client.open(sheet_name).sheet1
    sheet.append_row(row)


def get_rows(day):
    df = get_df()
    rows = df.loc[df['День недели'] == day]
    if rows.empty:
        return "Данные за этот день отсутствуют в таблице"

    return rows.to_string(columns=["Название дерева", "Количество фруктов"],
                          index=False,
                          justify="inherit",
                          col_space = [10, 10]
                          )

