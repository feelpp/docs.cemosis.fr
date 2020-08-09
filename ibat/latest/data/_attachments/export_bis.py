# -*- coding:utf-8 -*-

""" Extract iBat sensors data from Elasticsearch indices """

from elasticsearch import Elasticsearch, RequestsHttpConnection
import urllib3
import csv
import os
import sys
import argparse
import time
from datetime import datetime
from tools import string_elm_to_list, nodes_to_zones, submit_query

# tag::parameters[]
all_field = ["temperature","humidity","light","pir","sound"]
interval = 60
date_deb = "2019-01-01T00:00:00Z"
date_fin = "2019-01-31T23:59:59Z"
# end::parameters[]

""" *** Parameters *** """
# Arguments parsing

parser = argparse.ArgumentParser()

parser.add_argument("-f",
                    "--field",
                    nargs='*',
                    choices=all_field,
                    default=all_field,
                    help="""set the phisical field(s)
                     (default: %(default)s)""")

parser.add_argument("-sd",
                    "--start_date",
                    default=date_deb,
                    help="""the start date for the data export in the format
                    \"yyyy-mm-ddTHH:mn:ssZ\" (default: %(default)s)""")

parser.add_argument("-ed",
                    "--end_date",
                    default=date_fin,
                    help="""the end date for the data export in the format
                    \"yyyy-mm-ddTHH:mn:ssZ\" (default: %(default)s)""")

parser.add_argument("-in",
                    "--interval",
                    default=interval,
                    type=int,
                    help="""set the sampling period in minutes
                            (default: %(default)s min)""")

parser.add_argument("-c",
                    "--choices",
                    help="""set geometry choices in the format:\
                    \"min-max\": nodes interval(pieces),\
                    \n \"value,value,...,value\": list of nodes,\
                    \n \"min-max,value,...\": nodes interval,\
                    with list of nodes """)

parser.add_argument("-z",
                    "--zone",
                    help="""set the zones to request""")

args = parser.parse_args()

# tag::env_var[]
try:
    SERVER = os.environ["SERVER"]
except KeyError:
    print("Please set the environment variable SERVER")
    sys.exit(1)

try:
    LOGIN = os.environ["LOGIN"]
except KeyError:
    print("Please set the environment variable LOGIN")
    sys.exit(1)

try:
    PASSWORD = os.environ["PASSWORD"]
except KeyError:
    print("Please set the environment variable PASSWORD")
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
        ca_certs=False,
        verify_certs=False,
        connection_class=RequestsHttpConnection,
        timeout=100
    )
    print("Connected", es.info())
except Exception as ex:
    print("Error:", ex)
# end::connexion[]

# tag::node_names[]

names_nodes = []
if args.choices:
    names_nodes = string_elm_to_list(args.choices, 82, "zigduino-")
    name_file_outputed = "nodes_export.csv"

# end::node_names[]

# tag::zone_names[]

zone_to_request = []
# If args.zones, we map the nodes to the appropriate zone
# The results are stored in a dictionnary called dic_zones
# as {"zone_i": [(node_1, area_1), (node_2, area_2) etc...]}
if args.zone:
    zone_to_request = string_elm_to_list(args.zone, 14, "zone")
    dic_zones = nodes_to_zones("multizone_modele_attributes.json",
                               zone_to_request)
    name_file_outputed = "zones_export.csv"

# end::zone_names[]

col_names_csv = ["date_format", "epoch_format"]

executions_times = {}
if args.choices:
    executions_times["types_count"] = str(len(names_nodes)) + " nodes:"
    executions_times["types_values"] = names_nodes
elif args.zone:
    executions_times["types_count"] = str(len(zone_to_request)) + " zones:"
    executions_times["types_values"] = zone_to_request


start_time = time.time()
# Here, we extract selected data from the ibat query
# tag::data_extract[]

data = []
for field in set(args.field):
    if args.choices:
        for i, node in enumerate(names_nodes):
            tmp_result, temp_val = submit_query(node, args, field, es)
            if not(temp_val):
                continue
            result = tmp_result
            data.append(temp_val)
            col_names_csv.append(node + ":" + field)
    elif args.zone:
        temp_val_field = []
        for key, value in dic_zones.items():
            for node, area in value:
                tmp_result, temp_val = submit_query(node, args, field, es)
                if not(temp_val):
                    continue
                result = tmp_result
                data.append(temp_val)
                temp_val_field.append(temp_val)
                col_names_csv.append(key + node + ":" + field)

time_query = time.time() - start_time

# end::data_extract[]
executions_times["query"] = float("{:.2f}".format(time_query))

print("execution time : {}".format(executions_times["query"]))

# tag::csv_preparation[]
val_date = []
val_epoch = []
try:
    if result['aggregations']['2']['buckets']:
        for hit in result['aggregations']['2']['buckets']:
            val_date.append(hit['key_as_string'])
            val_epoch.append(hit['key'])
except Exception:
    print('No nodes to request')
    exit(1)

var_temp = [val_date, val_epoch]
var_temp.extend(data)
# end::csv_preparation[]

# tag::csv[]

with open(name_file_outputed, "w") as f_write:
    writer = csv.writer(f_write)
    writer.writerow(col_names_csv)
    writer.writerows(zip(*var_temp))

# end::csv[]