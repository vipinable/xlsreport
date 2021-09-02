import pandas as pd
import datetime

def lambda_handler(event, context):
    
    df = pd.read_csv(url)
    print(df)
    
    #row = int(datetime.datetime.now().strftime('%d'))
    row = -1
    
    try:
        rowIndex = df.index[row]
    except IndexError:
        print('Error: data not found for today')
    
    cash = df.iloc[row,1]
    ob =  df.iloc[row,2]
    sale =  df.iloc[row,3]
    cp =  df.iloc[row,4]
    expense = df.iloc[row,5]
    purchase = df.iloc[row,6]
    storeCredit = df.iloc[row,7]
    creditReceived =  df.iloc[row,8]
    deposit = df.iloc[row,9]
    nn = df.iloc[row,10]
    mh = df.iloc[row,11]
    
    actualCash = (ob + cp + creditReceived + nn + mh) - (storeCredit + expense)
    
    df.loc[rowIndex, 'UPI'] = sale - cp
    df.loc[rowIndex, 'Actual Cash'] = actualCash
    df.loc[rowIndex, 'Cash diff'] = cash - actualCash
    
    print(df.iloc[row])
    df.to_excel("output.xlsx")

    return(True)

if __name__ == '__main__':
      lambda_handler('event', 'context')
