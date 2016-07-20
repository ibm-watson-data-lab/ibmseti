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


