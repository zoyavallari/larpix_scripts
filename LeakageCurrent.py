import pandas as pd
import h5py
import matplotlib.pyplot as plt
import plotly
import chart_studio
import chart_studio.plotly as py
import plotly.graph_objs as go

chip_key_value = b'1-1-10'
config_write_packet = 2
data_packet = 0
global_threshold_register = 32

output_plot_name = "LeakageCurrent_new.html"

def col_filter(d, col, value):
    " Filter DataFrame d where col equals value"
    d_temp = d.loc[d[col] == value]
    d_temp = d_temp.reset_index()
    return d_temp

def setGlobalThresholdColumn(d):
    'Filling values for the global_threshold column. Removing config packet rows.'
    d['global_threshold'] = None
    register_value_temp = None
    for i in d.index:
        if(d.loc[i,'type'] == config_write_packet):
            register_value_temp = d['value'][i]
        else:
            d.loc[i,'global_threshold'] = register_value_temp
    d = d.loc[d['type'] == data_packet]
    d = d.reset_index(drop = True)
    return d

def calcDeltaTime(d):
    '''Calculating time difference between successive rows. 
    Removing any packet after time rollover or if the global threshold changes'''
    d['dt'] = 0
    d['dgt'] = -1
    l = len(d.timestamp)
    for i in range (1,l-1):
        time_diff = float(d.loc[i, 'timestamp']) - (d.loc[i-1, 'timestamp'])
        d.loc[i, 'dt'] = time_diff
        d.loc[i,'dgt'] = d.loc[i, 'global_threshold'] - d.loc[i-1, 'global_threshold']

    indexNames = d[(d['dt'] <= 0) | (d['dgt'] != 0)].index
    d.drop(indexNames , inplace=True)
    d.drop(columns=['dgt'], inplace=True)
    d = d.reset_index(drop = True)
    return d

def calcAbsTime(d):
    ''' Add successive dts to create x axis for plotting'''
    d['t_abs'] = 0
    for i in range (1,d.shape[0]):
        if(d.loc[i, 'global_threshold'] - d.loc[i-1, 'global_threshold'] > 0):
            d.loc[i,'t_abs'] = 0 
        else:
            d.loc[i,'t_abs'] = d.loc[i-1,'t_abs'] + d.loc[i,'dt']
    d['t_abs'] = d['t_abs']/5000 # convert to nanosec
    return d


def addDummyRows(df, threshold_value):
    ''' Solely to make the plot pretty. No physics reason to add this dummy row.
    Adds a dummy row in data to make the plot line come back to the base of y axis'''
    df2 = pd.DataFrame(columns = df.columns)
    line = pd.DataFrame({"t_abs": 0, 
                          "adc_counts": 128, 
                          "global_threshold": threshold_value},
                          index=[0])
    df2 = pd.concat([df2, line], ignore_index=True).reset_index(drop=True)
    
    for i in df.index:
        line = pd.DataFrame({"t_abs": df.loc[i,'t_abs'] + 0.0001, 
                          "adc_counts": 128, 
                          "global_threshold": threshold_value},
                          index=[df2.tail(1).index + 2]) 
        df2 = pd.concat([df2, df.loc[[i]], line], ignore_index=True).reset_index(drop=True)
    return df2

def plot_interactive(data, filename, title, x_label, y_label, group_name, add_dummy_flag):
    '''Plotting function '''
    # Removing rows with t_abs 0 for plotting 
    indexNames = data[(data['t_abs'] == 0)].index
    data.drop(indexNames , inplace=True)
    data = data.reset_index(drop = True)
    
    layout = go.Layout(title= title,
                       xaxis= dict( title= x_label),
                       yaxis=dict( title= y_label),
                       paper_bgcolor='rgb(233,233,233)',
                       plot_bgcolor='rgba(0,0,0,0)'
                      )
    plot_df_list = []
    for col in data[group_name].unique():
        data_temp = data.loc[data[group_name] == col]
        data_temp = data_temp.reset_index(drop = True)
        if (add_dummy_flag):
            data_temp = addDummyRows(data_temp, col)

        plot_df_list.append({ 'x': data_temp[x_label],
                   'y': data_temp[y_label],
                   'name': 'global_threshold '+ str(col),
                   'mode':'lines',
                   'line': dict(dash='dot'),
                   })
        
    fig = go.Figure(
        data = plot_df_list, # data_temp,
        layout = layout
                   )
         
    # Set axes ranges
    fig.update_xaxes(range=[0, 200])
    fig.update_yaxes(range=[128, 255])

    fig.update_layout(title='Leakage Current',
                   xaxis_title='Time (in ms)',
                   yaxis_title='ADC Count')
    
    plotly.offline.plot(fig,
                        filename=filename,
                        auto_open=False)

def main():

    data = h5py.File('/Users/zoya/work/dune/larpix/data/Sep19_LeakageCurrent/datalog_2019_09_19_17_02_10_PDT_.h5')
    print("File contains {}".format(list(data.keys())))
    data = data['packets'] 
    data = pd.DataFrame(data[0:len(data)])

    # Filtering Data
    data = data[(data['type'] == data_packet) | 
             ((data['type'] == config_write_packet) & (data['register'] == global_threshold_register))]
    data = data.reset_index(drop = True)
    #print(data.shape)
    data = setGlobalThresholdColumn(data) 
    #print(data.head())
    data = calcDeltaTime(data)
    #print(data.head())
    data = calcAbsTime(data)
    #print(data.head())

    #data.to_csv("your_csv.csv")

    plot_interactive(data, output_plot_name, "Leakage Current", "t_abs","adc_counts","global_threshold", True)
    print("{} was written!". format(output_plot_name))

if __name__ == '__main__':
    main()
