from flask import Flask, render_template, jsonify, request
import random
import math
import time
import pandas as pd
import datetime
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sktime.forecasting.model_selection import temporal_train_test_split
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

app = Flask(__name__)

sensor_values = {'timestamps': [], 'values': [], 'pred_values': []}
anomaly_values = {'timestamps': [], 'values': [], 'pred_values': []}

enableSaveData = False

# Counter to control when to generate noise
noise_counter = 0

def generate_sensor_data():
    global noise_counter
    # Generate noise only once every 50 times
    if noise_counter == 0:
        # Simulate noise with a random value between -1 and 1
        noise = random.uniform(-1, 1)
        # Reset counter
        noise_counter = 50
    else:
        noise = 0
        noise_counter -= 1

    # Simulate sensor value within a certain range
    sensor_value = 50 + noise * 10  # Assuming the sensor value ranges from 45 to 55
    
    # Add sinusoidal variation
    # Get the current time in seconds since the epoch
    current_time = time.time()
    sensor_value += 5 * math.sin(current_time/2)  # Adding a sinusoidal variation with amplitude 5
    return sensor_value

# Function to append sensor data with timestamp to a text file
def append_to_file(values, value, pred_value, filename):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # Get current timestamp  
    values['timestamps'].append(timestamp)
    values['values'].append(float(value))
    values['pred_values'].append(float(pred_value))
    if enableSaveData:
        with open(filename, 'a') as f:
            f.write(timestamp + ';' + str(value) + ';' + str(pred_value)+ '\n')
    return sensor_values

def append_to_file(values, value, pred_value, filename, max_lines):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # Get current timestamp  
    values['timestamps'].append(timestamp)
    values['values'].append(float(value))
    values['pred_values'].append(float(pred_value))
    
    if enableSaveData:
        with open(filename, 'a+') as f:
            # Check if file exceeds maximum lines
            f.seek(0)  # Move to the beginning of the file
            line_count = sum(1 for _ in f)
            if line_count >= max_lines:
                # If file exceeds maximum lines, remove the oldest lines
                lines_to_keep = line_count - max_lines + 1  # Keep one extra line for the new entry
                f.seek(0)  # Move to the beginning of the file
                lines = f.readlines()[lines_to_keep:]
                f.seek(0)
                f.truncate()
                f.writelines(lines)
        
            # Append new data
            f.write(timestamp + ';' + str(value) + ';' + str(pred_value) + '\n')
    
    return values

# Function to read previously saved sensor data from text file
def read_previous_data(time_range, filename):
    timestamps = []
    values = []
    pred_values = []
    if enableSaveData:
        with open(filename, 'r') as f:
            current_time = time.time()
            print("Current time: ",  current_time)

            cutoff_time = current_time - float(time_range) * 60  # Convert minutes to seconds
            print("Cut Off time: ",  cutoff_time)

            for line in f:
                timestamp, value, pred_value = line.strip().split(';')
            
                # Convert timestamp to float
                timestamp_ = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            
                # Convert datetime object to UNIX timestamp (float)
                timestamp_ = timestamp_.timestamp()

                # Check if the timestamp is within the time range
                if timestamp_ >= cutoff_time:
                    timestamps.append(timestamp)            
                    values.append(float(value))          
                    pred_values.append(float(pred_value))
                
    return {'timestamps': timestamps, 'values': values, 'pred_values': pred_values}

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
    #print('MAE: %.3f' % mae)
    #print('MAPE: %.3f' % mape)
    if mape > anomalyPerc: #mape
         anomalyDetected = True
    else:
         anomalyDetected = False    
    return anomalyDetected, mae, mape

def AnomalyDetectionMain(data, size, threshold):
    df = pd.DataFrame(data)
    df['timestamps'] = pd.to_datetime(df['timestamps'], format='%Y-%m-%d %H:%M:%S')
    df.set_index('timestamps', inplace=True)
    df = df.iloc[-500:]
    df.index = range(len(df))
    df.drop(columns=['pred_values'], inplace=True)
    y_train, y_test = SplitData(df, size)
    y_pred = SarimaxPrediction(df, size)
    #print(len(y_test), len(y_pred))
    anomaly, mae, mape = ErrorEstimation(y_test, y_pred, threshold)
    return anomaly, y_pred, mae, mape, df

# Route to provide sensor data
@app.route('/sensor_data', methods=['POST'])
def sensor_data():
    global sensor_values
    global anomaly_values
    df = pd.DataFrame()
    sensor_value = generate_sensor_data()
    size = 5

    try:
        threshold =  float(request.json.get('anomaly_range'))*0.01 * 2 #The MAE is from the middle, the threshold is the double, therefore, divide it by two
    except:
        threshold = 0.1  # Define threshold for anomaly detection
    
    try:
        anomaly, y_pred, mae, mape, df = AnomalyDetectionMain(sensor_values, size, threshold)
        y_pred_last = float(y_pred.iloc[-1])
        if anomaly:
           anomaly_values = append_to_file(anomaly_values, sensor_value, y_pred_last, 'anomalies_sensor_1.txt', 500)
    except:
        y_pred_last = sensor_value
        mae = 0
        mape = 0
    
    sensor_values = append_to_file(sensor_values, sensor_value, y_pred_last, 'sensor_data_1.txt', 500)  # Append sensor data to text file

    return jsonify(sensor_value=sensor_value, mae = mae, mape = mape, y_pred_last = y_pred_last, anomaly = anomaly, boxPlot = df['values'].tolist())

# Route to provide previously saved sensor data
@app.route('/previous_sensor_data', methods=['POST'])
def previous_sensor_data():
    global sensor_values
    #print("Previous Sensor Data")
    time_range = request.json.get('time_range')
    #print("time range: ", time_range)
    if enableSaveData:
        sensor_values = read_previous_data(time_range,'sensor_data_1.txt')
    return jsonify(sensor_values)

# Route to provide previously saved sensor data
@app.route('/previous_anomaly_data')
def previous_anomaly_data():
    global anomaly_values
    if enableSaveData:
        anomaly_values = read_previous_data(9999,'anomalies_sensor_1.txt')
    #print(anomaly_values)
    return jsonify(anomaly_values)

# Route to render the HTML template
@app.route('/')
def index():
    return render_template('index.html')

# Main function
def main():
    app.run(debug=True, port=5001, use_reloader=False)

if __name__ == "__main__":
    main()