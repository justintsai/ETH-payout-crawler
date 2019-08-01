'''
Get the payout history of my ETH address on GPUMINEPOOL
and upload it to my google spreadsheet
'''
import json
import sys
import time
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Use APScheduler on non-Unix-like systems (which lack daemons like 'at' or 'cron')
# from apscheduler.schedulers.blocking import BlockingScheduler

def get_data(url):
    data = []
    response = requests.get(url)
    json_data = str(response.text)
    json_obj = json.loads(json_data)

    for i in range(len(json_obj['payments'])):
        data.append([])
    for i in range(len(json_obj['payments'])):
        j = len(json_obj['payments']) -1 - i
        for key, value in json_obj['payments'][i].items():
            data[j].append(value)
        data[j][2], data[j][3] = data[j][3], data[j][2]
        data[j][0] = timestamp_datetime(data[j][0])
    data.append(json_obj['totalPaid'])
    # len(data) <= 32 since the json only stores the latest 31 payment
    return data


def timestamp_datetime(value):
    format = '%Y-%m-%d %H:%M:%S'
    value = time.localtime(value)
    dt = time.strftime(format, value)
    return dt


def auth_gss_client(path, scope):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(path, scope)
    return gspread.authorize(credentials)


def add_sheet(gss_client, key, name, row, col):
    worksheet = gss_client.open_by_key(key)
    worksheet.add_worksheet(name, row, col)
    sheet = worksheet.worksheet(name)
    sheet.insert_row(['時間', '數量', '交易ID', '狀態', '總額'], 1)


def look_into_sheet(table, data):
    # Return where the latest record in my sheet is in json data
    # data[len(data)-2] is the latest payout record
    for i in range(len(data)-1, 0, -1):
        data[i-1][1] = round(float(data[i-1][1]), 8)
        table[-1][1] = float(table[-1][1])
        if table[-1][0] == data[i-1][0]:
            return i-1  # if i-1 == 29, nothing to update


def update_sheet(gss_client, key, data):
    worksheet = gss_client.open_by_key(key)
    sheet = worksheet.worksheet('出金記錄')
    table = sheet.get_all_values()
    n_records = look_into_sheet(table, data)
    if n_records == len(data)-2:
        print('Everything up-to-date')
    else:
        print('%d record(s) not on the sheet!' % (len(data)-2 - n_records))
        for i in range(1, len(data)-n_records-1):
            sheet.insert_row(data[n_records+i], len(table)+i)
            print(data[n_records+i], len(table)+i)
        sheet.update_acell('E2', data[len(data)-1])
    print('Total Earned: {:.8f}'.format(data[len(data)-1]))


spreadsheetId = '1pAed6_SMO34Jet_BADdE6c2L8iiCMtFxnGNTJ2MSQCg'
# spreadsheetId = '1YVqHckcpI7BclVhTrh0wER3mNb1aNj7-65Xz59wjvRQ' # for testing


def main():
    sys.path = '/Users/Justin/Documents/Projects/ETH payout crawler/'
    url = 'https://gpumine.org/api/bill/0xeB8afFBcCb50c74e9dFf208C7d4bD48e0a06C336?coin=eth'

    auth_json_path = sys.path + 'GPUMINEPOOL-8cef42f493a3.json'
    gss_scope = ['https://spreadsheets.google.com/feeds']
    gss_client = auth_gss_client(auth_json_path, gss_scope)

    try:
        update_sheet(gss_client, spreadsheetId, get_data(url))
    except:
        add_sheet(gss_client, spreadsheetId, '出金記錄', 1, 26)
        update_sheet(gss_client, spreadsheetId, get_data(url))


if __name__ == '__main__':
    # def job():
    start_time = time.time()
    main()
    print("--- took %f seconds ---" % (time.time() - start_time))

# scheduler = BlockingScheduler()
# scheduler.add_job(job, 'cron', day='*/3', hour=16, minute=30)
# print(scheduler.get_jobs())
# scheduler.start()
