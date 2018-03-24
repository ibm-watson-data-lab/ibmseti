# IBMSETI

This README describes the `ibmseti` package. This software is used to read and analyze 
SETI Institute data generated from the Allen Telescope Array. It provides the essential 
code needed to get started reading the data, calculating spectrograms and autocorrelation
spectra, and extracting some of the standard features from those results.


## Example User Code

### Installation

    pip install ibmseti


### Read the Data

The raw data (`compamp` or `archive-compamp` files) are read with a `ibmseti.compamp.Compamp` object.
Be sure to open files in `rb` mode. 

```python
import ibmseti
rawdatafile = open('path/to/data/2014-08-11/act17713/2014-08-11_05-50-10_UTC.act17713.dx2009.id-2.R.archive-compamp','rb')
aca = ibmseti.compamp.Compamp(rawdatafile.read())
```

#### Simulated data

This package can now read data that was simulated for the [SETI Institute hackathon](https://www.eventbrite.com/e/seti-institute-hackathon-machine-learning-for-the-search-for-extraterrestrial-intelligence-tickets-32830428696) and [code challenge (June/July 2017)](https://www.eventbrite.com/e/seti-institute-code-challenge-machine-learning-for-the-search-for-extraterrestrial-intelligence-registration-32831985352)

```python
import ibmseti
rawdatafile = open('path/to/data/<some random string>.dat','rb')
aca = ibmseti.compamp.SimCompamp(rawdatafile.read())
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
ax.pcolormesh(freq_bins, time_bins, spectrogram)
```

#### Spectrum from Simulated Data

Due to the difference in the structure of the bytes packed in the simulated data compared to 
the real data (the simulated data are much simpler), a different code was written to create a spectrogram.
Also, there is no need for the time and frequency bin edges for the plots. The simulated signals could
be at any central frequency, and digitized at any sampling rate. However, the shape of the spectrogram 
produced in the code below transforms the data into the "standard" spectrogram/waterfall typically used
to analyze the real archive-compamp files.  Be sure to open files in `rb` mode. 

```python
rawdatafile = open('path/to/data/<uuid>.dat','rb')
aca = ibmseti.compamp.SimCompamp(rawdatafile.read())
spectrogram = aca.get_spectrogram()

import matplotlib.pyplot as plt
plt.ion()
fig, ax = plt.subplots()
ax.imshow(np.log(spectrogram), aspect = 0.5*float(spectrogram.shape[1]) / spectrogram.shape[0])
```


### Feature Extraction

Here we show some features one may extract from a spectrogram with the `ibmset.features` module.
In each of these, the `data` is the spectrogram.

It should be noted that these features are experimental and may or may not have strong 
impacts on classification. They are initial guesses made by a handful of SETI/NASA researchers, who
make no guarantees about their usefulness. But we add them in the code here to get you started. 

Also, the spectrograms are relatively large. One may consider reducing the size of the spectrogram
using https://gist.github.com/derricw/95eab740e1b08b78c03f. Calculations done with a 
spectogram of reduced size can be significantly faster. For example, one can reduce the
size from 129x6144 to 43x192: `spectrogram = bin_ndarray(spectrogram, (43,192), operation='sum')`). If you sliced
off one of the time-bins to make the spectrogram 128x6144, you could reduce the spectrogram by other factors.

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

##### Entropy (based on histogram of log of power)

The entropy of a signal is a measure of the amount of order/disorder in the system. In information
theory, it is the measure of the average amount of "information" in a signal. 

The `ibmseti.features.entropy` function computes the entropy of a histogram of the power
values measured in the spectrogram. The histogram represents an estimate of probability distribution function
of the power. You must build the histogram on your own, however. And you should also be
sure that your histogram is normalized to 1 (Sum h_i * bin_size_i  = 1). 

When used properly, this could score each spectrogram with a value between 0 and 1, where 1
represents pure noise and 0 would represent a maximally large signal, or amount of information.
(Though in reality, expect signals to have a value between 0.5 and 1, and for small signals to 
be closer to 1.0 than to 0.5.) 

The use of this measure depends significantly on how the histogram is created. There are 
multiple ways this can be done. See the [docstring for details on how to build a histogram and use this calculation.](ibmseti/features.py#L188-L282)

Example: 

```
bin_edges = range(0,501)
p, _ = np.histogram(np.clip(spectrogram.flatten(), 0, 500), bins=bin_edges, density=True)
w = np.diff(bin_edges)
h_p, h_max = ibmseti.features.entropy(p,w)

h_normal = h_p / h_max  #h_normal should range between 0 and 1.
```

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

##### Asymmetry

It may be useful to examine the asymmetry of the signal measured in the L and R polarization components. 
The asymmetry is defined as

  A = (spect_L - spect_R) / (spect_L + spect_R)

where `spect_L` and `spect_R` are the 2D spectrograms for the L and R polarizations.  The returned 
`A` can be further analyzed. The total integration of `A` could be a useful feature as we would expect
E.T. signals not to be completely polarized in either the L or R polarizations (A = +/- 1).  

##### Summation of Polarities

It may be useful to examine the full signal in both polarities by summing them together

  S = spect_L + spect_R

where `spect_L` and `spect_R` are the 2D spectrograms for the L and R polarizations.  

### License 

Copyright 2017 IBM Cloud Data Services

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



