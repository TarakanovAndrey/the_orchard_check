import os
from dotenv import load_dotenv
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials


load_dotenv()


SCOPE = os.environ.get('SCOPES')
SHEETS_NAME = os.environ.get("GOOGLE_SHEET_NAME")
MY_GMAIL = os.environ.get("MY_GMAIL")


def authorization(scope):
    credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json', SCOPE)
    gc = gspread.authorize(credentials)
    return gc


def get_sheets(sheets_name):
    gc = authorization(SCOPE)
    wks = gc.open(sheets_name).sheet1
    return wks


def create_google_sheet(client, sheet_name):
    google_sheet = None
    try:
        google_sheet = client.create(sheet_name)
        google_sheet.share(
            MY_GMAIL,
            perm_type='user',
            role='writer'
        )
        sheet = get_sheets(SHEETS_NAME)
        sheet.append_row(["День недели", "Название дерева", "Количество фруктов"])
        print("Таблица успешно создана")
    except Exception as e:
        print(e)
        return google_sheet


def get_df():
    wks = get_sheets(SHEETS_NAME)
    data = wks.get_all_values()
    headers = data.pop(0)
    df = pd.DataFrame(data, columns=headers)
    return df


def add_row(client, sheet_name, row):
    sheet = get_sheets(SHEETS_NAME)
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
    sheet = get_sheets(SHEETS_NAME)
    data = sheet.get_all_records()
    for row_index, row in enumerate(data):
        if row['День недели'] == new_values['updates_day'] and row['Название дерева'] == new_values['updates_tree']:
            if new_values.get('updates_new_day'):
                sheet.update_cell(row_index+2, 1, new_values['updates_new_day'])
            if new_values.get('updates_new_tree'):
                sheet.update_cell(row_index+2, 2, new_values['updates_new_tree'])
            if new_values.get('updates_new_count'):
                sheet.update_cell(row_index+2, 3, new_values['updates_new_count'])


def clear_table(sheet_name):
    sheet = get_sheets(SHEETS_NAME)
    rows_count = sheet.row_count
    sheet.delete_rows(2, rows_count)


def is_datas_exists(sheet_name):
    sheet = get_sheets(SHEETS_NAME)
    rows_count = sheet.row_count
    return rows_count > 1
