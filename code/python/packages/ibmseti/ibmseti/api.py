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

# def data_urls(cont_obj_list, base_url = __base_url, params={}):
#   '''
#   todo: need to implement this on the server. 

#   '''

def __build_list(L, key, value):
    '''
    Given a sequence of dictionaries, L, this builds a list containing 
    all of the dictionaries where key == value.
    
    For example:
    L = [{'id': '1234', 'name': 'Jason'},
         {'id': '2345', 'name': 'Tom'},
         {'id': '3456', 'name': 'Art'},
         {'id': 'adfad', 'name': 'Tom'},
         {'id': 'ad34d', 'name': 'Tom'}]
         
    toms = build_list(L, 'name', 'Tom')
    
    print toms
        [{'id': '2345', 'name': 'Tom'},
         {'id': 'adfad', 'name': 'Tom'},
         {'id': 'ad34d', 'name': 'Tom'}]
    '''
    return [L[i] for i,_ in enumerate(L) if _[key] == value]

def __build_tuple_list(L, key):
    '''
    L is a sequence of dictionaries, dicts, where each dictionary contains
    the key, `key`. 
    
    This returns a list of tuples where the first element of each tuple
    is a value of the dicts[key], and the second element is a list of 
    dictionaries where dicts[key] == value.
    
    For example: 
    
    L = [{'id': '1234', 'name': 'Jason'},
         {'id': '2345', 'name': 'Tom'},
         {'id': '3456', 'name': 'Art'},
         {'id': 'adfad', 'name': 'Tom'},
         {'id': 'ad34d', 'name': 'Tom'}]
         
    tuples = build_tuple_list(L, 'name')
    
    print tuples
        [
            ('Art', [{'id': '3456', 'name': 'Art'}]),
            ('Jason', [{'id': '1234', 'name': 'Jason'}]),
            ('Tom',
                [{'id': '2345', 'name': 'Tom'},
                {'id': 'adfad', 'name': 'Tom'},
                {'id': 'ad34d', 'name': 'Tom'}])
        ]
         
    '''
    unique_keys = set([r[key] for r in L])
    return ([ (v, __build_list(L, key, v)) for v in unique_keys])

def repack_meta(aca_meta):
  '''
  Takes the results from the `aca_meta` function and repackages them in a suitable way for
  packaging the meta-data with raw data files. 

  This extracts and transforms the `rows` in the `aca_meta` dictionary. Only the 'rows' key is
  retained. 

  The aca_meta['rows'] is a list of rows in the SETI SignalDB that contain meta-data and preliminary 
  signal classifications. Each row also contains the 'container' and 'objectname' of the raw
  signal data file on which the preliminary analysis was performed. It is possible, and actually likely,
  to find multiple SignalDB rows pointing to the same raw data file. 

  What this function does is to "invert" this data so that for each raw data file, one 
  '''
  rows = copy.copy(aca_meta['rows'])
  for d in rows:
    d['cont-obj'] = d['container'] + '-' + d['objectname']

  data_by_contobj = __build_tuple_list(rows, 'cont-obj')

  #now, we remove the 'cont-obj' things from the dictionaries (we don't really *have* to do this, but it's nice to get rid of it)
  for dd in data_by_contobj:
      for d in  dd[1]:
          try: 
              del d['cont-obj']
          except KeyError:
              pass

  return data_by_contobj


def add_temp_url(row):
  #each row is a tuple, The first element is the cont-obj, the second element is a list of SignalDB rows
  cont, obj = row[0].split('-',1) #restore the container, objectname values.


  get_temp_url = 'https://setigopublic.mybluemix.net/v1/data/url/{}/{}'.format(cont, obj)
  r = requests.get(get_temp_url)
  return (cont, obj, row[1], r.status_code, r.json()['temp_url']) #row[1] is the list of signalDB rows.
