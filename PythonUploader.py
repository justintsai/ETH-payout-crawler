'''
Get the payout history of my ETH address on GPUMINEPOOL
and upload it to my google spreadsheet
'''
import requests
import json
import sys
import time
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_data(url):
    data = []
    response = requests.get(url)
    jsonData = str(response.text)
    json_obj = json.loads(jsonData)
    pattern = '[0-9\-]+[0-9:]+'
    
    for i in range(len(json_obj['payments'])):
        data.append([])
        for key, value in json_obj['payments'][i].items():
            data[i].append(value)
        data[i][0] = ' '.join(re.findall(pattern, data[i][0])[:-1]) # shorten timestamps
    data.append(sum(map(float, list(map(list, zip(*data)))[1]))) # transpose "data" then sum payments
    return data

def auth_gss_client(path, scope):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(path, scope)
    return gspread.authorize(credentials)

def add_sheet(gss_client, key, name, row, col):
    worksheet = gss_client.open_by_key(key) 
    worksheet.add_worksheet(name, row, col)
    sheet = worksheet.worksheet(name)
    sheet.insert_row(['時間','數量','交易ID','狀態','總額'],1)

def check(l, data, i):
    data[i-1][1] = float(data[i-1][1])
    l[i][1] = float(l[i][1])
    return data[i-1] == l[i][:4] # l[0] is not part of payout history

def look_into_sheet(l, data):
    for i in range(1, len(data)): # data[len(data)-2] is the latest payout record
        try:
            check(l, data, i)
        except:
            return i-1 # (i-1) records on the sheet
    return len(data)-1 # records are up to date

def update_sheet(gss_client, key, data):
    worksheet = gss_client.open_by_key(key)
    sheet = worksheet.worksheet('出金記錄')
    list_of_lists = sheet.get_all_values()
    n_records = look_into_sheet(list_of_lists, data)
    if n_records == len(data)-1:
        print('Everything up-to-date')
    else:
        print('%d record(s) not on the sheet!' % (len(data)-1 - n_records))
        for i in range(n_records, len(data)-1):
            sheet.insert_row(data[i], i+2)
        sheet.update_acell('E2', data[len(data)-1])

spreadsheetId = '1pAed6_SMO34Jet_BADdE6c2L8iiCMtFxnGNTJ2MSQCg' 
# spreadsheetId = '1YVqHckcpI7BclVhTrh0wER3mNb1aNj7-65Xz59wjvRQ' for testing

def main():
    sys.path = '/Users/Justin/Documents/Projects/ETH payout crawler/'
    url = 'https://eth-tw.gpumine.org/api/miner/0xeB8afFBcCb50c74e9dFf208C7d4bD48e0a06C336'
    
    auth_json_path = sys.path + 'GPUMINEPOOL-8cef42f493a3.json'
    gss_scope = ['https://spreadsheets.google.com/feeds']
    gss_client = auth_gss_client(auth_json_path, gss_scope)
    
    try:
        update_sheet(gss_client, spreadsheetId, get_data(url))
    except:
        add_sheet(gss_client, spreadsheetId, '出金記錄', 1, 26)
        update_sheet(gss_client, spreadsheetId, get_data(url))
        
if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))