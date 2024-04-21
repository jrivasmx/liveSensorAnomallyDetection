https://docs.docker.com/language/python/containerize/

$ docker init

? What application platform does your project use? Python
? What version of Python do you want to use? 3.11.4
? What port do you want your app to listen on? 5001
? What is the command to run your app? 
default: python3 -m flask run --host=0.0.0.0
use: python3 -m flask run --host=0.0.0.0 --port=5001

$ docker compose up --build

note : 
time
statsmodels.tsa.statespace.sarimax
sktime.forecasting.model_selection
sklearn.metrics

The 'sklearn' PyPI package is deprecated, use 'scikit-learn'

$ docker compose up --build -d