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

    rows = df.loc[df['День недели'] == day, ["Название дерева", "Количество фруктов"]]
    if rows.empty:
        return False

    return rows.to_string(index=False, header=False)


def get_row_by_day_tree(day, tree):
    df = get_df()
    result = df.loc[(df['День недели'] == day) & (df['Название дерева'] == tree)]
    if result.empty:
        return False

    return result.to_string(index=False, header=False)


def is_exist(day, trees):
    df = get_df()
    result = df.loc[(df['День недели'] == day) & (df['Название дерева'] == trees)]
    return result.empty


def update_row(sheet_name: str, new_values: dict):
    sheet = client.open(sheet_name).sheet1
    data = sheet.get_all_records()
    for row_index, row in enumerate(data):
        if row['День недели'] == new_values['updates_day'] and row['Название дерева'] == new_values['updates_tree']:
            if new_values.get('updates_new_day'):
                sheet.update_cell(row_index+2, 1, new_values['updates_new_day'])
            if new_values.get('updates_new_tree'):
                sheet.update_cell(row_index+2, 2, new_values['updates_new_tree'])
            if new_values.get('updates_new_count'):
                sheet.update_cell(row_index+2, 3, new_values['updates_new_count'])


items = {'updates_day': 'Четверг',
         'updates_tree': 'Бук',
         # 'updates_new_day': 'Четверг',
         'updates_new_tree': 'Древень',
         # 'updates_new_count': '100'
         }

print(update_row(os.environ.get("GOOGLE_SHEET_NAME"), items))