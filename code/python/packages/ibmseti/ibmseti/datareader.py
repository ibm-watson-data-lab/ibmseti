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

from __constants__ import __header_offset, __bins_per_half_frame

def header(raw_str):
  '''
  raw_str is the raw data from a SETI compamp or archive-compamp file

  This returns the first header in the data file
  '''
  rf_center_frequency, half_frame_number, activity_id, subband_spacing_hz, start_subband_id, \
  number_of_subbands, over_sampling, polarization = struct.unpack('>diidiifi', raw_str[:__header_offset])  

  #todo -- add ability for somebody to use N*__bins_per_half_frame bins instead. Will
  #need to allow for N to be passed into this function, or set in the Contsants object
  half_frame_bytes = number_of_subbands * __bins_per_half_frame + __header_offset  
  number_of_half_frames = len(raw_str) / half_frame_bytes

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

def all_headers(raw_str):
  '''
  raw_str is the raw data from a SETI compamp or archive-compamp file

  This returns all headers in the data file. If this is a compamp file, there should
  be only one. If this is an archive-compamp file, there should be one for each
  subband in the file (typically 16).
  '''

  first_header = read_header(raw_str)
  packed_data = np.frombuffer(raw_str, dtype=np.int8)\
      .reshape((first_header['number_of_half_frames'], first_header['half_frame_bytes']))

  return [read_header(row) for row in packed_data]
  
def packed_data(raw_str, header):

  packed_data = np.frombuffer(raw_str, dtype=np.int8)\
      .reshape((header['number_of_half_frames'], header['half_frame_bytes']))  # create array of half frames
  packed_data = packed_data[::-1, __header_offset:]  # slice out header and flip half frame order to reverse time ordering
  packed_data = packed_data.reshape((header['number_of_half_frames']*(header['half_frame_bytes']- __header_offset))) # compact into vector

  return header, packed_data

def packed_data_to_complex(packed_data):
  '''
  This will take any data string, cast each byte to an int8 and interpret each byte
  as 4 bits real values and 4 bits imag values (RRRRIIII). The data are then
  used to fill a numpy array of dtype=complex. The numpy array is returned.

  packed_data: the data string
  normalize: if True, 
  '''
  #note that since we can only pack into int8 types, we must pad each 4-bit value with 4, 0 bits
  #this effectively multiplies each 4-bit value by 16 when that value is represented as an 8-bit signed integer.

  real_val = np.bitwise_and(packed_data, 0xf0).astype(np.int8)  # coef's are: RRRRIIII (4 bits real,
  imag_val = np.left_shift(np.bitwise_and(packed_data, 0x0f), 4).astype(np.int8)  # 4 bits imaginary in 2's complement)

  cdata = np.empty(len(real_val), complex)

  #"Normalize" by making appropriate bit-shift. Otherwise, values for real and imaginary coefficients are
  #inflated by 16x. 
  cdata.real = np.right_shift(real_val, 4)
  cdata.imag = np.right_shift(imag_val, 4)

  return cdata
