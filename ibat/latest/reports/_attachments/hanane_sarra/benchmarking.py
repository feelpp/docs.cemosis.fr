import sys
import subprocess
import pandas as pd
import json
import timeit
import argparse
import numpy as np
import time
import csv
from tools import *
from random import sample
from pandas.io.json import json_normalize
import scipy.stats as sc
import matplotlib.pyplot as plt

""" ***Initialize some parameters*** """
interval = 60
sampling_period = []
value_elm = []
number_execTimeit = 1
file = 0
data_algo = ""
verbose = False
start_date = "2019-01-01T00:00:00Z"
end_date = "2019-02-01T00:00:00Z"
zone_with_no_data = []


def print_verbose(msg='\n'):
    if verbose:
        print(msg)


def execScript(option_cmd, freq, value_option,
               start_date, end_date, data_algo="", ignore_error=True):

    ''' Executes the command associated with the ibat_query.py script.
        Parameters:
            option_cmd(str): node or zone
            freq(str): list of sambling periods
            value_option(str): list  of nodes/zones
            start_date(str): the start date for the data export
            end_date(str): the end date for the data export
            data_algo(str): choose between \"impute\" or \"impute and smooth\"\
                             data series
    '''
    cmd = '''python3 ibat_query.py --field "temperature" "humidity" "light"\
             "sound"  "pir" -sd {} -ed {} -in {} -eh'''.format(start_date,
                                                           end_date, freq)

    if option_cmd == 'node':
        cmd = cmd+(''' -c {}'''.format(value_option))
    elif option_cmd == 'zone':
        cmd = cmd+(''' -z {} '''.format(value_option))
    if data_algo == 'impute':
        cmd = cmd + ' --impute '
    elif data_algo == 'smooth':
        cmd = cmd + ' --impute --smooth'

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         shell=True)
    out, err = p.communicate()

    if p.returncode != 0:
        print_verbose("Error :" + str(err.decode()))
        print_verbose()
        print_verbose(out.decode())
        if not ignore_error:
            raise Exception


def compute_time_elm():
    ''' Calculates the execution time of the function execScript
        Returns:
            execute_time_elm(matrix of float): contains the execution time of\
                                            the function according to the\
                                            number of elements(nodes or zones)
                                            and the sambling periods
    '''

    list_elm = ''
    random_elm = []
    if option_cmd == 'node':
        size_matrix = nbr_elm / 4 if nbr_elm%4==0 else (nbr_elm/4)+1 
    else:
        size_matrix = nbr_elm
    
    execute_time_elm = np.zeros((int(size_matrix), len(sampling_period)))
    sum_execute_time_elm = np.zeros((int(size_matrix), len(sampling_period)))

    if option_cmd == 'node':
        value_elm = [val for val in (range(1, 70))]
        value_elm.extend([81, 82])
        for p in range(1, number_execTimeit+1):
            random_elm = sample([value for value in value_elm], k=nbr_elm)
            print_verbose("Number execution command : {}".format(p))
            print_verbose("List of random {}s : {}".format(option_cmd,
                                                           random_elm))
            list_elm = ""
            i = 0

            while(random_elm != []):
                print_verbose("Progress {:.0f}% ...".format(i*100/size_matrix))
                for _ in range(0,4):
                    if random_elm != []:
                        list_elm = list_elm + str(random_elm.pop(0)) + ","
                
                for j, freq in enumerate(sampling_period):
                    sum_execute_time_elm[i, j] = sum_execute_time_elm[i, j] + timeit.timeit(
                            stmt="execScript('{}','{}','{}','{}',\
                            '{}','{}')".format(option_cmd, freq, list_elm,
                                            start_date, end_date,
                                            data_algo),
                            setup="from __main__ import execScript",
                            number=1)
                    execute_time_elm[i, j] = sum_execute_time_elm[i, j] / p
                i+=1
            

    elif option_cmd == 'zone':
        value_elm = list(range(1, nbr_elm + 1))
        print_verbose("List of {}s : {}".format(option_cmd, value_elm))
        for i, elm in enumerate(value_elm):
            print_verbose("Progress {:.0f}% ...".format(((i*100)/(nbr_elm))))
            for j, freq in enumerate(sampling_period):
                execute_time_elm[i, j] = timeit.timeit(
                        stmt="execScript('{}','{}','1-{}','{}',\
                        '{}','{}')".format(option_cmd, freq, elm, start_date,
                                           end_date, data_algo),
                        setup="from __main__ import execScript",
                        number=number_execTimeit)
    return execute_time_elm


