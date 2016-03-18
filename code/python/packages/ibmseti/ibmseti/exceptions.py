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
Module that contains common exception classes.
'''

class IBMSETIException(Exception):
    '''
    Provides a way to issue library specific exceptions.
    An IBMSETIException object is instantiated with a message.
    Note:  The intended use for this class is internal to the library.
    :param str msg: A message that describes the exception.
    '''
    def __init__(self, msg):
        super(IBMSETIException, self).__init__(msg)


class IBMSETISparkException(IBMSETIException):
    '''
    Provides a way to issue library specific exceptions
    that pertain to using Spark.  A IBMSETISparkException object is
    instantiated with a message.
    Note:  The intended use for this class is internal to the library.
    :param str msg: A message that describes the exception.
    '''
    def __init__(self, msg):
        super(IBMSETISparkException, self).__init__(msg)
