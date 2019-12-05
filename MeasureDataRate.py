import pandas as pd
import h5py
import plotly
import chart_studio
import chart_studio.plotly as py
import plotly.graph_objs as go
import csv
import numpy as np
from collections import Counter


filenames  = dict(
                chan5 ='/Users/zoya/work/dune/larpix/data/data_rate/datalog_2019_09_22_18_21_22_PDT_C5_1Hz_10for10.h5',
                chan12 = '/Users/zoya/work/dune/larpix/data/data_rate/datalog_2019_09_22_18_24_10_PDT_C12_1Hz_10for10.h5',
                chan18 = '/Users/zoya/work/dune/larpix/data/data_rate/datalog_2019_09_22_18_26_55_PDT_.C18_1Hz_10for10.h5',
                chan26 = '/Users/zoya/work/dune/larpix/data/data_rate/datalog_2019_09_22_18_04_35_PDT_.C26_1Hz_10for10.h5'
                )

mean = dict(chan5 = None, chan12 = None, chan18 = None, chan26 = None)
sdev = dict(chan5 = None, chan12 = None, chan18 = None, chan26 = None)

def getData(filename):
    d = h5py.File(filename)
    d = d['packets']
    d = pd.DataFrame(d[0:len(d)])
    return d

def getMeanAndStd(packet_list, chan):
    global mean, sdev
    m = round(np.mean(packet_list),2)
    sd = round(np.std(packet_list),2)
    print("Mean and Std of {} are {} and {}".format(chan,m,sd))
    mean[chan] = m
    sdev[chan] = sd

def countDataPackets(data,chan):
    count = 0
    packet_list = []
    for i in data.index[1:]:
        if(data.loc[i,'type'] == 4):
            packet_list.append(count) 
            count = 0
        else:
            count = count+1
    getMeanAndStd(packet_list, chan)
    d = pd.DataFrame.from_dict(dict(Counter(packet_list)), orient='index')
    d.columns = [chan]
    return d.sort_index()

def plot_interactive(data, filename):
    '''Doc String'''
    layout = go.Layout(title='Data Rate = 1 Hz',
                   xaxis_title='# of Data Packets',
                   yaxis_title='Frequency',
                   paper_bgcolor='rgb(233,233,233)',
                   plot_bgcolor='rgba(0,0,0,0)'
                      )
    fig = go.Figure(data = [{ 'x': data[data[col].notnull()].index,
                              'y': data[data[col].notnull()][col],
                              'name': "{} - mean:{} , std:{}".format(col,mean[col],sdev[col]),
                              'mode':'lines+markers',
                              'line': dict(dash='dash')}  for col in data.columns],
                    layout = layout
                   )         
    plotly.offline.plot(fig,
                       filename=filename,
                        auto_open=False)

def main():
    chans = ['chan5','chan12','chan18','chan26']
    data_rate_freq = pd.DataFrame()
    for chan in chans:
        data = getData(filenames[chan])
        if(data_rate_freq.empty):
            data_rate_freq = countDataPackets(data, chan)
        else:
            data_rate_freq = pd.concat([data_rate_freq, countDataPackets(data, chan)],axis =1, sort = True)
        
    #print(data_rate_freq)

    plot_interactive(data_rate_freq, "datarate_1Hz_new.html" )


if __name__ == '__main__':
    main()




