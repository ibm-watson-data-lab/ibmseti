#IBM SETI

Code produced in partnership between the SETI Institute of Mountain View, CA and IBM. 


### Requirements
  requests


## Privacy Warning

We send usage information of this library when you import the package and make particular calls. 
This helps us to understand the popularity of this library. If you wish to turn this off, 
you may do so by

  ```python
  ibmseti.callback.disable()
  ```

In particular, we collect the following environment variables (which are set in your IBM Spark service)

  * SPARK_TENANT_ID
  * EGOSC_SERVICE_NAME
  * SPARK_EGO_CONSUMER
  * SPARK_IDENT_STRING
  * EGO_MASTER_LIST_PEM


## Example User Code

### Installation

    pip install --user ibmseti


### Setup

  ```python
  import ibmseti

  ```

### Select an Interesting Target

Use [a source](http://phl.upr.edu/projects/habitable-exoplanets-catalog)
to find interesting expolanet coordinates.

You'll need to know the right ascension (RA, in hours from 0.0 to 24) and declination 
(DEC, in degrees from -90.0 to 90.0) of your exoplanet.

All RA/DEC coordinates are references from the J2000 equinox. 

### Query the SignalDB

The Allen Telescope Array (ATA), the source of data for this project,
records radio signals while pointing toward particular celestial coordinates, 
usually targeting a known exoplanet.

The SignalDB contains the preliminary analysis of that raw data. 
You can use these rows of data to further refine your search. 

In the next step you'll use the SignalDB to get the raw data for "Candidate" signals for
a particular target. To do so, the `requests` library will be used to query our data server.
This query has been built into our data server. You only need to know the celestial 
coordinates of your target. A query to the database will be made to return the raw data
for Candidate signals for those coordinates (within a range of 0.01 hours and 0.01 degrees)

First, we can check to see if we have any data for a particular exoplanet. 

Let's look up Kepler 1229b, found here http://phl.upr.edu/projects/habitable-exoplanets-catalog.
This candidate has an Earth similarity index (ESI) of 0.73 (Earth = 1.0, Mars = 0.64, Jupiter = 0.12) 
and is 770 light-years away. It is the 5th highest-ranked planet by ESI.

You can take a look at this object in the sky: http://simbad.cfa.harvard.edu/simbad/sim-id?Ident=%408996422&Name=KOI-2418.01&submit=submit

The ATA only records the celestial coordinates toward which it was pointing during data acquisition,
and not any information about the exoplanet target. So, we must search our data
by a small range about those celestial coordinates.

Our data server is found at https://setigopublic.mybluemix.net. The query that returns
the RA/DEC coordinates for which we have Candidate signals is https://setigopublic.mybluemix.net/v1/coordinates/aca.
However, this will return all of the available coordinates. We can restrict the search by using 
the `ramin`, `ramax`, `decmin` and `decmax` options.

For example:

  ```python
  import requests
  RA=19.832
  DEC=46.997
  box = 0.002

  # We want this query
  # http://setigopublic.mybluemix.net/v1/coordinates/aca?ramin=19.830&ramax=19.834&decmin=46.995&decmax=46.999

  params = {
    'ramin':RA-box, 'ramax':RA+box, 'decmin':DEC-box, 'decmax':DEC+box
  }
  r = requests.get('https://setigopublic.mybluemix.net/v1/coordinates/aca',
      params = params)

  import json
  print json.dumps(r.json(), indent=1)
    ```

We get the following output:

  ```json
  {
    "returned_num_rows": 1,   
    "skipped_num_rows": 0, 
    "rows": [
      {
        "dec2000deg": 46.997, 
        "number_of_rows": 392, 
        "ra2000hr": 19.832
      }
    ], 
    "total_num_rows": 1
  }
  ```

This means we have 392 "candidate" signals recorded while observing this Earth-like planet. 

### Get Raw Data

Given a particular celestial coordinate, we can obtain all of the raw "candidate" signal data.
Again, we use our HTTP API to obtain these candidate events and the raw data associated
with them. 

The endpoint we will use is https://setigopublic.mybluemix.net/v1/aca/single.

Continuing from the example above


  ```python
  ra = r.json()['rows'][0]['ra2000hr']
  dec = r.json()['rows'][0]['dec2000deg']

  params = {'ra':ra, 'dec':dec}

  r = requests.get('https://setigopublic.mybluemix.net/v1/aca/single',
      params = params)

  print json.dumps(r.json(), indent=1)
  ```

The location of the raw data on our Softlayer Object Store account are found in 
the 'container' and 'objectname' fields. The objects are world-readable and do
not require credentials to access. 

The URL is contructed as

  https://baseurl/auth_id/container/objectname

where the `baseurl/auth_id` is

  https://dal05.objectstorage.softlayer.net/v1/AUTH_4f10e4df-4fb8-44ab-8931-1529a1035371

Searching through these results, one thing that you'll notice is that while there are 392
"candidate" signals found in the raw data, it doesn't mean there are 392 raw data files. There
will be duplicates, so you'll need to sort through them appropriately. If you do not and you use
the same raw data multiple times within a machine-learning algorithm (to extract a set of features, 
for example), you'll likely corrupt your results. 

In addition to the container and objectname of the raw data, the preliminary signal analysis
information is provided along with each file. (These are the data found in the SignalDB, described
[here]()).

You'll also notice there multiple files that point to the same SignalDB data, but with slightly
different file names. The antenna data are decomposed into left- and right-circularly polarized
signals and those data are stored in separate files; hence, the `L` and `R` components of the names.

The raw data can be attained with a HTTP request

  ```python
  cont = r.json()['rows'][0]['container']
  objname = r.json()['rows'][0]['objectname']
  base_url = 'https://dal05.objectstorage.softlayer.net/v1/AUTH_4f10e4df-4fb8-44ab-8931-1529a1035371'
  r = requests.get('/'.join([base_url, container, objname]))

  rawdata = r.content
  ```

### Generate Spectrograms

The raw data object attained from the Object Store contains a header, followed by the complex
time-series data. 

We now use a funciton in our library to convert each compamp data to 
a spectrogram. 

  ```python
  import ibmseti
  header, spectrogram = ibmseti.dsp.raw_to_spectrogram(rawdata)

  #Plot with matplotlib
  import matplotlib.pyplot as plt
  plt.ion()

  #transpose to get frequency bins on the horizontal and time on the vertical
  spectrogram = spectrogram.transpose() 

  fig, ax = plt.subplots()
  ax.imshow(spectrogram)
  plt.show()

  ax.set_aspect(float(spectrogram.shape[1]) / spectrogram.shape[0])
  ```

## Next Steps

The basics of querying and retrieving the data should now be understood. Futher examples
in our [notebooks]() folder will show how to apply these within the context of Spark, 
how to extract features from the spectrograms and apply some machine-learning models. 

It's now up to you to create new features and find better algorithms to search this
vast amount of radio-signal data to look for signals that could be signs of intelligent
life on other planets.

## Contributing

Please feel free to fork this code and submit Pull Requests. The core research team 
members from IBM, SETI and NASA will review your work and consider your algorithms for
inclusion of our library. Perhaps they'll be useful enough to be included in future
near-time analysis of data from the ATA and other SETI projects.



