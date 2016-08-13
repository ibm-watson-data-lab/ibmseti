#!/usr/bin/env python
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
This module provides convenience calls to the IBM+SETI Public REST API which
serves data for this project. 

This is a *very* basic (dumb) wrapper, using the requests library, to make calls to 
the REST API. At the moment, the API is limited to just four different endpoints.

This module does not perform any connection pooling or advanced usage of the
requests package. It is a simple convenience. Please feel free to contribute!

Also, this module contains a few helper functions for manipulating and packaging
the data returned from the API for the purposes of storing raw data and 
signalDB data together in a pickled file. 
'''

import requests
import copy

__base_url = 'https://setigopublic.mybluemix.net'

def coordinates_aca(base_url = __base_url, params={}):
  '''
  See https://github.com/ibm-cds-labs/setigopublic#celestial-coordinates-of-candidate-events

  params is a dictionary that may contain the keys: ramin, ramax, decmin, decmax, skip, limit.

  Raises exception on status. (Request.raise_for_status())

  returns JSON result.
  '''
  r = requests.get('{}/v1/coordinates/aca'.format(__base_url), params = params)
  r.raise_for_status()
  return r.json()


def aca_meta(ra, dec, base_url = __base_url, params={}):
  '''
  See https://github.com/ibm-cds-labs/setigopublic#meta-data-and-location-of-candidate-events

  Must provide the celestial coordinates of the object, `ra` and `dec`.

  params is a dictionary that may contain the keys: skip, limit.

  Raises exception on status. (Request.raise_for_status())

  returns JSON result.
  '''
  r = requests.get('{}/v1/aca/meta/{}/{}'.format(__base_url, ra, dec), params = params)
  r.raise_for_status()
  return r.json()

def data_url(container, objectname, base_url = __base_url, params={}):
  '''
  See https://github.com/ibm-cds-labs/setigopublic#temporary-url-for-raw-data

  Must provide the container and objectname the raw data file.

  params is a dictionary that may contain the keys: skip, limit.

  Raises exception on status. (Request.raise_for_status())

  returns JSON result.
  '''
  r = requests.get('{}/v1/data/url/{}/{}'.format(__base_url, container, objectname), params = params)
  r.raise_for_status()
  return r.json()

