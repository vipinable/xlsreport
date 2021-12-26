import pandas as pd
import os
import datetime
import boto3
import smtplib
import io
import tarfile
from botocore.exceptions import ClientError

session = boto3.session.Session()
sns = session.client('sns')
ssm = session.client('ssm')
s3 = session.client('s3')

snsTopicArn = os.environ['SNSTOPIC']

response = ssm.get_parameter(Name='EmailiDs',WithDecryption=True)
emailids = response['Parameter']['Value'].split(',')

def s3get(bucket,key):
    stream = s3.get_object(Bucket=bucket,Key=key)
    s3obj = stream['Body'].read()
    return(s3obj)

def sesmail(text,html,EmailId):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "Reports<" + emailids[0] + ">"
    
    # Replace recipient@example.com with a "To" address. If your account 
    # is still in the sandbox, this address must be verified.
    RECIPIENT = EmailId
    
    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the 
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    #CONFIGURATION_SET = "ConfigSet"
    
    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"
    
    # The subject line for the email.
    SUBJECT = "Malabar Essence Daily Closing Report"
    
    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = text
    
    # The HTML body of the email.
    BODY_HTML = html
    
    # The character encoding for the email.
    CHARSET = "UTF-8"
    
    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)
    
    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            #ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def snsmail(content):
    response = sns.publish(
    TopicArn=snsTopicArn,
    Message=content,
    Subject='Malabar Essence Closing Report'
    )
    return(None)
    
def dailyaccounts():

    url = 'https://docs.google.com/spreadsheets'
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
    print(df.iloc[row].to_string())
    df.to_excel("/tmp/output.xlsx")
    df.to_html("/tmp/output.html")
    html = ''
    with open('/tmp/output.html','r') as f:
        for line in f.readlines():
            html = html + line
    print(type(html))
    sesmail(df.iloc[row].to_string(),html)
    
def process_transations(tr,MonthData,ThisMonth):
    response = ssm.get_parameter(Name='meturl',WithDecryption=True)
    meturl = response['Parameter']['Value']
    print(meturl)
    df = pd.read_csv(meturl)
    for index, row in df.iterrows():
        rowlist = row.tolist()
        if rowlist[0].split()[0][-7:] == ThisMonth:
            if rowlist[0].split()[0] in MonthData:
                MonthData[rowlist[0].split()[0]][rowlist[1]].append(rowlist[2])

    html = '<table cellspacing=”0” cellpadding=”0” width=”640” align=”center” border=”1”>' + tr
    print(MonthData)
    #ToDay = datetime.datetime.today().strftime("%d/%m/%Y")
    DictTotal = {'sale': [], 'purchase': [], 'expense': [], 'deposit': [], 'diff': [], 'mvk': [], 'nvn': [], 'vsh': []}
    for key, value in MonthData.items():
        print(key)
        newtr = tr.replace('Date',key)
        newtr = newtr.replace('Close Balance',str(sum(value['Close Balance'])))
        newtr = newtr.replace('Expenses',str(sum(value['Expense'])))
        newtr = newtr.replace('Purchases',str(sum(value['Purchase'])))
        newtr = newtr.replace('Deposit',str(sum(value['Deposit'])))
        newtr = newtr.replace('Open Balance',str(sum(value['Open Balance'])))
        newtr = newtr.replace('Credit Received',str(sum(value['Credit Received'])))
        newtr = newtr.replace('Store Credit',str(sum(value['Credit'])))
        newtr = newtr.replace('Sale',str(round(sum(value['Cash'] + value['UPI'] + value['Due']),2)))
        newtr = newtr.replace('UPI',str(round(sum(value['UPI']),2)))
        newtr = newtr.replace('Due',str(round(sum(value['Due']),2)))
        newtr = newtr.replace('Payments',str(round(sum(value['Cash']),2)))
        newtr = newtr.replace('NVN',str(sum(value['NVN'])))
        newtr = newtr.replace('MVK',str(sum(value['MVK'])))
        newtr = newtr.replace('VSH',str(sum(value['VSH'])))
        
        ActualCash = sum(value['Open Balance'] + value['Cash'] + value['Credit Received']) - sum(value['Expense'] + value['NVN'] + value['MVK'] + value['VSH'])
        Cashdiff = sum(value['Close Balance']) - ActualCash
        newtr = newtr.replace('Diff',str(round(Cashdiff,2)))
        
        html = html + newtr
        
        DictTotal['sale'].append(round(sum(value['Cash'] + value['UPI'] + value['Due']),2))
        DictTotal['purchase'].append(sum(value['Purchase']))
        DictTotal['expense'].append(sum(value['Expense']))
        DictTotal['deposit'].append(sum(value['Deposit']))
        if Cashdiff < 0:
            DictTotal['diff'].append(round(Cashdiff,2))
        DictTotal['mvk'].append(sum(value['MVK']))
        DictTotal['nvn'].append(sum(value['NVN']))
        DictTotal['vsh'].append(sum(value['VSH']))
    
    pl = sum(DictTotal['sale']) - sum(DictTotal['purchase'] + DictTotal['expense'] + DictTotal['mvk'] + DictTotal['nvn'] + DictTotal['vsh'])
        
    html = html + '</table>'
    html = html + '<table cellspacing=”0” cellpadding=”0” align=”left” border=”1”>'
    html = html + '<tr><td><h2>Total Sale</h2></td><td><h2>' + str(round(sum(DictTotal['sale']),2)) + '</h2></td></tr>'
    html = html + '<tr><td><h2>Total Purchase</h2></td><td><h2>' + str(sum(DictTotal['purchase'])) + '</h2></td></tr>'
    html = html + '<tr><td><h2>Total Expense</h2></td><td><h2>' + str(sum(DictTotal['expense'])) + '</h2></td></tr>'
    html = html + '<tr><td><h2>Total Deposit</h2></td><td><h2>' + str(sum(DictTotal['deposit'])) + '</h2></td></tr>'
    html = html + '<tr><td><h2>Total MVK</h2></td><td><h2>' + str(sum(DictTotal['mvk'])) + '</h2></td></tr>'
    html = html + '<tr><td><h2>Total NVN</h2></td><td><h2>' + str(sum(DictTotal['nvn'])) + '</h2></td></tr>'
    html = html + '<tr><td><h2>Total VSH</h2></td><td><h2>' + str(sum(DictTotal['vsh'])) + '</h2></td></tr>'
    html = html + '<tr><td><h2>Total Diff</h2></td><td><h2>' + str(sum(DictTotal['diff'])) + '</h2></td></tr>'
    #html = html + '<tr><td><h2>Profit/Loss</h2></td><td><h2>' + str(round(pl,2)) + '</h2></td></tr>'
    html = html + '</table>'
    
    sesmail('New email Test',html,emailids[1])
    #sesmail('New email Test',html,emailids[2])
    print(DictTotal)

    
