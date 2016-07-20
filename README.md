#IBM SETI

The `ibmseti` package is used to read and analyze SETI Institute data generated from the Allen Telescope Array.
It provides the essential code needed to get started reading the data, calculating spectrograms and autocorrelation
spectra, and extracting some of the standard features from those results.

This coode was produced in partnership between the SETI Institute of Mountain View, CA and IBM.

## Privacy Warning

We send usage information of this library when you import the package in your code and make particular calls.
In particular, we collect the following environment variables:

  * USER
  * SPARK_MASTER_IP
  * SPARK_TENANT_ID

In the IBM Spark Service environment these envars contains unique identifiers for your Spark Service. 

If you wish to turn this off, you may do so by

```python
ibmseti.callback.disable()
```


## Example User Code

### Installation

    pip install ibmseti


### Setup

```python
import ibmseti
```

##### Obtaining Data

[Click here for documentation and examples for the Public IBM+SETI Data Server REST API](https://github.com/ibm-cds-labs/setigopublic/blob/master/README.md), 
which also briefly describes the SETI data. 
[This IBM Spark notebook](https://console.ng.bluemix.net/data/notebooks/e17dc8c6-9c33-4947-be31-ee6b4b7e0888/view?access_token=6e95d320610f67467ba63bc89d9cec48faf847f2532fdd7523b0dd2ccb9ea346#) 
gives an example use of the API and how to store the data in your Bluemix Account's Object Store instance.

### Read the Data

The raw data (`compamp` or `archive-compamp` files) are read with a `ibmseti.compamp.Compamp` object.

```python
import ibmseti
rawdata = open('path/to/data/2014-08-11/act17713/2014-08-11_05-50-10_UTC.act17713.dx2009.id-2.R.archive-compamp','r').read()
aca = ibmseti.compamp.Compamp(rawdata)
```

### Create Spectrogram and Plot

Here, we show the code to produce a Spectrogram plot from a Compamp object with the `ibmseti.dsp` module.

```python
spectrogram = ibmseti.dsp.compamp_to_spectrogram(aca)
time_bins = ibmseti.dsp.time_bins( aca.header() )
freq_bins = ibmseti.dsp.frequency_bins( aca.header() )

import matplotlib.pyplot as plt
plt.ion()
fig, ax = plt.subplots()
#ax.pcolormesh(freq_bins, time_bins, spectrogram)
```

### Feature Extraction

Here we show some features one may extract from a spectrogram with the `ibmset.features` module.
In each of these, the `data` is the spectrogram.

It should be noted that these features are experimental and may or may not have strong 
impacts on classification. They are initial guesses made by a handful of SETI/NASA researchers, who
make no guarantees about their usefulness. But we add them in the code here to get you started. 

##### Features based on the Spectrogram

###### Standard Deviation of the projection of the spectrogram onto the time and frequency axis.

```
std_time = math.sqrt(ibmseti.features.moment( ibmseti.features.projection(data, axis=1), moment=2))
std_freq = math.sqrt(ibmseti.features.moment( ibmseti.features.projection(data, axis=0), moment=2))
```

###### Average Standard Deviation of the spectrogram along each slice of the time and frequency axis.

```
std_time = np.mean(np.sqrt(ibmseti.features.moment( data, axis=0, moment=2)))
std_freq = np.mean(np.sqrt(ibmseti.features.moment( data, axis=1, moment=2)))
```

###### Average N-th moment of the spectrogram along each slice of the time and frequency axis.

```
N = 3 #kurtosis 
N = 4 #skewness
nth_moment_time = np.mean( ibmseti.features.moment( data, axis=0, moment=N))
nth_moment_freq = np.mean( ibmseti.features.moment( data, axis=1, moment=N))
```

###### N-th moment of the projection of the spectrogram onto the time and frequency axis.

```
N = 3 #kurtosis
N = 4 #skewness
nth_moment_time = ibmseti.features.moment( ibmseti.features.projection(data, axis=1), moment=N)
nth_moment_freq = ibmseti.features.moment( ibmseti.features.projection(data, axis=0), moment=N)
```

###### Mean [Total Variation](https://en.wikipedia.org/wiki/Total_variation) (along the time axis) of the spectrogram.

```
tv_for_each_frequency = ibmseti.features.total_variation(data)
tv = np.mean( tv_for_each_frequency )
```

###### Excess Kurtosis

Measures the *non-guassianity* of a distribution. Could be measure after projecting a spectrogram onto
it's frequency-axis.

```
fourth_mom = ibmseti.features.moment( ibmseti.features.projection(data, axis=0), moment=4)
variance = ibmseti.features.moment( ibmseti.features.projection(data, axis=0), moment=2)
excess_kurtosis = fourth_mom/variance - 3
```

###### Linear fit to histogram of log of power

###### Shannon Entropy (based on histogram of log of power)

##### Features based on the [First Difference](http://people.duke.edu/~rnau/411diff.htm)

###### Mean First Difference (along the time axis) of the spectrogram.

```
first_diff_along_time = ibmseti.features.difference(data, axis=0)
first_diff_along_freq = ibmseti.features.difference(data, axis=1)

fd_mean_along_time = np.mean(first_diff_along_time, axis=0).mean() 
fd_mean_along_freq = np.mean(first_diff_along_freq, axis=1).mean()

#same as first_diff_along_time.mean() because each element of the array is the same size!
#the average of the averages is the same as the total average if the sets of averages all have the same cardinality
```

###### N-th moment of the first difference

```
N = 2 #variation
N = 3 #kurtosis 
N = 4 #skewness
nth_moment_time = np.mean( ibmseti.features.moment( first_diff_along_time, axis=0, moment=N))
nth_moment_freq = np.mean( ibmseti.features.moment( first_diff_along_freq, axis=1, moment=N))
```

###### Maximum Variation

This can be calculated for the spectrogram, or for the first-difference, or gradient, 
along the time- or frequency-axis.

```
max_var_t = np.max( ibmseti.features.maximum_variation(ibmseti.features.difference(data, axis=0), axis=0))
max_var_f = np.max( ibmseti.features.maximum_variation(ibmseti.features.difference(data, axis=1), axis=1))
```


##### Features based on the Gradient

One can also calculate similar features (mean, N-th moments) based on the **gradient** of the signal along
the time or frequency axis. Use `ibmseti.features.first_order_gradient` 
or `numpy.gradient` to calculate the gradients. Then just as above with the
`first difference`, one can calculate the various moments and other features.




## Next Steps

More robust examples are found in the following shared IBM Spark notebooks. These examples show

* [how to use the REST API and store data to your Bluemix Object Store](https://console.ng.bluemix.net/data/notebooks/e17dc8c6-9c33-4947-be31-ee6b4b7e0888/view?access_token=6e95d320610f67467ba63bc89d9cec48faf847f2532fdd7523b0dd2ccb9ea346#)
* [retrieve the data from Object Store and calculate a spectrogram](https://console.ng.bluemix.net/data/notebooks/d9e06caa-ab8b-41d8-b9f7-507cea13f085/view?access_token=48f90032025617b309558b9734946c5bdc9cda5fdb1596ddb23899b05b162786)
* [retrieve the data from Object Store and calculate features](https://console.ng.bluemix.net/data/notebooks/f234dad3-4966-41d3-8f21-16649a87ba3f/view?access_token=dc4926ef99723f7068e5c48315fe7510fde4eb4ae7c00ed4f7521b012b5a5db5)

all using [the IBM Spark Service](http://www.ibm.com/analytics/us/en/technology/spark/) 
in [Bluemix](https://console.ng.bluemix.net/docs/services/AnalyticsforApacheSpark/index.html). 

It's now up to you to create new features and find better algorithms to search this
vast amount of radio-signal data to find signals that could be signs of extraterrestrial intelligent
life.


### License 

Copyright 2016 IBM Cloud Data Services

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


### Contributing

Please feel free to fork this repository and submit Pull Requests. The core research team 
members from SETI, NASA and IBM will review your work and consider your algorithms for
inclusion in our library. We are hoping to find new algorithms that are useful enough to 
be included in future real-time analysis of data from the ATA and other SETI projects.



