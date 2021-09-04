import pandas as pd
import datetime
import boto3

session = boto3.session.Session()

snsTopicArn = 'arn:aws:sns:us-east-1:731685434595:sceptre-test-xlsreport-sam-SNSTopic4xlsreport-50KGQW0MFDRX'

def sendmail(content):
    sns = session.client('sns')
    response = sns.publish(
    TopicArn=snsTopicArn,
    Message=content,
    Subject='Malabar Essence Closing Report'
    )
    return(None)

def lambda_handler(event, context):
    
    url = 'https://docs.google.com/spreadsheets/d/1pz5WxHe8-YjhaMWKkXtz26dPFttfsm2BPv53mfay5I4/export?format=csv&gid=241921063'
    df = pd.read_csv(url)
    print(df)
    
    row = int(datetime.datetime.now().strftime('%d'))
    
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
    
    print(type(df.iloc[row].to_string()))
    sendmail(df.iloc[row].to_string())
    print(df.iloc[row].to_string())
    df.to_excel("/tmp/output.xlsx")

    return('completed')
