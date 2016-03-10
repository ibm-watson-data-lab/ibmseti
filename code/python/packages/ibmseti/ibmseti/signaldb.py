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

from pyspark.sql.types import StructField, StringType, StructType, DoubleType, LongType

#The user of this module needs to set this!
sparkContext = None
sqlContext = None

_stringIndexes = (0, 1, 2, 4, 12, 13, 20, 21, 22)
_doubleIndexes = (5, 6, 7, 8, 9, 10, 11, 14, 16, 17, 18)
_longIndexes = (3, 15, 19)

def typeConvToUnphysicalValue(d):
  '''
  This is to be used with getSignalDbDataFrame to map each value
  in the RDD returned by SparkContext.textFile to a typed value in the DataFrame.

  This function maps each value to an approprate string, double or long int.  

  It is possilbe for values to be 'NULL'. With this function, NULLs are converted to
  'NULL' for string types, and to unphysical values of -999999999.0 and
  -999999999 for doubles and long ints, respectively. 
  '''

  returnList = []
  for i in range(len(d)):    
    if i in _stringIndexes: 
      returnList.append(d[i])
    elif i in _doubleIndexes: 
      if d[i] == u'NULL':
          returnList.append(-999999999.0)
      else:
          returnList.append(float(d[i]))
    elif i in _longIndexes: 
      if d[i] == u'NULL':
          returnList.append(-999999999)
      else:
          returnList.append(long(d[i]))

  return returnList

def typeConvToNones(d):
  '''
  This is to be used with getSignalDbDataFrame to map each value
  in the RDD returned by SparkContext.textFile to a typed value in the DataFrame.

  This function maps each value to an approprate string, double or long int.  

  It is possilbe for values to be 'NULL'. With this function, NULLs are converted to
  None for all types. 
  '''

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
    return [StructField(field_name, StringType(), True) for field_name in columns()]
  else:
    '''
    Note that this is the definitive source in this library for 
    the column names in the SignalDB.

    Also note that the DfitfHz/s column was changed from the original
    source on Softlayer. The '/' was removed --> DriftHzs
    '''
    return [StructField('UniqueId', StringType(), True),   #0
            StructField('Time', StringType(), True),       #1
            StructField('ActTyp', StringType(), True),     #2
            StructField('TgtId', LongType(), True),        #3
            StructField('catalog', StringType(), True),    #4
            StructField('RA2000Hr', DoubleType(), True),   #5
            StructField('Dec2000Deg', DoubleType(), True), #6
            StructField('Power', DoubleType(), True),      #7
            StructField('SNR', DoubleType(), True),        #8
            StructField('FreqMHz', DoubleType(), True),    #9
            StructField('DriftHzs', DoubleType(), True),   #10
            StructField('WidHz', DoubleType(), True),      #11
            StructField('Pol', StringType(), True),        #12
            StructField('SigTyp', StringType(), True),     #13
            StructField('PPeriodS', DoubleType(), True),   #14
            StructField('NPul', LongType(), True),         #15
            StructField('IntTimeS', DoubleType(), True),   #16
            StructField('TscpAzDeg', DoubleType(), True),  #17
            StructField('TscpElDeg', DoubleType(), True),  #18
            StructField('BeamNo', LongType(), True),       #19
            StructField('SigClass', StringType(), True),   #20
            StructField('SigReason', StringType(), True),  #21
            StructField('CandReason', StringType(), True)  #22
           ]


def columns():
  '''
  Returns the names of the columns of the SignalDB 
  '''
  #This may seem slow since we're creating a bunch of objects,
  #but its trivial given the time for other data analysis.
  #It's definitely worth the convenience of having one definitive source of column names.
  return [f.name for f in _structFieldArray(False)]


def signalDbRDDFromObjectStore(swiftFileURL, typeConversion=typeConvToNones, columns=None):
  
  if columns is None:
    columns = columns()

  rdd = sparkContext.textFile(swiftFileURL)\
          .filter(lambda line: line.startswith(columns[0]) is False)\
          .map(lambda line:line.split("\t"))
  
  #convert the types
  if typeConversion is not None:
    rdd = rdd.map(typeConversion)
  
  return rdd   


def signalDbDataFrameFromObjectStore(swiftFileURL, typeConversion=typeConvToNones, columns=None, fieldStruct=None):

  rdd = signalDbRDDFromObjectStore(swiftFileURL, typeConversion=typeConversion, columns=columns)

  if fieldStruct is None:
    if typeConversion == None:
      fieldStruct = _structFieldArray(True)
    else:
      fieldStruct = _structFieldArray(False)


  sqlContext = SQLContext(sparkContext)

  return sqlContext.createDataFrame(rowRDD, schema)


def signalDbRowsForTarget(RA, DEC, maxRangeArc = 0.01, source='node'):
  '''
  For a given position in the sky, query the signalDB database and return the
  rows that match the position within a given range.

  If source == 'node', then query a Node Server backed with a database where SignalDB is found
  (possibly use Cloudant or an RDMS service available in Bluemix environment)

  Otherwise, assume that source is a swiftFileURL and pull data from SoftLayer.
  '''

  #We query our database -- either the SL object store or NodeJS webserver
  #backed by a Cloudant (or mySQL database)

  #If we use Cloudant here, we may need to do some post-query calculation to 
  #remove signalDB rows that are outside of our range (this is necessary due to the way
  #Cloudant works)

  #return the rows
  pass


def compampName(signalDbRow):
  '''
  Return the name of the compamp file for a particular row in the SignalDB.
  '''
  pass
  
