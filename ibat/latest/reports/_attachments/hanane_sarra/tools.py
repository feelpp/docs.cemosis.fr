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


def build_query(node, start, end, interval, field):
    """
    Build an elastic search query for submission to the ibat database

    Parameters
    ----------
        node : str
            Name of the node to be queried in the ibat database
        start : str
            Starting date of the time interval queried.
            start is passed in the format "yyyy-mm-ddTHH:mn:ssZ"
        end : str
            ending date of the time interval queried.
            fin is passed in the format "yyyy-mm-ddTHH:mn:ssZ"
        interval : int
            Sampling period in minutes
        field : str
            field to be queried
            Either "temperature", "humidity", "light", "pir" or "sound"

    Returns
    ----------
        query_ibat : pandas dataframe
            Dataframe whose missing period starting at index "starts"
            of length "length" has been imputed.

    Example:
    ----------
     my_query =  build_query("zigduino-4",
                             "2019-01-01T00:00:00Z",
                             "2019-01-01T10:00:00Z",
                             60,
                             "temperature")
    """
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


def mean_aggregated(aggregated_dict, zone, field, list_value, value_field):
    '''
        Calculates the average weighted by the surfaces of the different
                                 rooms within a given area .
            Parameters:
                    zone(str): affected zone
                    field(str): affected field
                    list_value(tuple): tuple of node with its area
                    value_field(list of list): list of values of the field
                                                of the different nodes
                                                associated to the zone
            Returns:
                    aggregated_dict(dict): contains data aggregated by zones
    '''
    area = [v for n, v in list_value]
    mean = []
    if not(aggregated_dict.get(zone)):
        aggregated_dict[zone] = {}
    for j in range(len(value_field[0])):
        sum_area = 0
        sum_values = 0
        for i in range(len(area)):
            sum_area += area[i]
            try:
                sum_values += (area[i] * value_field[i][j])
            except Exception:  # in case different length of value_field
                continue
        mean.append(sum_values / sum_area)

    aggregated_dict[zone][field] = mean

    return aggregated_dict


def aggregatedCsv(file, var_temp, aggregated_dict):
    ''' Creates a csv file that contains var_temp and the aggregated_dict
           Parameters:
                file (string) : the csv file to create
                var_temp(list of string) : list of date_format and epoch_format
                aggregated_dict(dict):  contains data aggregated by zones
    '''
    with open(file, "w", newline='') as my_csv:
        writer = csv.writer(my_csv)
        first_ligne = ["date_format", "epoch_format"]
        aggregated_data = []
        for key, value in aggregated_dict.items():
            for ke, val in value.items():
                first_ligne += [key+"-"+ke]
                aggregated_data.append(val)
        var_temp.extend(aggregated_data)
        writer.writerow(first_ligne)
        # Yannick test
        writer.writerows(zip(*var_temp))



def dates_to_list_month(start_date, end_date):
    """ Lists the different dates from a start date, an end date, with an
            interval of one month.
            Parameters:
                    start_date(date_format): the start date for the data export
                    end_date(date_format) : the end date for the data export
            Returns:
                    list_months(list of string): contains the different dates
                        from the start date, the end date, with an interval
                        of one month.
    """
    first_month = int(list(start_date)[5]+list(start_date)[6])

    tmp_date = start_date
    list_months = []

    while(end_date[:7] != tmp_date[:7]):
        first_month += 1

        if first_month > 12:
            first_month = 1
            next_year = int(list(tmp_date)[2] + list(tmp_date)[3]) + 1
            if next_year > 9:
                tmp_date = tmp_date[:2] + str(next_year) + tmp_date[4:]

        if first_month > 9:
            tmp_date = tmp_date[:5] + str(first_month) + tmp_date[7:]
        else:
            tmp_date = tmp_date[:5] + '0' + str(first_month) + tmp_date[7:]

        if end_date[:7] == tmp_date[:7]:
            list_months.append(end_date)
        else:
            list_months.append(tmp_date)

    return list_months


def unit_field(field):
    """ Gives the unit of the specific field
            Parameters:
                    field(string): the field we want to get the unit from
            Returns:
                    unit(string): the unit of the given field
    """
    unit = {"temperature": ["Temperature(°C)"], "sound": ["Sound(dB)"],
            "humidity": ['Humidity(%)'], "light": ["Light(lx)"],
            "pir": [' Pir']}
    df = pd.DataFrame(unit, columns=['temperature', 'sound', 'humidity',
                                     'light', 'pir'])
    for i in df.columns:
        if i in field:
            unit = df.loc[:, [i]]
            unit = unit.iloc[0, 0]
    return unit


def plot_test_imputation(df_test, title, field,st,ed,mse):
    """ Plots the time serie to test the imputation algorithm
            Parameters:
                    df_test(dataFrame): dataFrame that contains the original
                                        data and the data imputed
                    title(string): the title of the plot png file
                    field(string): the field we want to plot
                    st(string): start date
                    ed(string): end date
                    mse(float): root mean square error
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    df_test.plot(ax=ax, fontsize=15)
    unit = unit_field(field)
    ax.set_ylabel(unit, fontsize=15)
    ax.set_xlabel("Date", fontsize=15)
    ax.set_title("Test of the imputation algorithm ",
                 fontsize=15)
    plt.text(1.2,0.6,"start_date="+st,horizontalalignment='center',
     verticalalignment='center', transform = ax.transAxes)
    plt.savefig("results_png/{}.png".format(title))


def index(df,st,ed):
    """Calculates index of st and ed in the df 
        Parameters:
                    df(dataFrame): dataFrame that contains the original
                                   data 
                    st(string): start date
                    ed(string): end date
        Returns:
                s(int):index of start date
                l(int):length between the start date and the end date 
    """
    lis=np.arange(0,df.shape[0])
    df['col_index'] = np.array(lis)
    s=int(df.loc[st,'col_index'])
    l=int(df.loc[ed,'col_index']-s)
    df=df.drop(columns=['col_index'],inplace=True)
    return s,l

def calculate_execution_time(start_time):

    end_time = time.time()
    return end_time - start_time