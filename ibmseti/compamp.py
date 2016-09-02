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
import struct

from . import __constants__


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
    self.__header__ = None

  def __read_half_frame_header__(self, data):
    rf_center_frequency, half_frame_number, activity_id, subband_spacing_hz, start_subband_id, \
    number_of_subbands, over_sampling, polarization = struct.unpack('>diidiifi', data[:__constants__.header_offset])  

    #rf_center_frequency is the center frequency of the first subband in the file. If this is a compamp file,
    #there is only one subband. If this is an archive-compamp, there are typically 16 subbands.
    #This information must be used to properly calculate the 

    #todo -- add ability for somebody to use N*__bins_per_half_frame bins instead. Will
    #need to allow for N to be passed into this function, or set in the Contsants object
    half_frame_bytes = number_of_subbands * __constants__.bins_per_half_frame + __constants__.header_offset  
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
    if self.__header__ is None:
      self.__header__ = self.__read_half_frame_header__(self.data)

    return self.__header__

  def headers(self):
    '''
    This returns all headers in the data file. There should be one for each
    half_frame in the file (typically 129).
    '''

    first_header = self.header()
    single_compamp_data = np.frombuffer(self.data, dtype=np.int8)\
        .reshape((first_header['number_of_half_frames'], first_header['half_frame_bytes']))

    return [self.__read_half_frame_header__(row) for row in single_compamp_data]
    
  def __packed_data__(self):
    '''
    Returns the bit-packed data extracted from the data file. This is not so useful to analyze.
    Use the complex_data method instead.
    '''
    header = self.header()

    packed_data = np.frombuffer(self.data, dtype=np.int8)\
        .reshape((header['number_of_half_frames'], header['half_frame_bytes']))  # create array of half frames
    packed_data = packed_data[::-1, __constants__.header_offset:]  # slice out header and flip half frame order to reverse time ordering
    packed_data = packed_data.reshape((header['number_of_half_frames']*(header['half_frame_bytes']- __constants__.header_offset))) # compact into vector

    return packed_data

  def complex_data(self):
    '''
    This will cast each byte to an int8 and interpret each byte
    as 4 bits real values and 4 bits imag values (RRRRIIII). The data are then
    used to create a 3D numpy array of dtype=complex, which is returned. 

    The shape of the numpy array is N half frames, M subbands, K data points per half frame,
    where K = __constants__.bins_per_half_frame, N is typically 129 and M is typically 1 for
    compamp files and 16 for archive-compamp files. 

    '''
    #note that since we can only pack into int8 types, we must pad each 4-bit value with 4, 0 bits
    #this effectively multiplies each 4-bit value by 16 when that value is represented as an 8-bit signed integer.
    packed_data = self.__packed_data__()
    header = self.header()

    real_val = np.bitwise_and(packed_data, 0xf0).astype(np.int8)  # coef's are: RRRRIIII (4 bits real,
    imag_val = np.left_shift(np.bitwise_and(packed_data, 0x0f), 4).astype(np.int8)  # 4 bits imaginary in 2's complement)

    cdata = np.empty(len(real_val), complex)

    #"Normalize" by making appropriate bit-shift. Otherwise, values for real and imaginary coefficients are
    #inflated by 16x. 
    cdata.real = np.right_shift(real_val, 4)
    cdata.imag = np.right_shift(imag_val, 4)

    # expose compamp measurement blocks
    cdata = cdata.reshape((header['number_of_half_frames'], header['number_of_subbands'], __constants__.bins_per_half_frame))

    return cdata


