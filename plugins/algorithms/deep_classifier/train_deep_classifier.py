#!/usr/bin/env python
#
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
"""
Created on 24 August 2016
@author: bradh41, tlanham

Deep learning module to classify
packets based on hex headers.

rabbitmq:
    host:       poseidon-rabbit
    exchange:   topic-poseidon-internal
    queue:
"""
import time
import os
import ast
import json
import subprocess
import cPickle
import sys
import binascii
import multiprocessing as mp
from itertools import chain
from collections import OrderedDict
import logging
import ipaddress

import numpy as np
import random
from copy import copy

import blocks
from blocks.bricks import Linear, Softmax, Softplus, NDimensionalSoftmax, BatchNormalizedMLP, Rectifier, Logistic, Tanh, MLP
from blocks.bricks.recurrent import GatedRecurrent, Fork, LSTM
from blocks.initialization import Constant, IsotropicGaussian, Identity, Uniform
from blocks.bricks.cost import BinaryCrossEntropy, CategoricalCrossEntropy
from blocks.filter import VariableFilter
from blocks.roles import PARAMETER
from blocks.graph import ComputationGraph

import theano
from theano import tensor as T


module_logger = logging.getLogger(__name__)


def rabbit_init(host, exchange, queue_name):  # pragma: no cover
    """
    Connects to rabbitmq using the given hostname,
    exchange, and queue. Retries on failure until success.
    Binds routing keys appropriate for module, and returns
    the channel and connection.
    """
    wait = True
    while wait:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, type='topic')
            result = channel.queue_declare(queue=queue_name, exclusive=True)
            wait = False
            module_logger.info('connected to rabbitmq...')
            print 'connected to rabbitmq...'
        except Exception, e:
            print 'waiting for connection to rabbitmq...'
            print str(e)
            module_logger.info(str(e))
            module_logger.info('waiting for connection to rabbitmq...')
            time.sleep(2)
            wait = True

    binding_keys = sys.argv[1:]
    if not binding_keys:
        ostr = 'Usage: %s [binding_key]...' % (sys.argv[0])
        module_logger.error(ostr)
        sys.exit(1)

    for binding_key in binding_keys:
        channel.queue_bind(exchange=exchange,
                           queue=queue_name,
                           routing_key=binding_key)

    module_logger.info(' [*] Waiting for logs. To exit press CTRL+C')
    return channel, connection


os.environ['THEANO_FLAGS'] = 'floatX=float32,device=cpu'
sys.setrecursionlimit(100000)

maxPackets = 2
packetTimeSteps = 80
loadPrepedData = False
dataPath = '/data/fs4/home/bradh/bigFlows.pickle'

packetReverse = False
padOldTimeSteps = True

runname = 'hredClassify2smallpackets'
rnnType = 'gru'  # gru or lstm

wtstd = 0.2
dimIn = 257  # hex has 256 characters + the <EOP> character
dim = 100  # dimension reduction size
batch_size = 20
numClasses = 4
clippings = 1

epochs = 1
lr = 0.0001
decay = 0.9
trainPercent = 0.9

module_logger = logging.getLogger(__name__)


def parse_header(line):  # pragma: no cover
    ret_dict = {}
    h = line.split()
    if h[2] == 'IP6':
        """
        Conditional formatting based on ethernet type.
        IPv4 format: 0.0.0.0.port
        IPv6 format (one of many): 0:0:0:0:0:0.port
        """
        ret_dict['src_port'] = h[3].split('.')[-1]
        ret_dict['src_ip'] = h[3].split('.')[0]
        ret_dict['dest_port'] = h[5].split('.')[-1].split(':')[0]
        ret_dict['dest_ip'] = h[5].split('.')[0]
    else:
        if len(h[3].split('.')) > 4:
            ret_dict['src_port'] = h[3].split('.')[-1]
            ret_dict['src_ip'] = '.'.join(h[3].split('.')[:-1])
        else:
            ret_dict['src_ip'] = h[3]
            ret_dict['src_port'] = ''
        if len(h[5].split('.')) > 4:
            ret_dict['dest_port'] = h[5].split('.')[-1].split(':')[0]
            ret_dict['dest_ip'] = '.'.join(h[5].split('.')[:-1])
        else:
            ret_dict['dest_ip'] = h[5].split(':')[0]
            ret_dict['dest_port'] = ''
    return ret_dict


