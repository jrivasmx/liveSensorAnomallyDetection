from flask import Flask, render_template, jsonify
import random
import time
import pandas as pd
import datetime
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sktime.forecasting.model_selection import temporal_train_test_split
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

sensor_values = {'timestamps': [], 'values': []}

# Function to read previously saved sensor data from text file
def read_previous_data(filename):
    timestamps = []
    values = []
    with open(filename, 'r') as f:
        for line in f:
            timestamp, value = line.strip().split(';')
            timestamps.append(timestamp)            
            values.append(float(value))
            sensor_values['timestamps'].append(timestamp)
            sensor_values['values'].append(float(value))
                
    return {'timestamps': timestamps, 'values': values}

# Function to generate simulated sensor data
def generate_sensor_data():
    # Simulate noise with a random value between 0 and 1
    noise = random.uniform(0, 1)
    # Simulate sensor value within a certain range
    sensor_value = 50 + noise * 10  # Assuming the sensor value ranges from 50 to 60
    return sensor_value

def append_to_file(value, filename):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # Get current timestamp  
    sensor_values['timestamps'].append(timestamp)
    sensor_values['values'].append(float(value))
    with open(filename, 'a') as f:
        f.write(timestamp + ';' + str(value) + '\n')

#============================
# Prediction 
#============================
def SplitData(y, size):    
    # Splitting dataset (test dataset size is last 12 periods/months)    
    y_train, y_test = temporal_train_test_split(y, test_size=size)
    return y_train, y_test

#============================
# Sarimax Prediction 
#============================
def SarimaxPrediction(y_train, size):
    model = SARIMAX(y_train, order=(1, 1, 1), seasonal_order=(1,0,1,size)) #was 12
    model_fit = model.fit()
    y_pred = model_fit.predict(start=len(y_train), end=len(y_train)+size-1, exog=None, dynamic=True) #was 11
    return y_pred

#============================
# Error Estimations 
#============================
def ErrorEstimation(y_test, y_pred, anomalyPerc):
    y_test = y_test.values.flatten()
    mae = mean_absolute_error(list(y_test), list(y_pred)) #was y_pred[signal]
    mape = mean_absolute_percentage_error(list(y_test), list(y_pred))
    print('MAE: %.3f' % mae)
    print('MAPE: %.3f' % mape)
    if mape > anomalyPerc: #mape
         anomalyDetected = True
    else:
         anomalyDetected = False    
    return anomalyDetected


sensor_values  = read_previous_data('sensor_data_1.txt')
size = 5

while True:
    sensor_value = generate_sensor_data()
    #print("sensor value: ", sensor_value)   
    time.sleep(1) # Sleep for 5 seconds
    append_to_file(sensor_value, 'sensor_data_1.txt')  # Append sensor data to text file
    data = pd.DataFrame(sensor_values)
    data['timestamps'] = pd.to_datetime(data['timestamps'], format='%Y-%m-%d %H:%M:%S')
    data.set_index('timestamps', inplace=True)
    data = data.iloc[-500:]
    data.index = range(len(data))
    y_train, y_test = SplitData(data, size)
    y_pred = SarimaxPrediction(y_train, size)
    #print(len(y_test), len(y_pred))
    anomaly = ErrorEstimation(y_test, y_pred, 0.1)