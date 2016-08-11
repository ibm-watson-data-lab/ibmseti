# Copyright (c) 2016 IBM. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
This module contains some of the standard features that are extracted from
spectrograms and auto-correlation calculations from the raw SETI data. 

Some functions are merely wrappers around Numpy-based operations, but 
contain documentation that explicitly show how they are used with SETI data. 

'''

import numpy as np
import scipy.stats

def difference(arr, n=1, axis=0, **kwargs):
  '''
  Assuming that `arr` is a 2D spectrogram returned by 
  ibmseti.dsp.raw_to_spectrogram(data), this function
  uses the Numpy.diff function to calculate the nth
  difference along either time or frequency.

  If axis = 0 and n=1, then the first difference is taken 
  between subsequent time samples

  If axis = 1 and n=1, then the first difference is taken
  between frequency bins.

  For example:
    
    //each column is a frequency bin
    x = np.array([
       [ 1,  3,  6, 10],   //each row is a time sample
       [ 0,  5,  6,  8],
       [ 2,  6,  9, 12]])
  
    ibmseti.features.first_difference(x, axis=1)
    >>> array([[2, 3, 4],
               [5, 1, 2],
               [4, 3, 3]])

    ibmseti.features.first_difference(x, axis=0)
    >>> array([[-1,  2,  0, -2],
               [ 2,  1,  3,  4]])
  
  '''
  return np.diff(arr, n=n, axis=axis, **kwargs)

def projection(arr, axis=0, **kwargs):
  '''
  Assuming that `arr` is a 2D spectrogram returned by 
  ibmseti.dsp.raw_to_spectrogram(data), where each row
  of the `arr` is a power spectrum at a particular time,
  this function uses the numpy.sum function to project the 
  data onto the time or frequency axis into a 1D array.

  If axis = 0, then the projection is onto the frequency axis
  (the sum is along the time axis)

  If axis = 1, then the projection is onto the time axis.
  (the sum is along the frequency axis)

  For example:
    
    //each column is a frequency bin
    x = np.array([
       [ 1,  3,  6, 10],   //each row is a time sample
       [ 0,  5,  6,  8],
       [ 2,  6,  9, 12]])
  
    ibmseti.features.projection(x, axis=1)
    >>> array([20, 19, 29])

    ibmseti.features.projection(x, axis=0)
    >>> array([ 3, 14, 21, 30])

  One interesting kwarg that you may wish to use is `keepdims`.
  See the documentation on numpy.sum for more information.

  '''
  return np.sum(arr, axis=axis, **kwargs)

def moment(arr, moment=1, axis=0, **kwargs):
  '''
  Uses the scipy.stats.moment to calculate the Nth central 
  moment about the mean.

  If `arr` is a 2D spectrogram returned by 
  ibmseti.dsp.raw_to_spectrogram(data), where each row
  of the `arr` is a power spectrum at a particular time,
  this function, then the Nth moment along each axis
  will be computed.

  If axis = 0, then Nth moment for the data in each
  frequency bin will be computed. (The calculation is done
    *along* the 0th axis, which is the time axis.)

  If axis = 1, then Nth moment for the data in each
  time bin will be computed. (The calculation is done
    *along* the 1st axis, which is the frequency axis.)

  For example, consider the 2nd moment:
    
    //each column is a frequency bin
    x = array([[  1.,   3.,   6.,  10.], //each row is a time sample
               [  0.,   5.,   6.,   8.],
               [  2.,   6.,   9.,  12.]])
  
    ibmseti.features.mement(x, moment=2, axis=0) //the returned array is of size 4, the number of columns / frequency bins.
    >>>  array([ 0.66666667,  1.55555556,  2.,  2.66666667])

    ibmseti.features.mement(x, moment=2, axis=1) //the returned array is of size 3, the number of rows / time bins.
    >>>  array([ 11.5 ,  8.6875, 13.6875])

  If `arr` is a 1D array, such as what you'd get if you projected
  the spectrogram onto the time or frequency axis, then you must
  use axis=0. 

  '''
  return scipy.stats.moment(arr, moment=moment, axis=axis, **kwargs)

def first_order_gradient(arr, axis=0):
  '''
  Returns the gradient of arr along a particular axis using
  the first order forward-difference. 
  Additionally, the result is padded with 0 so that the
  returned array is the same shape as in input array.
  '''
  grad_arr = difference(arr, n=1, axis=axis)
  return np.insert(grad_arr, grad_arr.shape[axis], 0, axis=axis)


def total_variation(arr):
  '''
  If arr is a 2D array (N X M), assumes that arr is a spectrogram with time along axis=0.

  Calculates the 1D total variation in time for each frequency and returns an array
  of size M.

  If arr is a 1D array, calculates total variation and returns a scalar.

  Sum ( Abs(arr_i+1,j  - arr_ij) )

  If arr is a 2D array, it's common to take the mean of the resulting M-sized array
  to calculate a scalar feature. 
  '''
  return np.sum(np.abs(np.diff(arr, axis=0)), axis=0)

def maximum_variation(arr):
  '''
  return np.max(arr, axis=0) - np.min(arr, axis=0)

  If `arr` is a 1D array, a scalar is returned.

  If `arr` is a 2D array (N x M), an array of length M is returned. 
  '''
  return np.max(arr, axis=0) - np.min(arr, axis=0)

def tv_2d_isotropic(grad_0_arr, grad_1_arr):
  '''
  Calculates the Total Variation

  Assumes a 2D array.

  grad_0_arr is the gradient along the 0th axis of arr.
  grad_1_arr is the gradient along the 1st axis of arr.

  You can use the 1st order forward-difference measure 
  of the gradient (the standard calculation). Or you
  can use the second_order central gradient. 

  '''
  return np.sqrt(grad_0_arr**2 + grad_1_arr**2).sum()


def entropy(data):
  '''
  Computes H(`data`) = Sum -1 * data_i * log(data_i)
  And returns H(`data`), log(len(`data`))

  If `data` is a PDF, H(`data`) is the entropy of the system in 'natural' units. 
  (The log is the 'natural log', ln)

  The maximum possible entropy of `data` is log( len(`data`) ).

  If `data` is a PDF and is normalized ( Sum data_i * bin_size = 1), then
  the normalized entropy is equal to H(`data`) / log(len(`data`)) and will
  be in the range of [0, 1]. If `data` is a completely flat PDF, then 
  the normalized entropy will equal 1. If the `data` is a histogram with 
  bin counts = 0 except for one bin, then the entropy will be 0. 

  There are three good ways to generate a histogram from the values in the
  spectrogram. The difference is how to define the bins. 1) by hand, 2) with numpy
  3) with astroML. It is recommended to use auto-generated binning from numpy or astroML.
  
  1. By Hand

  If you choose to set the bin size / number of bins in a histogram by hand, you 
  should be careful about how you handle spectrogram values that are outside of your 
  largest bin -- that is, values outside of your bin range. For example, assume
  that you've decide to bin the spectrogram values into 250 bins between the values of 0 and 250. If you
  observe a spectrogram that has a spectrogram value = 1000, then into which bin should to 
  place that measure? If you drop that value, you're essentially removing a potential 
  signal. It is suggested that you use the numpy.clip function in order to make the 
  largedst bin in your histogram contain the number of pixels with a value equal to or 
  greater than the largest bin edge. 

    binedges = range(0,251)
    my_hist, _ = np.histogram(np.clip(spectrogram, 0, 250), bins=binedges, density=True)

  2. Numpy

  Numpy contains ways to automatically choose the bins for your based on your `data`. 

  See http://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram.html

  3. astroML
  AstroML also provides automatic bin determination and includes the Bayesain Block method,
  which is based on a paper by SETI scientist, Jeff Scargle. 

  http://www.astroml.org/user_guide/density_estimation.html#bayesian-blocks-histograms-the-right-way

  It is suggested to use the following measures as features:

    spectrogram.min, spectrogram.max, number_of_bins, entropy, max_entropy, normalized_entropy.

  If `data` is NOT a PDF, then you're on your own to interpret the results. For example,
    
    ent, max = ibmseti.features.entropy(spectrogram.flatten())

  '''
  dd = map(lambda x: -x*log(x) if x else 0, data)
  return sum(dd), log(len(dd))