def parse_data(line):  # pragma: no cover
    ret_str = ''
    h, d = line.split(':', 1)
    ret_str = d.strip().replace(' ', '')
    return ret_str


def process_packet(output):  # pragma: no cover
    # TODO!! throws away the first packet!
    ret_header = {}
    ret_dict = {}
    ret_data = ''
    hasHeader = False
    for line in output:
        line = line.strip()
        if line:
            if not line.startswith('0x'):
                # header line
                if ret_dict and ret_data:
                    # about to start new header, finished with hex
                    ret_dict['data'] = ret_data
                    yield ret_dict
                    ret_dict.clear()
                    ret_header.clear()
                    ret_data = ''
                    hasHeader = False

                # parse next header
                try:
                    ret_header = parse_header(line)
                    ret_dict.update(ret_header)
                    hasHeader = True
                except:
                    ret_header.clear()
                    ret_dict.clear()
                    ret_data = ''
                    hasHeader = False

            else:
                # hex data line
                if hasHeader:
                    data = parse_data(line)
                    ret_data = ret_data + data
                else:
                    continue


def is_clean_packet(packet):  # pragma: no cover
    """
    Returns whether or not the parsed packet is valid
    or not. Checks that both the src and dest
    ports are integers. Checks that src and dest IPs
    are valid address formats. Checks that packet data
    is hex. Returns True if all tests pass, False otherwise.
    """
    if not packet['src_port'].isdigit(): return False
    if not packet['dest_port'].isdigit(): return False

    if packet['src_ip'].isalpha(): return False
    if packet['dest_ip'].isalpha(): return False

    if 'data' in packet:
        try:
            int(packet['data'], 16)
        except:
            return False

    return True


def order_keys(hexSessionDict):  # pragma: no cover
    orderedKeys = []

    for key in sorted(hexSessionDict.keys(), key=lambda key: hexSessionDict[key][1]):
        orderedKeys.append(key)

    return orderedKeys


def read_pcap(path):  # pragma: no cover
    print 'starting reading pcap file'
    hex_sessions = {} 
    proc = subprocess.Popen('tcpdump -nn -tttt -xx -r '+path,
                            shell=True,
                            stdout=subprocess.PIPE)
    insert_num = 0  # keeps track of insertion order into dict
    for packet in process_packet(proc.stdout):
        if not is_clean_packet(packet):
            continue
        if 'data' in packet:
            key = (packet['src_ip']+":"+packet['src_port'], packet['dest_ip']+":"+packet['dest_port'])
            rev_key = (key[1], key[0])
            if key in hex_sessions:
                hex_sessions[key][0].append(packet['data'])
            elif rev_key in hex_sessions:
                hex_sessions[rev_key][0].append(packet['data'])
            else:
                hex_sessions[key] = ([packet['data']], insert_num)
                insert_num += 1

    print 'finished reading pcap file'
    return hex_sessions


def pickleFile(thing2save, file2save2=None, filePath='/work/notebooks/drawModels/', fileName='myModels'):  # pragma: no cover

    if file2save2 is None:
        f = file(filePath+fileName+'.pickle', 'wb')
    else:
        f = file(filePath+file2save2, 'wb')

    cPickle.dump(thing2save, f, protocol=cPickle.HIGHEST_PROTOCOL)
    f.close()


def loadFile(filePath):  # pragma: no cover
    file2open = file(filePath, 'rb')
    loadedFile = cPickle.load(file2open)
    file2open.close()
    return loadedFile


def removeBadSessionizer(hexSessionDict, saveFile=False, dataPath=None, fileName=None):  # pragma: no cover
    for ses in hexSessionDict.keys():
        paclens = []
        for pac in hexSessionDict[ses][0]:
            paclens.append(len(pac))
        if np.min(paclens)<80:
            del hexSessionDict[ses]

    if saveFile:
        print 'pickling sessions'
        pickleFile(hexSessionDict, filePath=dataPath, fileName=fileName)

    return hexSessionDict


