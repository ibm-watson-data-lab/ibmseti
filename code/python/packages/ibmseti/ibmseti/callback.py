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
This module is used to send information back to IBM for tracking usage of 
this python package and analysis of SETI data. 

Please allow us to track usage of this service as it benefits both us and you.

You may, however, turn this off by modifying the code since it is open-source
under the Apache 2.0 License. 

TODO: Install SETI Deployment Tracker server on bluemix and then configure this
module to POST documents to that server to track usage.
Will attempt to access envars in Bluemix/Spark service to populate document.

'''
import requests
import datetime
import dateutil.tz
import json
import os

from .__info__ import __version__

_post_url = 'https://gadamc2.cloudant.com/seti_pythoncallbackevents'

_enabled = True

def disable():
  global _enabled
  _enabled = False

def enable():
  global _enabled
  _enabled = True

def postUsage(name):
  
  if _enabled is False:
    return

  nn  = datetime.datetime.now(dateutil.tz.tzlocal())

  doc = {
  'functioncall':name,
  'date':nn.isoformat(),
  'date_tz':nn.tzname(),
  'ibmseti_version':__version__,
  'user': os.environ.get('USER',None),
  'spark_tenant_id': os.environ.get('SPARK_TENANT_ID',None),
  'spark_master_ip': os.environ.get('SPARK_MASTER_IP',None),
  'doc_version':3,
  'type':'python-callback'
  }

  return requests.post(_post_url, headers={'Content-Type': 'application/json'},
    data=json.dumps(doc))

   

