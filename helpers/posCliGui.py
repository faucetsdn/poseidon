#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
'''
Created on 27 Oct 2017
@author: dgrossman
'''



import sys
import os
import time



def posArray(character, string):
    return [pos for pos, char in enumerate(string) if char == character]

def parseLine(line):
    parts = line[71:].strip()

    toparse = parts
    
    if '*******' in toparse:
        return ((False,None))
    if toparse.startswith('None'):
        return ((False,None))
    if toparse[1] != ':':
        return ((False,None))
    pos = posArray(':',toparse)
    state_trans = toparse[pos[1]+1:pos[2]]
    manual = (toparse[pos[2]+1:])[1:-1]

    d = dict()
    kv = manual.split(',') 
    for item in kv:
        #print('item',item)
        key,value = item.split(':',1)   
        #print('k',key,'v',value)
        d[key.strip().lstrip()[1:-1]]=value.strip().lstrip()[1:-1]

    print('dict',d)
    endpoint_dict = d

    return((True,(endpoint_dict['ip-address'],state_trans)))


def getUpdateIterator():
    while True:

        found = False
        while not found:
            line = sys.stdin.readline().strip()
            if '====START' in line:
                found = True
                line = sys.stdin.readline().strip()

        found = False
        y_va = list()
        while not found:
            line = sys.stdin.readline().strip()
            if '====STOP' not in line:
                use, val = parseLine(line)
                if use:
                    y_va.append(val)
            else:
                yield(y_va)
                found = True
                y_va=list()
            

if __name__ == "__main__":
    for x in getUpdateIterator():
        print(chr(27) + "[2J")
        x.sort(key=lambda tup: tup[0])
        for lines in x:
            print(lines)
        time.sleep(2)
   