def compute_time_date(list_dates, list_zones, start_date, end_date,
                      data_algo):
    ''' Calculates the execution time of the function execScript
        Parametres:
            list_dates(str): list of the different dates
            value_arg(int): the zone to request
            start_date(str): the start date for the data export
            end_date(str): the end date for the data export
            data_algo(str): choose between \"impute\"or\"impute and smooth\" \n
                            data series
    '''
    execute_time_month = np.zeros((len(list_dates), len(zone_to_request)))
    for i, elm in enumerate(list_dates):
        print_verbose("Progress {:.0f}% ...".format(((i*100)/len(list_dates))))
        for j, zone in enumerate(zone_to_request):
            try:
                execute_time_month[i, j] = (timeit.timeit(
                                stmt="execScript('zone','{}','{}','{}','{}',\
                                '{}',False)".format(int(sampling_period[0]),
                                                    zone, start_date, elm,
                                                    data_algo),
                                setup="from __main__ import execScript",
                                number=number_execTimeit))
            except Exception:
                if zone not in zone_with_no_data:
                    zone_with_no_data.append(zone)
                continue

    deleted_zones = 0
    for index, zone in enumerate(zone_to_request):
        if zone in zone_with_no_data:
            execute_time_month = np.delete(execute_time_month,
                                           index - deleted_zones, 1)
            deleted_zones += 1

    for zone in zone_with_no_data:
        zone_to_request.remove(zone)

    return execute_time_month


def fileCsv(name_col, value_col, name_line, value_line, file, tab_values):
    ''' Create the csv file that contains the tab_value.
        Parameters:
            name_col(str): name of tthe csv first colomn.
            value_col(list of str): list of the columns values.
            value_line(list of str): list of the lines values.
            file(str): name of the csv file to create.
            tab_values(tab of float): contains the execution time of\
                                      execScript function.
    '''
    csv_first_col = []
    csv_first_line = []

    if name_col == "month":
        for i, date in enumerate(value_col):
            csv_first_col += [str(i+1)+" {}s".format(name_col)]
    else:
        if name_col == "zone":
            for i in range(1, value_col+1):
                csv_first_col += [str(i)+" {}s".format(name_col)]
        elif name_col == "node":
            for i in value_col:
                csv_first_col += [str(i)+" {}s".format(name_col)] 

    csv_first_line = ['Number of '+name_col+'s']+[name_line + str(val) for val in value_line]
    with open('results_csv/{}.csv'.format(file), 'w', newline='') as my_csv:
        writer = csv.writer(my_csv)
        writer.writerow(csv_first_line)
        n = 0
        for row in tab_values:
            writer.writerow([csv_first_col[n]]+[row[i] for i in range(
                len(value_line))])
            n = n+1


def fct_plot(file, name_col, name_option, unit=""):
    ''' Plot the exuction time of the commman according to different parameters
        Parameters:
            file(str): name of the csv file to plot
            name_col(str): list of the columns
            name_option(str): node,zone or month
            unit(str): the unit of the abscess x
    '''

    name_col = []
    fig, ax = plt.subplots()

    my_csv = pd.read_csv("results_csv/{}.csv".format(file))
    x = np.linspace(1, my_csv.shape[0]*4, my_csv.shape[0])
    name_col += [my_csv.columns[i] for i in range(1, my_csv.shape[1])]

    if name_col == []:
        print_verbose('No data to plot')
        exit(1)
    tab = []
    for i in name_col:
        ax.plot(x, my_csv[str(i)], label=str(i) + unit)
        tab.append(my_csv[str(i)])
    plt.grid(True)
    droite=sc.linregress(x,tab)
    coefficient=droite.slope
    oorigine=droite.intercept
    Umodele=coefficient*x+oorigine
    plt.text(31,6700,r'$y = {} x + {}$'.format(round(coefficient,2),round(oorigine,2)), fontsize=14, color='r')
    plt.plot(x,Umodele,color='red',label='regression line')
    y_max = my_csv.max(axis=1, numeric_only=True)
    y_min = my_csv.min(axis=1, numeric_only=True)
    plt.xticks(np.arange(x.min(), x.max()+1, 5))
    plt.yticks(np.arange(y_min.min(), y_max.max(), 800))
    ax.set_ylabel('Execution time(s)')
    ax.set_xlabel('Number of {}s'.format(name_option))

    if data_algo == 'smooth':
        ax.set_title("""Total execution time (query, imputation, smoothing)""")
    elif data_algo == 'impute':
        ax.set_title("""Execution time of the imputation algorithm""")
    else:
        ax.set_title("""Execution time according to the number of {}s
                         """.format(name_option))

    ax.legend()
    plt.savefig("results_png/{}.png".format(file))


