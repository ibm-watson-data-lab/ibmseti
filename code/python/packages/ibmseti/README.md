#IBM SETI

Code produced in partnership between the SETI Institute of Mountain View, CA and IBM. 


### Requirements
  pyspark


## Example User Code

### Installation

  !pip install --user ibmseti

### Setup

  ```python
  import ibmseti

  #Set the sparkContext for the package to use
  #In Bluemix, this has already been instantiated as `sc`
  ibmseti.sparkContext = sc

  ```

### Select an Interesting Target

Use [a source](https://archive.stsci.edu/kepler/koi/search.php) or
[two](http://phl.upr.edu/projects/habitable-exoplanets-catalog) or 
[three](http://goldilocks.info/) to find an interesting Kepler expolanet coordinates.

The citizen scientist will have to figure out the coordinates in the sky
of what they're intersted in. 

Potentially, we could also  build a python tool that let's them find the 
coordinates based on a set of conditions (goldilocks zone, planet size, 
star size, etc...) -- does one not already exist??

  ```python
  kepler_coord = (-12.208, 18.351)
  ```

### Query the SignalDB for all SignalDB rows for these sky coordinates

The SignalDB contains the preliminary analysis of the data recorded for the sky coordinates.
You can use these rows of data to further refine your search. 

In the next step you'll use a list of SignalDB rows to get the raw data for those rows.
**see note below

  ```python
  sigDbRows = ibmseti.signaldb.signalDbRowsForTarget(*kepler_coord)
  ```

### Get Raw DAta

  ```python
  #from each row, determine the compamp name for that row
  compampNames = [ibmseti.signaldb.compampName(r) for r in sigDbRows]

  #returns an RDD of compampFiles
  #(*** see below)
  compampFiles = ibmseti.somemodule.getRawCompampFiles(compampNames)
  ```

### Generate Spectrograms

We now use a funciton in our library to convert each compamp data to 
a spectrogram. Additionally, the `transform` module may contain
other tools such as computing KLT transformations or SWAC calculations.

  ```python
  spectrograms = compampFiles.map(ibmseti.transform.compampToSpectrogram)

  #Plot with matplotlib

  ```

### Feature Extraction and Machine Learning

Here we offer a few examples to get started on building your own models. Additionally,
if we have the data, we could provide our own "canned" machine learning models as
examples and as starting points for futher analysis by citizen scientists. 

  ```python
  #From the spectrograms, we extract the features
  specFeatures = spectrograms.map(ibmseti.spectrograms.extractStandardFeatures)

  #Then we use some kind of machine learning if we know how to classify 
  classification = [myclassifier(s) for s in spectrograms ]

  #Each of these
  kNNModel = ibmseti.models.buildKNNModel(spe)
  ```

** In the final product, this will require a Node.js web server running on Bluemix. 
When requested by the `ibmseti` package, that server will query the database where
the SignalDB is stored.  We may limit the total number of rows returned here. 
We may also allow one to pass in conditions on the search, such as only returning 
rows where SigClass == "Cand" and other criteria in the SignalDB

*** This will also need a Node.js server in order to rate-limit users to a small 
number of compamps per day. 