# Making the hex dictionary
def hexTokenizer():  # pragma: no cover
    hexstring = '''0, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D, E, F,
                   10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 1A, 1B,
                   1C, 1D, 1E, 1F, 20, 21, 22, 23, 24, 25, 26, 27,
                   28, 29, 2A, 2B, 2C, 2D, 2E, 2F, 30, 31, 32, 33,
                   34, 35, 36, 37, 38, 39, 3A, 3B, 3C, 3D, 3E, 3F,
                   40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 4A, 4B,
                   4C, 4D, 4E, 4F, 50, 51, 52, 53, 54, 55, 56, 57,
                   58, 59, 5A, 5B, 5C, 5D, 5E, 5F, 60, 61, 62, 63,
                   64, 65, 66, 67, 68, 69, 6A, 6B, 6C, 6D, 6E, 6F,
                   70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 7A, 7B,
                   7C, 7D, 7E, 7F, 80, 81, 82, 83, 84, 85, 86, 87,
                   88, 89, 8A, 8B, 8C, 8D, 8E, 8F, 90, 91, 92, 93,
                   94, 95, 96, 97, 98, 99, 9A, 9B, 9C, 9D, 9E, 9F,
                   A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, AA, AB,
                   AC, AD, AE, AF, B0, B1, B2, B3, B4, B5, B6, B7,
                   B8, B9, BA, BB, BC, BD, BE, BF, C0, C1, C2, C3,
                   C4, C5, C6, C7, C8, C9, CA, CB, CC, CD, CE, CF,
                   D0, D1, D2, D3, D4, D5, D6, D7, D8, D9, DA, DB,
                   DC, DD, DE, DF, E0, E1, E2, E3, E4, E5, E6, E7,
                   E8, E9, EA, EB, EC, ED, EE, EF, F0, F1, F2, F3,
                   F4, F5, F6, F7, F8, F9, FA, FB, FC, FD, FE, FF'''.replace('\t', '')

    hexList = [x.strip() for x in hexstring.lower().split(',')]
    hexList.append('<EOP>')  # End Of Packet token
    hexDict = {}

    for key, val in enumerate(hexList):
        if len(val) == 1:
            val = '0'+val
        hexDict[val] = key  #dictionary k=hex, v=int  

    return hexDict


def srcIpDict(hexSessionDict):  # pragma: no cover
    ''' 
    input: dictionary of key = sessions, value = list of HEX HEADERS of packets in session
    output: dictionary of key = source IP, value/subkey = dictionary of destination IPs, 
                                           subvalue = [[sport], [dport], [plen], [protocol]]
    
    '''
    srcIpDict = OrderedDict()   
    uniqIPs = [] #some ips are dest only. this will collect all ips, not just srcIpDict.keys()
    
    for session in hexSessionDict.keys():
        
        for rawpacket in hexSessionDict[session][0]:
            packet = copy(rawpacket)
            
            dstIpSubDict = {}
            
            sourceMAC = packet[:12]
            destMAC = packet[12:24]
            srcip = packet[52:60]
            dstip = packet[60:68]
            sport = packet[68:72]
            dport = packet[72:76]
            plen = packet[32:36]
            protocol = packet[46:48]
            
            uniqIPs = list(set(uniqIPs) | set([dstip, srcip]))

            if srcip not in srcIpDict:
                dstIpSubDict[dstip] = [[sport], [dport], [plen], [protocol], [sourceMAC], [destMAC]]
                srcIpDict[srcip] = dstIpSubDict

            if dstip not in srcIpDict[srcip]:    
                srcIpDict[srcip][dstip] = [[sport], [dport], [plen], [protocol], [sourceMAC], [destMAC]]
            else:
                srcIpDict[srcip][dstip][0].append(sport)
                srcIpDict[srcip][dstip][1].append(dport)
                srcIpDict[srcip][dstip][2].append(plen)
                srcIpDict[srcip][dstip][3].append(protocol)
                srcIpDict[srcip][dstip][4].append(sourceMAC)
                srcIpDict[srcip][dstip][5].append(destMAC)
                
    return srcIpDict, uniqIPs


def dictUniquerizer(dictOdictsOlistOlists):  # pragma: no cover
    '''
    input: dictionary of dictionaries that have a list of lists 
           ex. srcIpDict[srcip][dstip] = [[sport], [dport], [plen], [protocol]]
    output: dictionary of dictionaries with list of lists with unique items in the final sublist
    
    WARNING: will overwrite your input dictionary. Make a copy if you want to preserve dictOdictsOlistOlists.
    '''
    #dictCopy
    for key in dictOdictsOlistOlists.keys():
        for subkey in dictOdictsOlistOlists[key].keys():
            for sublist in xrange(len(dictOdictsOlistOlists[key][subkey])):
                dictOdictsOlistOlists[key][subkey][sublist] = list(set(dictOdictsOlistOlists[key][subkey][sublist]))
    
    return dictOdictsOlistOlists


