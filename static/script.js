document.addEventListener('DOMContentLoaded', function() {
    // Set default value for the time range input field
    document.getElementById('time-range').value = 5;
    document.getElementById('anomaly-range').value = 5;

    // Fetch sensor data for the default time range
    fetchSensorData();
    
    // Start the interval to fetch sensor data every second
    setInterval(fetchSensorData, 1000);
});

var layout = {
    showlegend: true,
        xaxis: {
            title: 'Time'
        },
        yaxis: {
            title: 'Value'
        },
    legend: {
      x: 1,
      xanchor: 'right',
      y: 10
    }
  };

var sensorData = {
    x: [],
    y: [],
    y_pred: [],
    mode: 'lines',
    type: 'scatter'
};

// Function to fetch sensor data
async function fetchSensorData() {
    var selectedanomalyRange = document.getElementById('anomaly-range').value;
    fetchAnomalyData();
    fetch('/sensor_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({anomaly_range: selectedanomalyRange})
        })
        .then(response => response.json())
        .then(data => {
            //document.getElementById('status-value').innerText = 'Getting Sensor Value' 
            // Update sensor value
            document.getElementById('sensor-value').innerText = data.sensor_value.toFixed(2);
            document.getElementById('mae-value').innerText = data.mae.toFixed(2);
            document.getElementById('mape-value').innerText = data.mape.toFixed(2);
            document.getElementById('y_pred-value').innerText = data.y_pred_last.toFixed(2);
            
            var anomalyText = data.anomaly ? 'Detected' : 'OK';
            document.getElementById('anomaly-value').innerText = anomalyText;

            // Add new data point to the timeline
            sensorData.x.push(new Date());
            sensorData.y.push(data.sensor_value);          
            sensorData.y_pred.push(data.y_pred_last);

            // Determine marker color based on data.anomaly
            var markerColor = data.anomaly ? 'red' : 'orange';
            
            // Filter data based on selected time range
            var selectedTimeRange = document.getElementById('time-range').value;
            var currentTime = new Date();
            var fiveMinutesAgo = new Date(currentTime.getTime() - selectedTimeRange * 60000); // 5 minutes ago
            var newDataIndices = sensorData.x.reduce((indices, timestamp, index) => {
                if (timestamp >= fiveMinutesAgo) {
                    indices.push(index);
                }
                return indices;
            }, []);

            var newX = newDataIndices.map(index => sensorData.x[index]);
            var newY = newDataIndices.map(index => sensorData.y[index]);
            var newY_pred = newDataIndices.map(index => sensorData.y_pred[index]);

            // Determine marker color based on data.anomaly
            var markerColor = data.anomaly ? 'red' : 'orange';

            // Create plot with filtered data
            Plotly.newPlot('sensor-timeline', [
                { x: newX, y: newY, mode: 'lines', name: 'Sensor Value' },
                { x: newX, y: newY_pred, mode: 'markers', name: 'Predicted Sensor Value', marker: { color: markerColor } }
            ], layout);

            // Create box plot using Plotly
            var trace = {
                y: data.boxPlot,
                type: 'box'
            };

            var layout = {
                title: 'Box Plot',
                yaxis: {
                    title: 'Values'
                }
            };
            
            document.getElementById('status-value').innerText = 'Loading Box Plot' 
            Plotly.newPlot('boxPlot', [trace], layout);
            document.getElementById('status-value').innerText = '' 
        });
        
}


function fetchAnomalyData() {
    var list = document.getElementById("anomalyList");
    var existingListItems = document.getElementById("anomalyList").getElementsByTagName("li");
    var newListItems = document.createDocumentFragment();

    // Initialize a flag to track if lists are equal
    var isEqual = true;
    //document.getElementById('status-value').innerText = 'Check Anomly List Data' 
    fetch('/previous_anomaly_data')
        .then(response => response.json())
        .then(data => {
            // Determine the start index for the loop
            var startIndex = Math.max(0, data.timestamps.length - 5);
            document.getElementById('status-value').innerText = 'Anomaly List Function'

            // Loop through the last 5 data points received from the server in reverse order and create list items
            for (var i = data.timestamps.length - 1; i >= startIndex; i--) {
                var listItem = document.createElement("li");
                listItem.textContent = "Timestamp: " + data.timestamps[i] + ", y: " + data.values[i].toFixed(2) + ", y_pred: " + data.pred_values[i].toFixed(2);
                newListItems.appendChild(listItem);
            }

            //document.getElementById('status-value').innerText = 'Existing List Length: ' + existingListItems.length; 
                // Compare each item in the lists
            for (var i = 0; i < existingListItems.length; i++) {
                //document.getElementById('status-value').innerText =existingListItems[i].textContent;
                //document.getElementById('status-value').innerText = newListItems.childNodes[i].textContent;
                if (existingListItems[i].textContent !== newListItems.childNodes[i].textContent) {
                    // If any items are not equal, set the flag to false and break the loop
                    isEqual = false;
                    document.getElementById('status-value').innerText = 'Update Anomaly List' 
                    break;
                }

            }

            if (!isEqual || existingListItems.length == 0)
            {   
                // Clear any existing list items
                list.innerHTML = "";
                // Loop through the last 5 data points received from the server in reverse order and create list items
                for (var i = data.timestamps.length - 1; i >= startIndex; i--) {
                    var listItem = document.createElement("li");
                    listItem.textContent = "Timestamp: " + data.timestamps[i] + ", y: " + data.values[i].toFixed(2) + ", y_pred: " + data.pred_values[i].toFixed(2);
                    list.appendChild(listItem);
                    document.getElementById('status-value').innerText = 'Anomaly List Updated' 
                }
            }
    });

    if (!isEqual)
    {   
        // Clear any existing list items
        list.innerHTML = "";
        // Append each item from newListItems to the list
        list.appendChild(newListItems);
    }
}

// Function to fetch previously saved data
function fetchPreviousData() {
    // Fetch time range from UI
    var selectedTimeRange = document.getElementById('time-range').value;
    // Send time range to backend
    document.getElementById('status-value').innerText = 'Loading Previous Data' 
    fetch('/previous_sensor_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ time_range: selectedTimeRange})
    })
        .then(response => response.json())
        .then(data => {
            // Update sensor value
            document.getElementById('sensor-value').innerText = 'Sensor Value: ' + data.values[data.values.length - 1];

            // Update sensorData with previously saved data
            sensorData.x = data.timestamps.map(timestamp => new Date(timestamp));
            sensorData.y = data.values; 
            sensorData.y_pred = data.pred_values;  

            // Create initial plot
            Plotly.newPlot('sensor-timeline', [
                { x: sensorData.x, y: sensorData.y, mode: 'lines', name: 'Sensor Value' },
                { x: sensorData.x, y: sensorData.y_pred, mode: 'markers', name: 'Predicted Sensor Value' }
            ], layout);
          
            // Fetch new sensor data after updating the graph with previous data
            fetchSensorData();
        });
}

// Fetch previously saved data when the page loads
fetchPreviousData();

// Update sensor data and graph when the selected time range changes
document.getElementById('time-range').addEventListener('change', function() {
    // Fetch previous data with new time range
    fetchPreviousData();
});
