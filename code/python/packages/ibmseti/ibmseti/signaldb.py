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
    Prints description of module including information about the columns (or
      at least a link to an external page that has that info.)
'''
import requests


def candidatesForTarget(RA, DEC, maxRangeDeg = 0.01, **kwargs):
  '''
  For a given position in the sky, query the signalDB database and return the
  rows that match the position within a given range.

  This queries a service backed with a database where SignalDB is found
  (possibly use Cloudant or an RDMS service available in Bluemix environment)

  Because we can build query views in the database for this simple function
  of retrieving rows from the SignalDB

  optional keyword arguments:
  url: the url of the signaldb data server

  '''

  db_url = kwargs.get('url','https://setisignaldb.mybluemix.net')
  
  payload = {
    'RA':RA,
    'DEC':DEC,
    'maxRangeDeg':maxRangeDeg
  }

  r = requests.post(
    db_url,
    params=payload
  )

  r.raise_for_status()

  return r.json()

def archiveCompamps():
  pass

def compampName(signalDbRow):
  '''
  Return the name of the compamp file for a particular row in the SignalDB.
  '''
  pass
  