def ipDirSwitcher(hexSessionList):  # pragma: no cover
    '''
    switches both ip and mac addresses
    input is a list of packets from ONE session
    '''
    
    ipdirsession = []
        
    for p in hexSessionList:
        sourceMAC = p[:12]
        destMAC = p[12:24]
        sourceIP = p[52:60]
        destIP = p[60:68]

        ipdirsession.append(destMAC + sourceMAC + p[24:52] + destIP + sourceIP + p[68:])

    return ipdirsession


def portDirSwitcher(hexSessionList):  # pragma: no cover
    '''
    input is a list of packets from ONE session
    '''
    
    portdirsession = []
    
    for p in hexSessionList:
        sport = p[68:72]
        dport = p[72:76]

        portdirsession.append(p[:68]+dport+sport+p[76:])

    return portdirsession


def dstIpSwapOut(hexSessionList, dictOcoms, listOuniqIPs):  # pragma: no cover    
    swapSession = []
    sourceMAC = hexSessionList[0][:12]#[0] assumes first packet contains true initial direction
    destMAC = hexSessionList[0][12:24]
    srcip = hexSessionList[0][52:60] 
    dstip = hexSessionList[0][60:68]
    normDstIps = dictOcoms[srcip].keys()+[srcip] #get list of dstIPs that srcIP talks to
    abbynormIps = copy(listOuniqIPs)
    
    for normIp in normDstIps:
        abbynormIps.remove(normIp) #remove itself and know dstIPs from list of consideration.
    
    abbynormDestIp = random.sample(abbynormIps, 1)[0] #get random ip that srcip doesn't talk to

    for rawpacket in hexSessionList:
        packet = copy(rawpacket)
        
        if packet[60:68] == dstip:
            packet = packet[:60] + abbynormDestIp + packet[68:] #
        elif packet[60:68] == srcip:
            packet = packet[:52] + abbynormDestIp + packet[60:] #in case direction switches for packet in session
            
        swapSession.append(packet)

    return swapSession


def oneHot(index, granular = 'hex'):  # pragma: no cover
    if granular == 'hex':
        vecLen = 257
    else:
        vecLen = 17
    
    zeroVec = np.zeros(vecLen)
    zeroVec[index] = 1.0
    
    return zeroVec


def oneSessionEncoder(sessionPackets, hexDict, maxPackets=2, packetTimeSteps=100,
                      packetReverse=False, charLevel=False, padOldTimeSteps=True):  # pragma: no cover
    
    sessionCollect = []
    packetCollect = []
    
    if charLevel:
        vecLen = 17
    else:
        vecLen = 257
    
    if len(sessionPackets) > maxPackets: #crop the number of sessions to maxPackets
        sessionList = copy(sessionPackets[:maxPackets])
    else:
        sessionList = copy(sessionPackets)

    for packet in sessionList:
        packet = [hexDict[packet[i:i+2]] for i in xrange(0,len(packet)-2+1,2)]
            
        if len(packet) >= packetTimeSteps: #crop packet to length packetTimeSteps
            packet = packet[:packetTimeSteps]
            packet = packet+[256] #add <EOP> end of packet token
        else:
            packet = packet+[256] #add <EOP> end of packet token
        
        packetCollect.append(packet)
        
        pacMat = np.array([oneHot(x) for x in packet]) #one hot encoding of packet into a matrix
        pacMatLen = len(pacMat)
        
        #padding packet
        if packetReverse:
            pacMat = pacMat[::-1]

        if pacMatLen < packetTimeSteps:
            #pad by stacking zeros on top of data so that earlier timesteps do not have information
            #padding the packet such that zeros are after the actual info for better translation
            if padOldTimeSteps:
                pacMat = np.vstack( ( np.zeros((packetTimeSteps-pacMatLen,vecLen)), pacMat) ) 
            else:
                pacMat = np.vstack( (pacMat, np.zeros((packetTimeSteps-pacMatLen,vecLen))) ) 

        if pacMatLen > packetTimeSteps:
            pacMat = pacMat[:packetTimeSteps, :]

        sessionCollect.append(pacMat)

    #padding session
    sessionCollect = np.asarray(sessionCollect, dtype=theano.config.floatX)
    numPacketsInSession = sessionCollect.shape[0]
    if numPacketsInSession < maxPackets:
        #pad sessions to fit the
        sessionCollect = np.vstack( (sessionCollect,np.zeros((maxPackets-numPacketsInSession,
                                                             packetTimeSteps, vecLen))) )
    
    return sessionCollect, packetCollect


