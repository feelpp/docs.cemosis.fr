# -*- coding:utf-8 -*-

""" Extract iBat sensors data from Elasticsearch indices """

from elasticsearch import Elasticsearch
import urllib3
import csv
import os
import sys
import copy
import certifi
import argparse
import time
all_field = ["temperature","humidity","light","pir","sound"]

# tag::parameters[]
interval = 60
date_deb = "2019-01-01T00:00:00Z"
date_fin = "2019-01-31T23:59:59Z"
# end::parameters[]
""" *** Parameters *** """
##
parser = argparse.ArgumentParser()

parser.add_argument("-sd","--start_date" , default = date_deb,
                    help = "the start date for the data export in the format \"yyyy-mm-ddTHH:mn:ssZ\" (default: %(default)s)")
parser.add_argument("-ed","--end_date" , default = date_fin,
                    help = "the end date for the data export in the format \"yyyy-mm-ddTHH:mn:ssZ\" (default: %(default)s)")
parser.add_argument("-in","--interval" , default = interval, type = int,
                    help = "set give the number of minutes for the aggregation (default: %(default)s)")

parser.add_argument("-f","--field", nargs = '*', choices = all_field,
                    default = all_field,
                    help = "set the phisical field(s) (default: %(default)s)")

parser.add_argument("-a","--all", type = int , default = 1, choices = [1,2],
                    help = "set geometry choice. \n 1: for all building \n 2: for both pieces (default: %(default)s)")

args = parser.parse_args()

# tag::env_var[]
try:
   SERVER = os.environ["SERVER"]
except KeyError:
   print ("Please set the environment variable SERVER")
   sys.exit(1)

try:
   LOGIN = os.environ["LOGIN"]
except KeyError:
   print ("Please set the environment variable LOGIN")
   sys.exit(1)

try:
   PASSWORD = os.environ["PASSWORD"]
except KeyError:
   print ("Please set the environment variable PASSWORD")
   sys.exit(1)
# end::env_var[]

# Disable warning for self-signed certificats
urllib3.disable_warnings()

# Connect to Elasticsearch cluster
# tag::connexion[]
try:
    es = Elasticsearch(
        [SERVER],
        http_auth=(LOGIN, PASSWORD),
        port=8443,
        use_ssl=True,
        verify_certs=False,
        timeout=100
    )
    print ("Connected", es.info())
except Exception as ex:
    print ("Error:", ex)
# end::connexion[]
csv_first_ligne = []
if args.all==2:
   csv_first_ligne += ["zigduino-35","zigduino-37"]
else:
# tag::node_names[]
    csv_first_ligne += ["zigduino-"+str(i) for i in range(1,70)]
    csv_first_ligne.extend(["zigduino-81","zigduino-82"])
# end::node_names[]

# tag::query[]
def Query(node,deb,fin,interval,field):
    Q_IBAT = {
    "size": 0,
    "query": {
        "bool": {
            "filter": [
            {
                "range": {
                    "@timestamp": {
                        "gte": deb,
                        "lte": fin
                    }
                }
            },
            {
                "query_string": {
                    "analyze_wildcard": True,
                    "query":"node: \""+node+"\""
                }
            }]
        }
    },
    "aggs": {
        "2": {
            "date_histogram": {
                "interval": str(interval)+"m",
                "field": "@timestamp",
                "min_doc_count":0,
                "format": "yyyy-MM-dd'T'HH:mm:ss"
            },
            "aggs": {
                "1":{
                    "avg": {"field": field}
                }
            }
        }
    }

    }
    return Q_IBAT
# end::query[]
time_series=["date_format","epoch_format"]
start = time.time()
# tag::data_extract[]
data = []
for field in set(args.field):
    for i,node in enumerate(csv_first_ligne):
        temp_val = []
        body = Query(node,args.start_date,args.end_date,args.interval,field)
        result = es.search(index="ibat-*", body=body, size=0)
        for hit in result['aggregations']['2']['buckets']:
             temp_val.append(hit['1']['value'])
        data.append(temp_val)
        time_series.append(node + ":" + field)
# end::data_extract[]
res = time.time() - start
print("execution time",res)
# tag::csv_preparation[]
val_date = []
val_epoch = []
for hit in result['aggregations']['2']['buckets']:
    val_date.append(hit['key_as_string'])
    val_epoch.append(hit['key'])

var_temp = [val_date,val_epoch]
var_temp.extend(data)

# end::csv_preparation[]

# tag::csv[]
with open("export.csv", "w") as f_write:
    writer = csv.writer(f_write)
    writer.writerow(time_series)
    writer.writerows(zip(*var_temp))
# end::csv[]
