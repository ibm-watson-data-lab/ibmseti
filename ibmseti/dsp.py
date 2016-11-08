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
  Utilities to work with Spectrograms -- Power spectra v time (aka "waterfall" plots) 
'''

import numpy as np

from . import constants

def time_bins(header):
  '''
  Returns the time-axis lower bin edge values for the spectrogram.
  '''
  return np.arange(header['number_of_half_frames'], dtype=np.float64)*constants.bins_per_half_frame\
  *(1.0 - header['over_sampling']) / header['subband_spacing_hz']

def frequency_bins(header):
  '''
  Returnes the frequency-axis lower bin edge values for the spectrogram. 
  '''

  center_frequency = 1.0e6*header['rf_center_frequency']
  if header["number_of_subbands"] > 1:
    center_frequency += header["subband_spacing_hz"]*(header["number_of_subbands"]/2.0 - 0.5)

  return np.fft.fftshift(\
    np.fft.fftfreq( int(header["number_of_subbands"] * constants.bins_per_half_frame*(1.0 - header['over_sampling'])), \
      1.0/(header["number_of_subbands"]*header["subband_spacing_hz"])) + center_frequency
    )
  
def complex_to_fourier(cdata, over_sampling, norm=None):
  '''
  cdata: 3D complex data (shaped by subbands and half_frames, as returned from Compamp.complex_data())
  over_sampling: The fraction of oversampling across subbands (typically 0.25)
  norm: None or "ortho" -- see Numpy FFT Normalization documentation. Default is None.

  returns the signal in complex fourier space. The output fourier data are shifted so the central frequency
  is at the center of the values. All over-sampled frequencies have been removed so that all frequency bins
  can be properly arranged next to each other. 
  '''
  
  # FFT all blocks separately and rearrange output
  fftcdata = np.fft.fftshift(np.fft.fft(cdata, norm=norm), 2)  
  
  # slice out oversampled frequencies
  if over_sampling > 0:
    fftcdata = fftcdata[:, :, int(cdata.shape[2]*over_sampling/2):-int(cdata.shape[2]*over_sampling/2)] 
    
  return fftcdata

def fourier_to_time(fcdata, norm=None):
  '''
  Converts the data from 2D fourier space signal to a 1D time-series.

  fcdata: Complex fourier spectrum as a 2D array, The axis=0 is for each "half frame", and axis=1 contains the
  fourier-space data for that half frame. Typically there are 129 "half frames" in the data. 
  Furthermore, it's assumed that fftshift has placed the central frequency at the center of axis=1.

  norm: None or "ortho" -- see Numpy FFT Normalization documentation. Default is None.

  Usage:

    aca = ibmseti.compamp.Compamp(raw_data)
    cdata = aca.complex_data()  #cdata is a 3D numpy array in the time domain.
    #can manipulate cdata in time-space if desired (use various windowing functions, for example)
    fcdata = ibmseti.dsp.complex_to_fourier(cdata, aca.header()['over_sampling'])
    fcdata_2d = ibmseti.dsp.reshape_to_2d(fcdata)
    tcdata_1d = ibmseti.dsp.fourier_to_time(fcdata_2d)


  One can recover the Fourier Spectrum of cdata_1d by:

    cdata_2d = cdata_1d.reshape(aca.header()['number_of_half_frames'], int(aca.header()['number_of_subbands'] * ibmseti.constants.bins_per_half_frame*(1 - aca.header()['over_sampling'])))
    fcdata_2d_v2 = np.fft.fftshift(np.fft.fft(cdata_2d), 1)

    #fcdata_2d_v2 and fcdata_2d should be the same
    np.sum(np.sum(fcdata_2d - fcdata_2d_v2))  # should equal to approximately 0

  '''

  return np.fft.ifft(np.fft.ifftshift(fcdata, 1),norm=norm).reshape(fcdata.shape[0] * fcdata.shape[1])  # single complex time series


def complex_to_power(cdata, over_sampling):  
  '''
  cdata: 3D complex data (shaped by subbands and half_frames, as returned from Compamp.complex_data())
  over_sampling: The fraction of oversampling across subbands (typically 0.25). 
  
  returns a 3D spectrogram
  
  Example:
      aca = ibmseti.compamp.Compamp(raw_data)
      cdata = aca.complex_data()
      #can perform any transformations on cdata here, such as applying hanning windows for smoother FFT results.
      #cdata = np.multiply(cdata, np.hanning(constants.bins_per_half_frame))
      power = ibmseti.dsp.complex_to_power(, aca.header()['over_sampling'])
  
  Typically, this 3D spectrogram is rehaped so that the subbands are aligned next to each other
  in a 2D spectrogram
  
      spectrogram = ibmseti.dsp.reshape_to_2d(power)
  '''
  
  fftcdata = complex_to_fourier(cdata, over_sampling)

  # calculate power, normalize and amplify by factor 15 (what is the factor of 15 for?)
  fftcdata = np.multiply(fftcdata.real**2 + fftcdata.imag**2, 15.0/cdata.shape[2])

  return fftcdata

def reshape_to_2d(arr):
  '''
  Assumes a 3D Numpy array, and reshapes like
  
  arr.reshape((arr.shape[0], arr.shape[1]*arr.shape[2]))

  This is useful for converting processed data from `complex_to_power`
  and from `autocorrelation` into a 2D array for image analysis and display.

  '''
  return arr.reshape((arr.shape[0], arr.shape[1]*arr.shape[2]))


def compamp_to_spectrogram(compamp):
  '''
  Returns spectrogram, with each row containing the measured power spectrum for a XX second time sample.

  Using this function is shorthand for:
      aca = ibmseti.compamp.Compamp(raw_data)
      power = ibmseti.dsp.complex_to_power(aca.complex_data(), aca.header()['over_sampling'])
      spectrogram = ibmseti.dsp.reshape_to_2d(power)

  Example Usage: 
      import ibmseti
      import matplotlib.pyplot as plt
      plt.ion()
  
      aca = ibmseti.compamp.Compamp(raw_data)

      spectrogram = ibmseti.dsp.compamp_to_spectrogram(aca)
      time_bins = ibmseti.dsp.time_bins( aca.header() )
      freq_bins = ibmseti.dsp.frequency_bins( aca.header() )

      fig, ax = plt.subplots()
      ax.pcolormesh(freq_bins, time_bins, spectrogram)

      #Time is on the horizontal axis and frequency is along the vertical.

  '''

  power = complex_to_power(compamp.complex_data(), compamp.header()['over_sampling'])
  
  return reshape_to_2d(power)

def scale_to_png(arr):
  if arr.min() < 0:
    sh_arr = arr + -1.0*arr.min()
  else:
    sh_arr = arr
  return np.clip(sh_arr * 255.0/sh_arr.max(), 0, 255).astype(np.uint8)


def compamp_to_ac(compamp, window=np.hanning):  # convert single or multi-subband compamps into autocorrelation waterfall

  '''
  Adapted from Gerry Harp at SETI.
  
  '''
  header = compamp.header()
 
  cdata = compamp.complex_data()

  #Apply Windowing and Padding
  cdata = np.multiply(cdata, window(cdata.shape[2]))  # window for smoothing sharp time series start/end in freq. dom.
  cdata_normal = cdata - cdata.mean(axis=2)[:, :, np.newaxis]  # zero mean, does influence a minority of lines in some plots

  cdata = np.zeros((cdata.shape[0], cdata.shape[1], 2 * cdata.shape[2]), complex)
  cdata[:, :, cdata.shape[2]/2:cdata.shape[2] + cdata.shape[2]/2] = cdata_normal  # zero-pad to 2N

  #Perform Autocorrelation
  cdata = np.fft.fftshift(np.fft.fft(cdata), 2)  # FFT all blocks separately and arrange correctly
  cdata = cdata.real**2 + cdata.imag**2  # FFT(AC(x)) = FFT(x)FFT*(x) = abs(x)^2
  cdata = np.fft.ifftshift(np.fft.ifft(cdata), 2)  # AC(x) = iFFT(abs(x)^2) and arrange correctly
  cdata = np.abs(cdata)  # magnitude of AC

  # normalize each row to sqrt of AC triangle
  cdata = np.divide(cdata, np.sqrt(np.sum(cdata, axis=2))[:, :, np.newaxis])  

  return cdata

def ac_viz(acdata):
  '''
  Adapted from Gerry Harp at SETI.
  
  Slightly massages the autocorrelated calculation result for better visualization.

  In particular, the natural log of the data are calculated and the
  values along the subband edges are set to the maximum value of the data, 
  and the t=0 delay of the autocorrelation result are set to the value of the t=-1 delay.

  This is allowed because the t=0, and subband edges do not carry any information. 

  To avoid log(0), a value of 0.000001 is added to all array elements before being logged. 
  '''

  acdata = np.log(acdata+0.000001)  # log to reduce darkening on sides of spectrum, due to AC triangling
  acdata[:, :, acdata.shape[2]/2] = acdata[:, :, acdata.shape[2]/2 - 1]  # vals at zero delay set to symmetric neighbor vals
  acdata[:, :, acdata.shape[2] - 1] = np.max(acdata)  # visualize subband edges

  return acdata