def floatX(X):  # pragma: no cover
    return np.asarray(X, dtype=theano.config.floatX)


def dropout(X, p=0.):  # pragma: no cover
    if p != 0:
        retain_prob = 1 - p
        X = X / retain_prob * srng.binomial(X.shape, p=retain_prob, dtype=theano.config.floatX)
    return X


def clip_norm(g, c, n):  # pragma: no cover
    '''n is the norm, c is the threashold, and g is the gradient'''
    if c > 0: 
        g = T.switch(T.ge(n, c), g*c/n, g) 
    return g


def clip_norms(gs, c):  # pragma: no cover
    norm = T.sqrt(sum([T.sum(g**2) for g in gs]))
    return [clip_norm(g, c, norm) for g in gs]


def max_norm(p, maxnorm=0.):  # pragma: no cover
    if maxnorm > 0:
        norms = T.sqrt(T.sum(T.sqr(p), axis=0))
        desired = T.clip(norms, 0, maxnorm)
        p = p * (desired/ (1e-7 + norms))
    return p


def gradient_regularize(p, g, l1=0., l2=0.):  # pragma: no cover
    g += p * l2
    g += T.sgn(p) * l1
    return g


def weight_regularize(p, maxnorm=0.):  # pragma: no cover
    p = max_norm(p, maxnorm)
    return p


def Adam(params, cost, lr=0.0002, b1=0.1, b2=0.001, e=1e-8, l1=0., l2=0., maxnorm=0., c=8):  # pragma: no cover

    updates = []
    grads = T.grad(cost, params)
    grads = clip_norms(grads, c)

    i = theano.shared(floatX(0.))
    i_t = i + 1.
    fix1 = 1. - b1**(i_t)
    fix2 = 1. - b2**(i_t)
    lr_t = lr * (T.sqrt(fix2) / fix1)

    for p, g in zip(params, grads):
        m = theano.shared(p.get_value() * 0.)
        v = theano.shared(p.get_value() * 0.)
        m_t = (b1 * g) + ((1. - b1) * m)
        v_t = (b2 * T.sqr(g)) + ((1. - b2) * v)
        g_t = m_t / (T.sqrt(v_t) + e)
        g_t = gradient_regularize(p, g_t, l1=l1, l2=l2)
        p_t = p - (lr_t * g_t)
        p_t = weight_regularize(p_t, maxnorm=maxnorm)

        updates.append((m, m_t))
        updates.append((v, v_t))
        updates.append((p, p_t))

    updates.append((i, i_t))

    return updates


def RMSprop(cost, params, lr=0.001, l1=0., l2=0., maxnorm=0., rho=0.9, epsilon=1e-6, c=8):  # pragma: no cover

    grads = T.grad(cost, params)
    grads = clip_norms(grads, c)
    updates = []

    for p, g in zip(params, grads):
        g = gradient_regularize(p, g, l1=l1, l2=l2)
        acc = theano.shared(p.get_value() * 0.)
        acc_new = rho * acc + (1 - rho) * g ** 2
        updates.append((acc, acc_new))
 
        updated_p = p - lr * (g / T.sqrt(acc_new + epsilon))
        updated_p = weight_regularize(updated_p, maxnorm=maxnorm)
        updates.append((p, updated_p))
    return updates


