
import numpy as np
import struct

_header_offset = 40

def read_header(raw_str, max_subband_bins_per_1khz_half_frame = 512):

  rf_center_frequency, half_frame_number, activity_id, hz_per_subband, start_subband_id, \
  number_of_subbands, over_sampling, polarization = struct.unpack('>diidiifi', raw_str[:_header_offset])  # read header

  half_frame_bytes = number_of_subbands * max_subband_bins_per_1khz_half_frame + _header_offset  # MAX_SUBBAND_BINS_PER_1KHZ_HALF_FRAME = 512
  number_of_half_frames = len(raw_str) / half_frame_bytes

  return {'rf_center_frequency':rf_center_frequency, 
          'half_frame_number':half_frame_number, 
          'activity_id':activity_id, 
          'hz_per_subband':hz_per_subband, 
          'start_subband_id':start_subband_id,
          'number_of_subbands':number_of_subbands, 
          'over_sampling':over_sampling, 
          'polarization':polarization, 
          'half_frame_bytes':half_frame_bytes, 
          'number_of_half_frames':number_of_half_frames}

def to_header_and_packed_data(raw_str, max_subband_bins_per_1khz_half_frame = 512):

  header = read_header(raw_str, max_subband_bins_per_1khz_half_frame)

  packed_data = np.frombuffer(raw_str, dtype=np.int8)\
      .reshape((header['number_of_half_frames'], header['half_frame_bytes']))  # create array of half frames
  packed_data = packed_data[::-1, _header_offset:]  # slice out header and flip half frame order to reverse time ordering
  packed_data = packed_data.reshape((header['number_of_half_frames']*(header['half_frame_bytes']-_header_offset))) # compact into vector

  return header, packed_data

def packed_data_to_complex(packed_data, normalize=True):

  #note that since we can only pack into int8 types, we must pad each 4-bit value with 4, 0 bits
  #this effectively multiplies each 4-bit value by 16 when that value is represented as an 8-bit signed integer.

  real_val = np.bitwise_and(packed_data, 0xf0).astype(np.int8)  # coef's are: RRRRIIII (4 bits real,
  imag_val = np.left_shift(np.bitwise_and(packed_data, 0x0f), 4).astype(np.int8)  # 4 bits imaginary in 2's complement)

  cdata = np.empty(len(real_val), complex)

  #Add option to normalize. I don't think the values of our 
  #data will reach the limits of float32 or float64 numbers. A factor of 16x16 (256x) won't
  #inflate the values to anywhere near the float32/64 limits, 
  #but it does add more computation. So, can turn off this bit-shift operation
  if normalize:
    cdata.real = np.right_shift(real_val, 4)
    cdata.imag = np.right_shift(imag_val, 4)
  else:
    cdata.real = real_val
    cdata.imag = imag_val

  return cdata
