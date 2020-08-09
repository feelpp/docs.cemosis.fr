import sys
import subprocess
import pandas as pd
import json
import timeit
import argparse
import numpy as np
import datetime
import time
import csv
import matplotlib.pyplot as plt

# tag::query[]
def build_query(node, start, end, interval, field):
    query_ibat = {
     "size": 0,
     "query": {
        "bool": {
            "filter": [
             {
                "range": {
                    "@timestamp": {
                        "gte": start,
                        "lte": end
                    }
                }
             },
             {
                "query_string": {
                    "analyze_wildcard": True,
                    "query": "node: \""+node+"\""
                }
             }]
        }
     },
     "aggs": {
        "2": {
            "date_histogram": {
                "interval": str(interval)+"m",
                "field": "@timestamp",
                "min_doc_count": 0,
                "format": "yyyy-MM-dd'T'HH:mm:ss"
            },
            "aggs": {
                 "1": {
                    "avg": {"field": field}
                 }
            }
        }
     }

    }
    return query_ibat
# end::query[]


def string_elm_to_list(argument, max_value, forme=""):
    '''
        Converts a string element to a list
            Parameters:
                    argument(str): the argument to convert.
                    max_value(int): the maximum value that the argument can
                                         reach (14 for zones and 72 for nodes)
                    forme(str): node or zone
            Returns:
                    string_elm_to_list(str): a list that contains the values
                                                     of the argument
            Example:
                    >>> argument = '1,4-6,8,10-13'
                    >>> zone_list = string_elm_to_list(argument, 14, "zone")
                    >>> print(zone_list)
                    ['1','4','5','6','8','10','11','12','13']
    '''
    returned_list = []
    try:
        if argument and',' in argument:
            value_comma = argument.split(',')
            for value in value_comma:
                if value and '-' in value:
                    value_dash = value.split('-')
                    value_dash = [int(v) for v in value_dash
                                  if int(v) > 0 and int(v) < max_value]
                    returned_list.extend([forme+str(v)
                                         for v in range(value_dash[0],
                                         value_dash[1]+1)])
                elif value:
                    if int(value) > max_value or int(value) < 0:
                        raise(Exception())
                    returned_list.append(forme+value)
                else:
                    raise(Exception)
        elif argument and '-' in argument:
            value_dash = argument.split('-')
            value_dash = [int(v) for v in value_dash
                          if int(v) > 0 and int(v) < max_value]
            returned_list = [forme+str(v)
                             for v in range(value_dash[0], value_dash[1]+1)]
        elif argument:
            if int(argument) > 0 and int(argument) < max_value:
                returned_list.append(forme+argument)
    except Exception:
        print("Error values in argument", argument)
    if not(returned_list):
        exit(1)

    return returned_list

def nodes_to_zones(file, zone_to_request):
    """ Reads json file.
            Parameters:
                    file (string) : the json file ro read
                    zone_to_request(list of string) : List of zones
            Returns:
                    my_dic(dict): contains the nodes of each zone and
                                  their area
    """
    df = pd.read_json(file)
    my_dic = {}
    for zone in zone_to_request:
        if(int(df.building[zone]['n_nodes'])) != 0:
            zone_node_area = []
            for i in range(1, int(df.building[zone]['n_nodes'])+1):
                zone_node_area.append(("zigduino-"+str(df.building[zone]
                                       ['node'+str(i)]['node_id']),
                                       float(df.building[zone]['node'+str(i)]
                                       ['location']['space_area'])))
            my_dic.update({str(zone): zone_node_area})
        else:
            print("No nodes in", zone)
    return my_dic

# tag::submit_query[]
def submit_query(node, args, field, es):
    temp_val = []
    body = build_query(node,
                       args.start_date,
                       args.end_date,
                       args.interval,
                       field)
    result = es.search(index="ibat-*", body=body, size=0)
    for hit in result['aggregations']['2']['buckets']:
        temp_val.append(hit['1']['value'])
    return result, temp_val
# end::submit_query[]
