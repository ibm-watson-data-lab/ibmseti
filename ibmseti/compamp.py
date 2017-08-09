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

  def __init__(self, data, shape=(int(32*12),int(6144/12))):
    '''
    data is the raw data read from a simulated SETI compamp or archive-compamp file. It should be a string.

    This object does not automatically read and unpack the data upon instantiation. Instead, it does
    so only when called upon. This allows the object to be instantiated on a Spark driver, 
    and the work to read/unpack the data may be performed on an executor. 

    It also does not cache the unpacked data in order to reduce the memory footprint.

    Note to SETI/IBM researchers: This class is for the public simulated files, as it assumes
    just a one line header. 

    NEW: Default shape is 384 x 512 (previously was 32 x 6144)
    Standard usage:

      raw_data = open('data_file.dat', r).read()
      #or
      r = requests.get('https://url/to/data_file.dat')
      raw_data = r.content
    
      import ibmseti
      aca = ibmseti.SimCompamp(raw_data)
      spectrogram = aca.get_spectrogram()

    The shape can be changed with

      aca.shape = (32,6144)
    
    '''
    
    header, self.data = data.split(b'\n',1)
    private_header = None

    header = json.loads(header)

    if header.get('simulator_software_version',0) > 0:
        #this is the private header and we need to remove one more line
        #to get the public header
        private_header = header
        header, self.data = self.data.split(b'\n',1)

    self._header = header
    self.shape = shape
    self._private_header = private_header

    self.sigProc(None)

  def header(self):
    '''
    Returns the header

    NB: added to match the header() call from the Compamp object.
    '''
    return self._header

  def private_header(self):
    '''
    Returns the private header

    '''
    return self._private_header

  def sigProc(self, function=None):
    '''
    Set a function to peform signal processing before converting the time-series data into 
    a spectrogram.

    Your function should expect a single input, a 2D complex-valued time-series numpy array. It will
    have the shape you set with the self.shape attribute. Your function should return a
    2D numpy array. Note: the returned array can be any shape and size.

    If the function is None, there will be no effect on the time-series data. 

    For example: 

      import numpy as np
      aca = ibmseti.compamp.SimCompamp(data)

      def mySigProc(compdata):
        return compdata * np.hanning(compdata.shape[1])

      aca.sigProc(mySigProc)

      #the hanning window will be applied to the 2D complex time-series data
      spectrogram = aca.get_spectrogram()

    '''
    self._sigProc = function if function else lambda x : x

  
  def complex_data(self):
    '''
    This unpacks the data into a time-series data, of complex values.

    Also, any DC offset from the time-series is removed.

    This is a 1D complex-valued numpy array.
    '''
    cp = np.frombuffer(self.data, dtype='i1').astype(np.float32).view(np.complex64)
    cp = cp - cp.mean()
    return cp

  def _reshape(self, complex_data):
    '''
    Reshapes the input complex_data in a 2D array of size, shape. Standard is 384 x 512 for simulation files. 
    This is not the same size as standard SETI archive-compamp files, which are typically 129 x 6144. One can 
    also shape the data as 32 x 6144 in order to create spectrogram in a shape that is more similar to the 
    typical shape of spectrogram. Reshaping changes the time-resolution and frequency-resolution of the resulting
    spectrogram. The optimal shape for signal class recognition may vary for each class.

    However, you can play around with shape size as much as you want.
    '''
    return complex_data.reshape(*self.shape)

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
    Transforms the input simulated data and computes a standard-sized spectrogram.

    If self.sigProc function is not None, the 2D complex-valued time-series data will 
    be processed with that function before the FFT and spectrogram are calculated. 
    '''

    return self._spec_power(self._spec_fft(  self._sigProc( self._reshape( self.complex_data() )) ))
