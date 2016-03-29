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

from pyspark.sql.types import StructField, StringType, StructType, DoubleType, LongType
from pyspark import SQLContext

from .callback import postUsage as _postUsage
from .exceptions import IBMSETISparkException

#The user of this module needs to set this!
sparkContext = None


def typeConvToNones(d):
  '''
  This is to be used with getSignalDbDataFrame to map each value
  in the RDD returned by SparkContext.textFile to a typed value in the DataFrame.

  This function maps each value to an approprate string, double or long int.  

  It is possilbe for values to be 'NULL'. With this function, NULLs are converted to
  None for all types. 
  '''

  _stringIndexes = (0, 1, 2, 4, 12, 13, 20, 21, 22)
  _doubleIndexes = (5, 6, 7, 8, 9, 10, 11, 14, 16, 17, 18)
  _longIndexes = (3, 15, 19)  

  returnList = []
  for i in range(len(d)):
    if d[i] == u'NULL':
        returnList.append(None) 
    else:    
      if i in _stringIndexes: 
        returnList.append(d[i])
      elif i in _doubleIndexes: 
        returnList.append(float(d[i]))
      elif i in _longIndexes: 
        returnList.append(long(d[i]))
  
  return returnList

def _structFieldArray(allStrings = False):

  if allStrings:
    # this is a horrible circular dependency!
    return [StructField(field_name, StringType(), True) for field_name in columns()]
  else:
    '''
    Note that this is the definitive source in this library for 
    the column names in the SignalDB.

    Also note that the DfitfHz/s column was changed from the original
    source on Softlayer. The '/' was removed --> DriftHzs
    '''
    return [StructField('UNIQUEID', StringType(), True),   #0
            StructField('TIME', StringType(), True),       #1
            StructField('ACTTYP', StringType(), True),     #2
            StructField('TGTID', LongType(), True),        #3
            StructField('CATALOG', StringType(), True),    #4
            StructField('RA2000HR', DoubleType(), True),   #5
            StructField('DEC2000DEG', DoubleType(), True), #6
            StructField('POWER', DoubleType(), True),      #7
            StructField('SNR', DoubleType(), True),        #8
            StructField('FREQMHZ', DoubleType(), True),    #9
            StructField('DRIFTHZS', DoubleType(), True),   #10
            StructField('WIDHZ', DoubleType(), True),      #11
            StructField('POL', StringType(), True),        #12
            StructField('SIGTYP', StringType(), True),     #13
            StructField('PPERIODS', DoubleType(), True),   #14
            StructField('NPUL', LongType(), True),         #15
            StructField('INTTIMES', DoubleType(), True),   #16
            StructField('TSCPAZDEG', DoubleType(), True),  #17
            StructField('TSCPELDEG', DoubleType(), True),  #18
            StructField('BEAMNO', LongType(), True),       #19
            StructField('SIGCLASS', StringType(), True),   #20
            StructField('SIGREASON', StringType(), True),  #21
            StructField('CANDREASON', StringType(), True)  #22
           ]


def columns():
  '''
  Returns the names of the columns of the SignalDB 
  '''
  #This may seem slow since we're creating a bunch of objects,
  #but its trivial given the time for other data analysis.
  #It's definitely worth the convenience of having one definitive source of column names.
  return [f.name for f in _structFieldArray(False)]


def signalDbRDDFromObjectStore(swiftFileURL, typeConversion=typeConvToNones, cols=None):
  
  if sparkContext is None:
    raise IBMSETISparkException('ibmseti.signaldb.sparkContext is None.')

  if cols is None:
    cols = columns()
  
  lencols = len(cols)
  headerstart = cols[0].lower()

  rdd = sparkContext.textFile(swiftFileURL)\
          .filter(lambda line: line.lower().startswith(headerstart) is False)\
          .filter(lambda line: len(line.split("\t")) == lencols)\
          .map(lambda line:line.split("\t"))
  
  #convert the types
  if typeConversion is not None:
    rdd = rdd.map(typeConversion)
  
  return rdd   


def signalDbDataFrameFromObjectStore(swiftFileURL, typeConversion=typeConvToNones, cols=None, fieldStruct=None):

  rdd = signalDbRDDFromObjectStore(swiftFileURL, typeConversion=typeConversion, cols=cols)

  if fieldStruct is None:
    if typeConversion == None:
      fieldStruct = _structFieldArray(allStrings=True)
    else:
      fieldStruct = _structFieldArray(allStrings=False)

  sqlContext = SQLContext(sparkContext)
  schema = StructType(fieldStruct)

  return sqlContext.createDataFrame(rdd, schema)


def signalDbRowsForTarget(RA, DEC, SigClass=None, maxRangeArc = 0.01):
  '''
  For a given position in the sky, query the signalDB database and return the
  rows that match the position within a given range.

  This queries a service backed with a database where SignalDB is found
  (possibly use Cloudant or an RDMS service available in Bluemix environment)

  Because we can build query views in the database for this simple function
  of retrieving rows from the SignalDB
  '''

  _db_url = 'https://gadamc2.cloudant.com/signaldb'


  _postUsage('signalDbRowsForTarget')
  pass


def compampName(signalDbRow):
  '''
  Return the name of the compamp file for a particular row in the SignalDB.
  '''
  pass
  
