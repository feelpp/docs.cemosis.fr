""" Extract iBat sensors data from Elasticsearch indices """
from elasticsearch import Elasticsearch, RequestsHttpConnection
from missing.impute import Impute
from smoother.kalman import KalmanSmoother
# from sklearn.metrics import mean_squared_error
from tools import string_elm_to_list, build_query, nodes_to_zones, plot_test_imputation, index, aggregatedCsv, mean_aggregated, submit_query, calculate_execution_time
from tools_latex import add_line_to_latex_file
from random import randint
from datetime import datetime
import urllib3
import csv
import os
import sys
import argparse
import time
import pandas as pd
# import sys
sys.path.insert(1, 'smoother')  # For python 2

all_field = ["temperature", "humidity", "light", "pir", "sound"]

# tag::parameters[]
interval = 60
date_deb = "2019-01-01T00:00:00Z"
date_fin = "2019-01-31T23:59:59Z"
impute_ws = 10
impute_ntrees = 50
smooth_emsize = 10
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

parser.add_argument("-a",
                    "--aggregated",
                    action="store_true",
                    help="""aggregate data output """)


parser.add_argument("--impute",
                    action="store_true",
                    help="""impute missing values in the time series""")
# parser.add_argument("--test_impute", action="store_true",
#                    help="""test imputation algorithm  """)
parser.add_argument("--impute_verbose",
                    action="store_true",
                    help="""verbosity mode for imputation""")
parser.add_argument("--impute_ws",
                    type=int,
                    default=impute_ws,
                    help="""window size for the imputation process,
                    default:10""")
parser.add_argument("--impute_ntrees",
                    type=int,
                    default=impute_ntrees,
                    help="""number of trees in the random forest,
                    default:50""")


parser.add_argument("--smooth",
                    action="store_true",
                    help="""smooth the times series, impute recommended""")
parser.add_argument("--smooth_verbose",
                    action="store_true",
                    help="""verbosity mode for smoothing""")
parser.add_argument("--smooth_emsize",
                    type=int,
                    default=smooth_emsize,
                    help="""size of the sample for EM training,
                    default:10, -1:all the time serie""")

parser.add_argument("-eh","--execution_history",
                    action="store_true",
                    help="""Store on a latex file history of executions times""")

args = parser.parse_args()

if args.aggregated and not(args.zone):
    parser.error("--aggregated requires --zone.")

if args.choices and args.zone:
    parser.error("must choose between --choices and --zone, not both of them.")

# End of argument parsing


# Check that all environment variables are correctly set
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

date_time_now = datetime.now().strftime("%d_%m_%Y_%H_h_%M_min_%S_s")
name_file_outputed = "results_csv/export_" + date_time_now + ".csv"
name_file_agregated_outputed = "results_csv/export_agregated" + date_time_now + ".csv"


with open(name_file_outputed, "w") as f_write:
    writer = csv.writer(f_write)
    writer.writerow(col_names_csv)
    writer.writerows(zip(*var_temp))

# end::csv[]
time_impute = 0
time_smooth = 0 
if args.impute or args.smooth:
    df = pd.read_csv(name_file_outputed,
                     encoding='latin',
                     delimiter=",",
                     decimal=',',
                     index_col=0,
                     parse_dates=True)
    df = df.drop(columns=['epoch_format'])
    df = df.apply(pd.to_numeric)

    start_time = time.time()
    if args.impute:
        my_imp = Impute(df, window_size=args.impute_ws,
                        n_trees=args.impute_ntrees,
                        verbose=args.impute_verbose)
        my_imp.fillWithRF()
        df = my_imp.getData()

    time_impute = time.time() - start_time
    executions_times["impute"] = float("{:.2f}".format(time_impute))

    start_time = time.time()
    if args.smooth:
        ks = KalmanSmoother(df, verbose=args.smooth_verbose)
        df = ks.smooth(em_training=args.smooth_emsize)

    time_smooth = time.time() - start_time
    executions_times["smooth"] = float("{:.2f}".format(time_smooth))






    df.to_csv(name_file_outputed)






# Agregation: nodes into zones

# Here we agregate the different nodes into their respective nodes
# Within each zone, the field of interest is agregated with an area weighted
# sum of each node of the zone

# aggregate export_test.csv
csv_file = pd.read_csv(name_file_outputed)
name_col = []
name_col += [csv_file.columns[i] for i in range(1, csv_file.shape[1])]

temp = [val_date, val_epoch]
aggregated_dict = {}

if args.zone:
    for field in set(args.field):
        for key, value in dic_zones.items():
            val_field = []
            for node, area in value:
                val = [temp for temp in csv_file[key+node+":"+field]]
                val_field.append(val)
            if args.aggregated:
                # Computing the area weighted sum of each node within the zone
                aggregated_dict = mean_aggregated(aggregated_dict, key,
                                                  field, value, val_field)
    if args.aggregated:
        aggregatedCsv(name_file_agregated_outputed,
                      temp,
                      aggregated_dict)

# Attention, il ne faut pas calculer le temps à ce moment du script,
# qui prend également en compte le temps mis pour l'agrégation des zones
# i.e t_total = time_query + time_impute + time_smooth + t_agregation_zones
# Ici on veut simplement t_total =time_query + time_impute + time_smooth
#executions_times["total"] = float("{:.2f}".format(calculate_execution_time(start_time)))

executions_times["total"] = float("{:.2f}".format(time_query + time_impute + time_smooth))

if args.execution_history:
    add_line_to_latex_file("history_executions", executions_times)




# Cette partie du code n'a pas sa place ici. Devrait être mis dans un script à part

    # if args.test_impute:
    #     my_imp = Impute(df, window_size=args.impute_ws,
    #                     n_trees=args.impute_ntrees,
    #                     verbose=args.impute_verbose)
    #     st = '2019-06-16 00:00:00'
    #     ed = '2019-06-16 02:00:00'
    #     s, l = index(df, st, ed)
    #     df_AImpute, df_BImpute, mse = my_imp.test_impute(df.columns[0],
    #                                                      s,
    #                                                      l,
    #                                                      n=1)
    #     df_test = pd.DataFrame({"real_values": df_BImpute,
    #                            "infered_values": df_AImpute})
    #     df_test.to_csv("results_csv/test_impute.csv")
    #     plot_test_imputation(df_test, 'test_imputation',
    #                          df.columns[0],
    #                          st,
    #                          ed,
    #                          mse)
























