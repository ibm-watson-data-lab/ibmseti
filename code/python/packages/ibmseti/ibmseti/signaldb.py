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
    
This module is useful for reading the SignalDB data 
in our Softlayer ObjectStore. (As of now, this requires credentials only
available to IBM, SETI, and NASA researchers.)

'''

from pyspark.sql.types import StructField, StringType, StructType, DoubleType, LongType
from pyspark import SQLContext

def typeConversion(line):
  '''
  This map each valuein the RDD returned by SparkContext.textFile to a typed value.

  This function maps each value to an approprate string, double or long int.  

  It is possilbe for values to be 'NULL'. With this function, NULLs are converted to
  None for all types. 
  '''

  #this if/else lets one use this function either on the row before splitting
  #or after already have been split
  #this is not optimal, but somewhat useful for testing
    
  if type(line) == type([]):
    d = line
  else:
    d = line.strip('\n').split("\t")
        
  _stringIndexes = (0, 1, 2, 4, 12, 13, 20, 21, 22)
  _doubleIndexes = (5, 6, 7, 8, 9, 10, 11, 14, 16, 17, 18)
  _longIndexes = (3, 15, 19)  

  nullValue = None
  returnList = []

  cols = columns()
  lencols = len(cols)
  headerstart = cols[0].lower()
    
  for i in range(lencols): #only user the first 23 columns
    
    try:
        value = d[i]
    except IndexError:
        value = u'NULL'
    
    ## NOTE -- EARLY return here under this condition.
    if i == 0 and (value == u'NULL' or value == headerstart):
        returnList = ['null'] + [None for i in range(lencols-1)] 
        return returnList
    
    
    if value == u'NULL':
        returnList.append(nullValue) 
    
    else:    
      if i in _stringIndexes: 
        try:
          returnList.append(str(value))
        except:
          if i == 0:
            returnList.append('null')  #special case
          else:
            returnList.append(nullValue)

      elif i in _doubleIndexes:
        try:
          returnList.append(float(value))
        except:
          returnList.append(nullValue)

      elif i in _longIndexes: 
        try:
          returnList.append(long(value))
        except:
          returnList.append(nullValue)

  
  return returnList

def _structFieldArray():

    '''
    Note that this is the definitive source in this library for 
    the column names in the SignalDB.

    Also note that the DfitfHz/s column was changed from the original
    source on Softlayer. The '/' was removed --> DriftHzs
    '''
    return [StructField('UNIQUEID', StringType(), False),  #0
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
  return [f.name for f in _structFieldArray()]


def signalDbRDDFromFile(sparkContext, fileURL):

  return sparkContext.textFile(fileURL).map(typeConversion)


def signalDbDataFrameFromFile(sparkContext, fileURL):

  rdd = signalDbRDDFromFile(sparkContext, fileURL)

  return signalDbDataFrameFromSignalDbRDD(sparkContext, rdd)


def signalDbDataFrameFromSignalDbRDD(sparkContext, rdd):

  sqlContext = SQLContext(sparkContext)

  return sqlContext.createDataFrame(rdd, StructType(_structFieldArray()) )