def predictClass(predictFun, hexSessionsDict, comsDict, uniqIPs, hexDict, hexSessionsKeys,
                 numClasses=4, trainPercent=0.9, dimIn=257, maxPackets=2,
                 packetTimeSteps=16, padOldTimeSteps=True):  # pragma: no cover
    
    testCollect = []
    predtargets = []
    actualtargets = []
    trainIndex = int(len(hexSessionsKeys)*trainPercent)
        
    start = trainIndex
    end = len(hexSessionsKeys)
        
    trainingSessions = []
    trainingTargets = []

    for trainKey in range(start, end):
        sessionForEncoding = list(hexSessionsDict[hexSessionsKeys[trainKey]][0])

        adversaryList = [sessionForEncoding, 
                         dstIpSwapOut(sessionForEncoding, comsDict, uniqIPs), 
                         portDirSwitcher(sessionForEncoding), 
                         ipDirSwitcher(sessionForEncoding)]
        abbyIndex = random.sample(range(len(adversaryList)), 1)[0]
        abbyOneHotSes = oneSessionEncoder(adversaryList[abbyIndex],
                                          hexDict=hexDict,
                                          packetReverse=packetReverse, 
                                          padOldTimeSteps=padOldTimeSteps, 
                                          maxPackets=maxPackets, 
                                          packetTimeSteps=packetTimeSteps)

        targetClasses = [0]*numClasses
        targetClasses[abbyIndex] = 1
        abbyTarget = np.array(targetClasses, dtype=theano.config.floatX)
        trainingSessions.append(abbyOneHotSes[0])
        trainingTargets.append(abbyTarget)

    sessionsMinibatch = np.asarray(trainingSessions, dtype=theano.config.floatX).reshape((-1, packetTimeSteps, 1, dimIn))
    targetsMinibatch = np.asarray(trainingTargets, dtype=theano.config.floatX)

    predcostfun = predictFun(sessionsMinibatch)
    testCollect.append(np.mean(np.argmax(predcostfun,axis=1) == np.argmax(targetsMinibatch, axis=1)))

    predtargets = np.argmax(predcostfun,axis=1)
    actualtargets = np.argmax(targetsMinibatch, axis=1)

    print "TEST accuracy:         ", np.mean(testCollect)
    print

    return predtargets, actualtargets, np.mean(testCollect)


def binaryPrecisionRecall(predictions, targets, numClasses = 4):  # pragma: no cover
    for cla in range(numClasses):
        
        confustop = np.array([])
        confusbottom = np.array([])

        predictions = np.asarray(predictions).flatten()
        targets = np.asarray(targets).flatten()

        pred1 = np.where(predictions == cla)
        pred0 = np.where(predictions != cla)
        target1 = np.where(targets == cla)
        target0 = np.where(targets != cla)

        truePos = np.intersect1d(pred1[0], target1[0]).shape[0]
        trueNeg = np.intersect1d(pred0[0], target0[0]).shape[0]
        falsePos = np.intersect1d(pred1[0], target0[0]).shape[0]
        falseNeg = np.intersect1d(pred0[0], target1[0]).shape[0]

        top = np.append(confustop, (truePos, falsePos))
        bottom = np.append(confusbottom, (falseNeg, trueNeg))
        confusionMatrix = np.vstack((top, bottom))
        
        precision = float(truePos)/(truePos + falsePos + 0.00001)  # 1 - (how much junk did we give user)
        recall = float(truePos)/(truePos + falseNeg + 0.00001)  # 1 - (how much good stuff did we miss)
        f1 = 2*((precision*recall)/(precision+recall+0.00001))

        module_logger.info('class '+str(cla)+' precision: ', precision)
        module_logger.info('class '+str(cla)+' recall:    ', recall)
        module_logger.info('class '+str(cla)+' f1:        ', f1)