if '__main__':

    """ *** Parameters *** """
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--option_cmd", choices=['node', 'zone'],
                        required=True,
                        help="""choose benchmarking option between node\
                        or zone.""")

    parser.add_argument("-in", "--interval_periods", default=interval,
                        help="""set the sampling periods in minutes.
                        \nformat:\"min-max\": sampling periods interval
                        \nformat:\"value,value,...,value\"sampling periods list
                        \nformat\"min-max,value,...\":sampling periods interval
                        and sampling periods list""")

    parser.add_argument("-n", "--number_elm", type=int,
                        help="number of nodes or zones to request")

    parser.add_argument("-p", "--number_execTimeit", type=int,
                        default=number_execTimeit,
                        help="""set the number of times each query is repeated\
                        before its time execution is evaluated.\n
                        Example: number_execTimeit = 10 : each query runs\
                        10 times before its execution time is evaluated""")

    parser.add_argument("-f", "--create_file", type=int, default=file,
                        choices=[0, 1], help="""set create file choices.
                        \n default : 0 create new file.csv
                        \n 1 use old file.csv """)

    parser.add_argument("-z", "--zones",
                        help="""set the zones to request""")

    parser.add_argument("-sd", "--start_date", default=start_date,
                        help="""the start date for the data export in the\
                        format \"yyyy-mm-ddTHH:mn:ssZ\"""")

    parser.add_argument("-ed", "--end_date", default=end_date,
                        help="""the end date for the data export in the format
                        \"yyyy-mm-ddTHH:mn:ssZ\" """)

    parser.add_argument("--data_algo", choices=['impute', 'smooth'],
                        help="""choose between data algorithms
                        \n impute:impute missing values in the time series
                        \n smooth:smooth the times series""")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="""Verbosity""")

    args = parser.parse_args()

    """ ***Conditions on parameters*** """
    if args.zones and args.number_elm:
        parser.error("must choose between --number_elm and --zones,\
                      not both of them.")

    if args.zones and args.option_cmd == "node":
        parser.error("--zones requires --option_cmd zone")

    if args.zones and not(args.start_date or args.end_date):
        parser.error("--zones requires --start_date and --end_date")

    if args.start_date and not (args.end_date):
        parser.error("--start_date requires --end_date.")

    if args.end_date and not(args.start_date):
        parser.error("--end_date requires --star_date.")

    if args.number_elm:
        nbr_elm = args.number_elm
    elif args.zones:
        zones = args.zones
        zone_to_request = string_elm_to_list(zones, 14)

    if args.number_execTimeit:
        number_execTimeit = args.number_execTimeit

    if args.create_file:
        file = args.create_file

    if args.data_algo:
        data_algo = args.data_algo

    if args.start_date:
        start_date = args.start_date
    if args.end_date:
        end_date = args.end_date

    verbose = args.verbose
    sampling_period = string_elm_to_list(args.interval_periods, 1000000)
    option_cmd = args.option_cmd

    # Begin of program
    print_verbose()
    print_verbose("Benchmarking of response time to request DB, with options:")
    if args.number_elm:
        print_verbose("Calculation of the execution time in relation to the number of {} for each sampling period".format(option_cmd))
        print_verbose("Number of {}s : {}".format(option_cmd, nbr_elm))
    elif args.zones:
        print_verbose("Calculation of the execution time in relation to the number of months for each zone")
        print_verbose("For zones : {}".format(zone_to_request))
    print_verbose("Sampling periods : {}".format(sampling_period))
    print_verbose()
    print_verbose("Start date : {}".format(start_date))
    print_verbose("End date : {}".format(end_date))
    print_verbose("Prediction data algorithm : {}".format(data_algo))
    print_verbose("Import existing csv file: {}".format("True" if file == 1 else "False"))
    print_verbose("Number of execution command: {}".format(number_execTimeit))
    print_verbose()

    # Ploting the execution time according to the number of elmts
    if not args.zones:
        if file == 0:
            print_verbose("Calculating...A plot will be displayed in few time")
            execute_time_elm = compute_time_elm()
            print_verbose("Progress 100% ...")
            
            mult4 = 1
            value_col = []
            nbr_elm_tmp = nbr_elm
            while (nbr_elm_tmp > 4):
                value_col.append( mult4 * 4 )
                mult4+=1
                nbr_elm_tmp -= 4
            value_col.append(nbr_elm)

            fileCsv(option_cmd, value_col ,"sampling_period-", sampling_period,
                    'execute_time_elm', execute_time_elm)
        fct_plot('execute_time_elm', sampling_period, option_cmd, "min")

    else:
        # Ploting the execution time according to the number of months
        print_verbose("Calculating ... A plot will be displayed in few time.")
        list_months = dates_to_list_month(start_date, end_date)
        execute_time_month = compute_time_date(list_months, zone_to_request,
                                               start_date, end_date, data_algo)
        print_verbose("Progress 100% ...")
        fileCsv("month", list_months, option_cmd, zone_to_request,
                'execute_time_month', execute_time_month)
        fct_plot('execute_time_month', zone_to_request, "month")
