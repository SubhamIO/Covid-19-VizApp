import os
import pandas as pd
import pickle
import bs4 as bs
import requests
from sklearn import preprocessing
import folium
import json
from flask import Flask, request, jsonify, render_template


import flask
app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/index')
def index():
    return flask.render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():

    os.chdir('/Users/subham/Desktop/COVID19Viz')
    # STEP 1 : Scrape data from MOFHW and store thm in DataFrame
    url = 'https://www.mohfw.gov.in/'
    # make a GET request to fetch the raw HTML content
    web_content = requests.get(url).content
    # parse the html content
    soup = bs.BeautifulSoup(web_content, "html.parser")
    # remove any newlines and extra spaces from left and right
    extract_contents = lambda row: [x.text.replace('\n', '') for x in row]
    # find all table rows and data cells within
    stats = []
    all_rows = soup.find_all('tr')
    for row in all_rows:
        stat = extract_contents(row.find_all('td'))
    # notice that the data that we require is now a list of length 5
        if len(stat) == 5:
            stats.append(stat)
    #now convert the data into a pandas dataframe for further processing
    new_cols = ["Sr.No", "States/UT","Confirmed","Recovered","Deceased"]
    state_data = pd.DataFrame(data = stats, columns = new_cols)

    # STEP 2 : Converting them to list for later use
    states = state_data['States/UT'].values.tolist()
    confirmed = state_data['Confirmed'].values.tolist()
    recovered = state_data['Recovered'].values.tolist()
    dead = state_data['Deceased'].values.tolist()

    state_data['Confirmed'] = state_data['Confirmed'].map(int)
    state_data['Recovered'] = state_data['Recovered'].map(int)
    state_data['Deceased'] = state_data['Deceased'].map(int)

    # STEP 3 : Load Latitudes and Longitudes from pickle files
    with open('latitudes_list.pkl', 'rb') as f:
        lats = pickle.load(f)

    with open('longitudes_list.pkl', 'rb') as f:
        lons = pickle.load(f)

    #STEP 4: Save them to dataFrame
    state_data['Latitudes'] = lats
    state_data['Longitudes'] = lons

    #STEP %: Create map object
    m = folium.Map(location=[21, 78], zoom_start=12)

    # Global tooltip
    tooltip = 'Click For More Info'
    hotspot = 'Hotspot'

    # Create markers
    for i in range(0,32):
            state_name = states[i]
            #idx = states.index(state_name)
            confirm_cases = confirmed[i]
            recovered_cases = recovered[i]
            dead_cases = dead[i]

            #Different colors to markers depending on the count
            if int(confirm_cases)>=1000:
                color = 'darkred'
            elif int(confirm_cases)>=500 and int(confirm_cases)<1000:
                color= 'orange'
            else:
                color = 'green'


            folium.Marker([lats[i], lons[i]],popup=state_name+'\nConfirmed Cases : '+str(confirm_cases)+'\nRecovered Cases : '+str(recovered_cases)+'\nDead Cases : '+str(dead_cases),tooltip=tooltip,icon=folium.Icon(color=color)).add_to(m)

            # Let's mark the hotspots
            if int(confirm_cases)>1000:
                folium.CircleMarker(
                    location=[lats[i], lons[i]],
                    radius=30,
                    popup='Hotspots',
                    color='#428bca',
                    fill=True,
                    fill_color='#ca4242',tooltip=hotspot
                ).add_to(m)

    #STEP 6 : Generate html page
    m.save('./templates/Covid__19.html')
    return render_template('Covid__19.html')


if __name__ == '__main__':
    #app.debug = True
    #app.run()
    app.run(host='0.0.0.0', port=8080)