def training(runname, rnnType, maxPackets, packetTimeSteps, packetReverse, padOldTimeSteps, wtstd, 
             lr, decay, clippings, dimIn, dim, numClasses, batch_size, epochs, 
             trainPercent, dataPath, loadPrepedData=False):  # pragma: no cover
    print locals()
    print
    
    X = T.tensor4('inputs')
    Y = T.matrix('targets')
    linewt_init = IsotropicGaussian(wtstd)
    line_bias = Constant(1.0)
    rnnwt_init = IsotropicGaussian(wtstd)
    rnnbias_init = Constant(0.0)
    classifierWts = IsotropicGaussian(wtstd)

    learning_rateClass = theano.shared(np.array(lr, dtype=theano.config.floatX))
    learning_decay = np.array(decay, dtype=theano.config.floatX)
    
    ###DATA PREP
    print 'loading data'
    if loadPrepedData:
        hexSessions = loadFile(dataPath)

    else:
        hexSessions = read_pcap(dataPath)
        hexSessions = removeBadSessionizer(hexSessions)

    numSessions = len(hexSessions)
    print str(numSessions) + ' sessions found'
    hexSessionsKeys = order_keys(hexSessions)
    hexDict = hexTokenizer()
    
    print 'creating dictionary of ip communications'
    comsDict, uniqIPs = srcIpDict(hexSessions)
    comsDict = dictUniquerizer(comsDict)
     
    print 'initializing network graph'
    ###ENCODER
    if rnnType == 'gru':
        rnn = GatedRecurrent(dim=dim, weights_init = rnnwt_init, biases_init = rnnbias_init, name = 'gru')
        dimMultiplier = 2
    else:
        rnn = LSTM(dim=dim, weights_init = rnnwt_init, biases_init = rnnbias_init, name = 'lstm')
        dimMultiplier = 4

    fork = Fork(output_names=['linear', 'gates'],
                name='fork', input_dim=dimIn, output_dims=[dim, dim * dimMultiplier], 
                weights_init = linewt_init, biases_init = line_bias)

    ###CONTEXT
    if rnnType == 'gru':
        rnnContext = GatedRecurrent(dim=dim, weights_init = rnnwt_init, 
                                    biases_init = rnnbias_init, name = 'gruContext')
    else:
        rnnContext = LSTM(dim=dim, weights_init = rnnwt_init, biases_init = rnnbias_init, 
                          name = 'lstmContext')

    forkContext = Fork(output_names=['linearContext', 'gatesContext'],
                name='forkContext', input_dim=dim, output_dims=[dim, dim * dimMultiplier], 
                weights_init = linewt_init, biases_init = line_bias)

    forkDec = Fork(output_names=['linear', 'gates'],
                name='forkDec', input_dim=dim, output_dims=[dim, dim*dimMultiplier], 
                weights_init = linewt_init, biases_init = line_bias)

    #CLASSIFIER
    bmlp = BatchNormalizedMLP( activations=[Logistic(),Logistic()], 
               dims=[dim, dim, numClasses],
               weights_init=classifierWts,
               biases_init=Constant(0.0001) )

    #initialize the weights in all the functions
    fork.initialize()
    rnn.initialize()
    forkContext.initialize()
    rnnContext.initialize()
    forkDec.initialize()
    bmlp.initialize()

    def onestepEnc(X):
        data1, data2 = fork.apply(X) 

        if rnnType == 'gru':
            hEnc = rnn.apply(data1, data2) 
        else:
            hEnc, _ = rnn.apply(data2)

        return hEnc

    hEnc, _ = theano.scan(onestepEnc, X) #(mini*numPackets, packetLen, 1, hexdictLen)
    hEncReshape = T.reshape(hEnc[:,-1], (-1, maxPackets, 1, dim)) #[:,-1] takes the last rep for each packet
                                                                 #(mini, numPackets, 1, dimReduced)
    def onestepContext(hEncReshape):

        data3, data4 = forkContext.apply(hEncReshape)

        if rnnType == 'gru':
            hContext = rnnContext.apply(data3, data4)
        else:
            hContext, _ = rnnContext.apply(data4)

        return hContext

    hContext, _ = theano.scan(onestepContext, hEncReshape)
    hContextReshape = T.reshape(hContext[:,-1], (-1,dim))

    data5, _ = forkDec.apply(hContextReshape)

    pyx = bmlp.apply(data5)
    softmax = Softmax()
    softoutClass = softmax.apply(pyx)
    costClass = T.mean(CategoricalCrossEntropy().apply(Y, softoutClass))

    #CREATE GRAPH
    cgClass = ComputationGraph([costClass])
    paramsClass = VariableFilter(roles = [PARAMETER])(cgClass.variables)
    updatesClass = Adam(paramsClass, costClass, learning_rateClass, c=clippings) 

    module_logger.info('starting graph compilation')
    classifierTrain = theano.function([X,Y], [costClass, hEnc, hContext, pyx, softoutClass], 
                                      updates=updatesClass, allow_input_downcast=True)
    classifierPredict = theano.function([X], softoutClass, allow_input_downcast=True)
    module_logger.info('graph compilation finished')
    print 'finished graph compilation'

    trainIndex = int(len(hexSessionsKeys)*trainPercent)

    epochCost = []
    gradNorms = []
    trainAcc = []
    testAcc = []

    costCollect = []
    trainCollect = []

    module_logger.info('beginning training')
    iteration = 0
    #epoch
    for epoch in xrange(epochs):

        #iteration/minibatch
        for start, end in zip(range(0, trainIndex,batch_size),
                              range(batch_size, trainIndex, batch_size)):

            trainingTargets = []
            trainingSessions = []

            #create one minibatch with 0.5 normal and 0.5 abby normal traffic
            for trainKey in range(start, end):
                sessionForEncoding = list(hexSessions[hexSessions.keys()[trainKey]][0])

                adversaryList = [sessionForEncoding, 
                                 dstIpSwapOut(sessionForEncoding, comsDict, uniqIPs), 
                                 portDirSwitcher(sessionForEncoding), 
                                 ipDirSwitcher(sessionForEncoding)]
                abbyIndex = random.sample(range(len(adversaryList)), 1)[0]
                
                abbyOneHotSes = oneSessionEncoder(adversaryList[abbyIndex],
                                                  hexDict = hexDict,
                                                  packetReverse=packetReverse, 
                                                  padOldTimeSteps = padOldTimeSteps, 
                                                  maxPackets = maxPackets, 
                                                  packetTimeSteps = packetTimeSteps)

                targetClasses = [0]*numClasses
                targetClasses[abbyIndex] = 1
                abbyTarget = np.array(targetClasses, dtype=theano.config.floatX)
                trainingSessions.append(abbyOneHotSes[0])
                trainingTargets.append(abbyTarget)

            sessionsMinibatch = np.asarray(trainingSessions).reshape((-1, packetTimeSteps, 1, dimIn))
            targetsMinibatch = np.asarray(trainingTargets)

            costfun = classifierTrain(sessionsMinibatch, targetsMinibatch)

            if iteration % (numSessions / (10 * batch_size)) == 0:
                costCollect.append(costfun[0])
                trainCollect.append(np.mean(np.argmax(costfun[-1],axis=1) == np.argmax(targetsMinibatch, axis=1)))
                module_logger.info('   Iteration: ', iteration)
                module_logger.info('   Cost: ', np.mean(costCollect))
                module_logger.info('   TRAIN accuracy: ', np.mean(trainCollect))
                print '   Iteration: ', iteration
                print '   Cost: ', np.mean(costCollect)
                print '   TRAIN accuracy: ', np.mean(trainCollect)

            iteration+=1

            #testing accuracy
            if iteration % (numSessions / (2 * batch_size)) == 0:
                predtar, acttar, testCollect = predictClass(classifierPredict, hexSessions, comsDict, uniqIPs, hexDict,
                                                            hexSessionsKeys,
                                                            numClasses, trainPercent, dimIn, maxPackets, packetTimeSteps,
                                                            padOldTimeSteps)
                binaryPrecisionRecall(predtar, acttar)
                module_logger.info(str(testCollect))

            #save the models
            if iteration % (numSessions / (5 * batch_size)) == 0:
                pickleFile(classifierTrain, filePath='',
                            fileName=runname+'TRAIN'+str(iteration))
                pickleFile(classifierPredict, filePath='',
                            fileName=runname+'PREDICT'+str(iteration))

        epochCost.append(np.mean(costCollect))
        trainAcc.append(np.mean(trainCollect))
        
        module_logger.info('Epoch: ', epoch)
        module_logger.info('Epoch cost average: ', epochCost[-1])
        module_logger.info('Epoch TRAIN accuracy: ', trainAcc[-1])
        print 'Epoch: ', epoch
        print 'Epoch cost average: ', epochCost[-1]
        print 'Epoch TRAIN accuracy: ', trainAcc[-1]

    return classifierTrain, classifierPredict


if __name__ == '__main__':
    host = 'poseidon-rabbit'
    exchange = 'topic-poseidon-internal'
    queue_name = 'NAME'
    #channel, connection = rabbit_init(host=host,
    #                                  exchange=exchange,
    #                                  queue_name=queue_name)
    print 'starting program'
    dataPath = 'testpcap.cap'
    train, predict = training(runname, rnnType, maxPackets, packetTimeSteps, packetReverse, padOldTimeSteps, wtstd, 
             lr, decay, clippings, dimIn, dim, numClasses, batch_size, epochs, 
             trainPercent, dataPath, loadPrepedData)
