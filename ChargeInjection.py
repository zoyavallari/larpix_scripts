import pandas as pd
import h5py
import plotly
import chart_studio
import chart_studio.plotly as py
import plotly.graph_objs as go
import csv
import numpy as np

config_write_packet = 2
data_packet = 0
adc_count_register = 46 #TODO Check name

filenames  = dict(
                amp5 = '/Users/zoya/work/dune/larpix/data/charge_injection/datalog_2019_09_20_20_33_05_PDT_.h5',
                amp10 = '/Users/zoya/work/dune/larpix/data/charge_injection/datalog_2019_09_20_20_24_41_PDT_.h5',
                amp15 = '/Users/zoya/work/dune/larpix/data/charge_injection/datalog_2019_09_20_20_22_30_PDT_.h5'
                )
adc_filter = dict(amp5 = 175, amp10 = 200, amp15 = 225)
mean = dict(amp5 = None, amp10 = None, amp15 = None)
sdev = dict(amp5 = None, amp10 = None, amp15 = None)

def getData(filename):
    d = h5py.File(filename)
    d = d['packets']
    d = pd.DataFrame(d[0:len(d)])
    d = d[(d['type'] == data_packet) | ((d['type'] == config_write_packet) & 
                                        (d['register'] == adc_count_register))]
    d = d.reset_index(drop = True)
    return d

def col_filter(d,filter_col, filter_value):
    d_temp = d.loc[d[filter_col] == filter_value]
    d_temp = d_temp.reset_index()
    return d_temp

def calcMeanSTD(d,amp):
    global mean, sdev
    print("Applying adc filter of testpulse {} to {}".format(adc_filter[amp], amp))
    d = d.loc[d['adc_counts'] > adc_filter[amp]]
    m = round(np.mean(d['adc_counts']),2)
    std = round(np.std(d['adc_counts']),2)
    print("Mean and SD of testpulse {} is {} and {}".format(amp,m,std))
    mean[amp] = m
    sdev[amp]= std
    
def plot_interactive(data, filename):
    '''Doc String'''
    layout = go.Layout(title='Charge Injection; Channel 26',
                   xaxis_title='ADC Count',
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
         
    fig.update_xaxes(range=[160, 250])
    plotly.offline.plot(fig,
                       filename=filename,
                        auto_open=False)


def main():
    amp_list = ['amp5','amp10','amp15']
    data_agg = pd.DataFrame() #this data frame will save the frequency of adc_counts

    for testpulse_amp in amp_list:
        data = getData(filenames[testpulse_amp])
        print("Number of rows in {} data = {}".format(testpulse_amp,data.shape[0]))
        ADC_list = []
        for i in data.index[1:]:
            if((data.loc[i,'type'] == data_packet) & (data.loc[i-1, 'type'] == config_write_packet)):
                ADC_list.append(i)
        data = data.loc[ADC_list]
        # Calculating the distribution of adc_counts
        if(data_agg.empty):
            data_agg = data.groupby('adc_counts').agg(freq = ('adc_counts','count'))
        else:
            data_agg = pd.concat([data_agg, data.groupby('adc_counts').agg(freq = ('adc_counts','count'))], axis =1, sort = True)

        calcMeanSTD(data, testpulse_amp)
    
    data_agg.columns = amp_list #renaming columns

    #Plot away!
    plot_interactive(data_agg, "chargeinjection26_new.html" )

if __name__ == '__main__':
    main()
