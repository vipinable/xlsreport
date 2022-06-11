#!/usr/bin/env python
sqldump = 'ospos-full-backup-2021-12-25-21.sql'

def parse_items():
    print(sqldump)
    ospos_items = {}
    with open(sqldump,'r') as f:
       line = f.readline()
       while line:
         if ('ospos_items' in line) and ('INSERT INTO' in line):
            line = line.replace('),(',';')
            line = line.replace(');',';')
            for i in line.split(';'):
                value = i.strip().split(',')
                if value[0]:
                  key = value[9]
                  ospos_items[key] = value
         line = f.readline()
    print(len(ospos_items))

    for id,name in ospos_items.items():
        if name[3] == 'NULL':
          print(id,name[0])

def parse_sales_payments():
    ospos_sales_payments = {}
    with open(sqldump,'r') as f:
       line = f.readline()
       while line:
          if ('ospos_sales_payments' in line) and ('INSERT INTO' in line):
            line = line.replace('),(',';').strip('\n').replace("'","")
            line = line.replace(');',';').strip(';')
            for sale in line.split(';'):
               print(sale.split(','))
               date = sale.split(',')[7][:10]
               amount = float(sale.split(',')[3])
               if date in ospos_sales_payments.keys():
                   if sale.split(',')[2] in ospos_sales_payments[date].keys():
                       ospos_sales_payments[date][sale.split(',')[2]].append(amount)
                   else:
                       ospos_sales_payments[date][sale.split(',')[2]] = []
                       ospos_sales_payments[date][sale.split(',')[2]].append(amount)
               else:
                   ospos_sales_payments[date] = {}
                   ospos_sales_payments[date][sale.split(',')[2]] = []
                   ospos_sales_payments[date][sale.split(',')[2]].append(amount)
          line = f.readline()
    print(ospos_sales_payments)

if __name__ == "__main__":
  #parse_items()
  parse_sales_payments()