def parse_sqldump(bucket,key,ThisMonth):
    MonthData = {}
    stream = s3.get_object(Bucket=bucket,Key=key)
    tmpfile = io.BytesIO()
    tmpfile.write(stream['Body'].read())
    tmpfile.seek(0)
    with tarfile.open(fileobj=tmpfile, mode="r:gz") as tararch:
        extract = tararch.extractfile(key.split('/')[1][:-7])
        content = io.BufferedReader(extract)
        line = content.readline().decode('utf-8')
        while line:
            if ('ospos_sales_payments' in line) and ('INSERT INTO' in line):
                line = line.replace('),(',';').strip('\n').replace("'","")
                line = line.replace(');',';').strip(';')
                for sale in line.split(';'):
                    date = datetime.datetime.strptime(sale.split(',')[7][:10], "%Y-%m-%d").strftime("%d/%m/%Y")
                    amount = float(sale.split(',')[3])
                    if ThisMonth in date:
                        if date in MonthData.keys():
                            if sale.split(',')[2] in MonthData[date].keys():
                                MonthData[date][sale.split(',')[2]].append(amount)
                            else:
                                MonthData[date][sale.split(',')[2]] = []
                                MonthData[date][sale.split(',')[2]].append(amount)
                        else:
                            MonthData[date] = {}
                            MonthData[date]['Cash'] = []
                            MonthData[date]['Due'] = []
                            MonthData[date]['UPI'] = []
                            MonthData[date]['Expense'] = []
                            MonthData[date]['Purchase'] = []
                            MonthData[date]['Credit'] = []
                            MonthData[date]['Credit Received'] = []
                            MonthData[date]['Sales'] = []
                            MonthData[date]['Close Balance'] = []
                            MonthData[date]['NVN'] = []
                            MonthData[date]['MVK'] = []
                            MonthData[date]['VSH'] = []
                            MonthData[date]['Open Balance'] = []
                            MonthData[date]['Deposit'] = []
                            MonthData[date][sale.split(',')[2]].append(amount)
            line = content.readline().decode('utf-8')
        return(MonthData)
    
def lambda_handler(event, context):
    
    try:
        eventSource = event['Records'][0]['eventSource']
    except Exception:
        eventSource = 'other'
    
    tr =  '''  <tr>
                <td>Date</td>
				<td>Open Balance</td>
				<td>Sale</td>
				<td>Payments</td>
				<td>UPI</td>
				<td>Due</td>
				<td>Expenses</td>
				<td>Purchases </td>
				<td>Store Credit</td>
				<td>NN</td>
				<td>MVK</td>
				<td>VSH</td>
				<td>Credit Received</td>
				<td>Close Balance</td>
				<td>Deposit</td>
				<td>Diff</td>
			   </tr> '''


    if eventSource == 'aws:s3':
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        ThisMonth = datetime.datetime.today().strftime("%m/%Y")
        #ThisMonth = '10/2021'
        MonthData = parse_sqldump(bucket,key,ThisMonth)
        process_transations(tr,MonthData,ThisMonth)
    
    #sesmail('Testing',header.replace('content',table))
    #dailyaccounts()


    return('completed')
