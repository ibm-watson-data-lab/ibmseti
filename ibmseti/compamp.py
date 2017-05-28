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

import numpy as np
import json
import struct

from . import constants


class Compamp(object):

  '''
  Class to read and unpack data from SETI archive-compamp and compamp files.
  '''

  def __init__(self, data):
    '''
    data is the raw data read from a SETI compamp or archive-compamp file as a string type.

    This object does not automatically read and unpack the data upon instantiation. Instead, it does
    so only when called upon. This allows the object to be instantiated on a Spark driver, 
    and the work to read/unpack the data may be performed on an executor. 

    It also does not cache the unpacked data in order to reduce the memory footprint.
    '''
    self.data = data
    self._header = None

  def _read_half_frame_header(self, data):
    rf_center_frequency, half_frame_number, activity_id, subband_spacing_hz, start_subband_id, \
    number_of_subbands, over_sampling, polarization = struct.unpack('>diidiifi', data[:constants.header_offset])  

    #rf_center_frequency is the center frequency of the first subband in the file. If this is a compamp file,
    #there is only one subband. If this is an archive-compamp, there are typically 16 subbands.
    #This information must be used to properly calculate the 

    #todo -- add ability for somebody to use N*__bins_per_half_frame bins instead. Will
    #need to allow for N to be passed into this function, or set in the Contsants object
    half_frame_bytes = number_of_subbands * constants.bins_per_half_frame + constants.header_offset  
    number_of_half_frames = len(data) / half_frame_bytes

    return {'rf_center_frequency':rf_center_frequency, 
            'half_frame_number':half_frame_number, 
            'activity_id':activity_id, 
            'subband_spacing_hz':subband_spacing_hz, 
            'start_subband_id':start_subband_id,
            'number_of_subbands':number_of_subbands, 
            'over_sampling':over_sampling, 
            'polarization':polarization, 
            'half_frame_bytes':half_frame_bytes, 
            'number_of_half_frames':number_of_half_frames}

  def header(self):
    '''
    This returns the first header in the data file

    '''
    if self._header is None:
      self._header = self._read_half_frame_header(self.data)

    return self._header

  def headers(self):
    '''
    This returns all headers in the data file. There should be one for each
    half_frame in the file (typically 129).
    '''

    first_header = self.header()
    single_compamp_data = np.frombuffer(self.data, dtype=np.int8)\
        .reshape((first_header['number_of_half_frames'], first_header['half_frame_bytes']))

    return [self._read_half_frame_header(row) for row in single_compamp_data]
    
  def _packed_data(self):
    '''
    Returns the bit-packed data extracted from the data file. This is not so useful to analyze.
    Use the complex_data method instead.
    '''
    header = self.header()

    packed_data = np.frombuffer(self.data, dtype=np.int8)\
        .reshape((header['number_of_half_frames'], header['half_frame_bytes']))  # create array of half frames
    packed_data = packed_data[::-1, constants.header_offset:]  # slice out header and flip half frame order to reverse time ordering
    packed_data = packed_data.reshape((header['number_of_half_frames']*(header['half_frame_bytes']- constants.header_offset))) # compact into vector

    return packed_data

  def complex_data(self):
    '''
    This will cast each byte to an int8 and interpret each byte
    as 4 bits real values and 4 bits imag values (RRRRIIII). The data are then
    used to create a 3D numpy array of dtype=complex, which is returned. 

    The shape of the numpy array is N half frames, M subbands, K data points per half frame,
    where K = constants.bins_per_half_frame, N is typically 129 and M is typically 1 for
    compamp files and 16 for archive-compamp files. 

    Note that this returns a Numpy array of type complex64. This data is not retained within Compamp objects.

    '''
    #note that since we can only pack into int8 types, we must pad each 4-bit value with 4, 0 bits
    #this effectively multiplies each 4-bit value by 16 when that value is represented as an 8-bit signed integer.
    packed_data = self._packed_data()
    header = self.header()

    real_val = np.bitwise_and(packed_data, 0xf0).astype(np.int8)  # coef's are: RRRRIIII (4 bits real,
    imag_val = np.left_shift(np.bitwise_and(packed_data, 0x0f), 4).astype(np.int8)  # 4 bits imaginary in 2's complement)

    cdata = np.empty(len(real_val), np.complex64)

    #"Normalize" by making appropriate bit-shift. Otherwise, values for real and imaginary coefficients are
    #inflated by 16x. 
    cdata.real = np.right_shift(real_val, 4)
    cdata.imag = np.right_shift(imag_val, 4)

    # expose compamp measurement blocks
    cdata = cdata.reshape((header['number_of_half_frames'], header['number_of_subbands'], constants.bins_per_half_frame))

    return cdata


class SimCompamp(object):

  '''
  Class to unpack data simulated SETI archive-compamp and compamp files.

  Also has functions to compute the DFT and spectrograms.
  '''

  def __init__(self, data, shape=(32,6144)):
    '''
    data is the raw data read from a simulated SETI compamp or archive-compamp file. It should be a string.

    This object does not automatically read and unpack the data upon instantiation. Instead, it does
    so only when called upon. This allows the object to be instantiated on a Spark driver, 
    and the work to read/unpack the data may be performed on an executor. 

    It also does not cache the unpacked data in order to reduce the memory footprint.

    Note to SETI/IBM researchers: This class is for the public simulated files, as it assumes
    just a one line header. 

    Standard usage:

    
    raw_data = open('data_file.dat', r).read()
    #or
    r = requests.get('https://url/to/data_file.dat')
    raw_data = r.content
    
    import ibmseti
    aca = ibmseti.SimCompamp(raw_data)
    spectrogram = aca.get_spectrogram()
    
    '''
    
    header, self.data = data.split('\n',1)
    self._header = json.loads(header)
    self._shape = shape


  def header(self):
    '''
    Returns the header

    NB: added to match the header() call from the Compamp object.
    '''
    return self._header

  def complex_data(self):
    '''
    This unpacks the data into a time-series data, of complex values.

    '''
    return np.frombuffer(self.data, dtype='i1').astype(np.float32).view(np.complex64)

  def _reshape(self, complex_data):
    '''
    Reshapes the input complex_data in a 2D array of size, shape. Standard is 32 x 6144 for simulation files. 
    This is not the same size as standard SETI archive-compamp files, which are typically 129 x 6144.

    However, you can play around with shape size as much as you want.

    Tip: If you slice out the first (or last) 6144 samples of the data, you can produce many more
    2D shapes (128 x 6144... 64 x 12288, 32 x 24567) than you can normally. 
    '''
    return complex_data.reshape(*self._shape)

  def _spec_fft(self, complex_data):
    '''
    Calculates the DFT of the complex_data along axis = 1.  This assumes complex_data is a 2D array.

    This uses numpy and the code is straight forward
    np.fft.fftshift( np.fft.fft(complex_data), 1)

    Note that we automatically shift the FFT frequency bins so that along the frequency axis, 
    "negative" frequencies are first, then the central frequency, followed by "positive" frequencies.
    '''
    return np.fft.fftshift( np.fft.fft(complex_data), 1)

  def _spec_power(self, complex_data_fft):
    '''
    Computes the |v|^2 of input. Assuming a 2D array in the frequency domain (output of spec_fft), this
    produces a spectrogram
    '''
    return np.abs(complex_data_fft)**2

  def get_spectrogram(self):
    '''
    Transforms the input simulated data and computes a standard-sized spectrogram
    '''
    return self._spec_power(self._spec_fft(self._reshape(self.complex_data())))
