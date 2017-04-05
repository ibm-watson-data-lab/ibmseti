import numpy as np
import json


class SimCompamp(object):

  '''
  Class to unpack data simulated SETI archive-compamp and compamp files.

  Also has functions to compute the DFT and spectrograms.
  '''

  def __init__(self, data):
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
    self.header = json.loads(header)

  def complex_data(self):
    '''
    This unpacks the data into a time-series data, of complex values.

    '''
    return np.frombuffer(self.data, dtype='i1').astype(np.float32).view(np.complex64)

  def _reshape(self, complex_data, shape=(129,6144)):
    '''
    Reshapes the input complex_data in a 2D array of size, shape. Standard is 129x6144. 
    This is the same size as standard SETI archive-compamp files. 

    However, you can play around with shape size as much as you want.

    Tip: If you slice out the first (or last) 6144 samples of the data, you can produce many more
    2D shapes (128 x 6144... 64 x 12288, 32 x 24567) than you can normally. 
    '''
    return complex_data.reshape(*shape)

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