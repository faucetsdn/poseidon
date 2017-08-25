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
import sessionizer
import learningfunctions
import adversarialfunctions
import time
import os
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
from blocks.bricks import Softmax, NDimensionalSoftmax, BatchNormalizedMLP, Tanh, MLP
from blocks.bricks.recurrent import GatedRecurrent, Fork, LSTM
from blocks.initialization import Constant, IsotropicGaussian, Identity, Uniform
from blocks.bricks.cost import BinaryCrossEntropy, CategoricalCrossEntropy
from blocks.filter import VariableFilter
from blocks.roles import PARAMETER
from blocks.graph import ComputationGraph

import theano
from theano import tensor as T


module_logger = logging.getLogger(__name__)

fd = None
STORAGE_PORT = '28000'
DATABASE = 'poseidon_records'
COLLECTION = 'models'


def get_path():
    try:
        path_name = sys.argv[1]
    except BaseException:
        module_logger.debug('no argv[1] for pathname')
        path_name = None
    return path_name


def get_host():
    """
    Checks for poseidon host env
    variable and returns it if found,
    otherwise logs error.
    """
    if 'POSEIDON_HOST' in os.environ:
        return os.environ['POSEIDON_HOST']
    else:
        module_logger.debug('POSEIDON_HOST environment variable not found')
        return None


def rabbit_init(host, exchange, queue_name, rabbit_rec):  # pragma: no cover
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
        except Exception as e:
            print 'waiting for connection to rabbitmq...'
            print str(e)
            module_logger.info(str(e))
            module_logger.info('waiting for connection to rabbitmq...')
            time.sleep(2)
            wait = True

    if rabbit_rec:
        binding_keys = sys.argv[1:]
        if not binding_keys:
            ostr = 'Usage: {0} [binding_key]...'.format(sys.argv[0])
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

maxPackets = 4
loadPrepedData = True  # load preprocessed data
# dataPath = '/data/fs4/datasets/pcaps/smallFlows.pcap'  # path to data
dataPath = '/data/fs4/home/bradh/bigFlows.pickle'  # path to data
savePath = '/data/fs4/home/bradh/outputs/'  # where to save outputs

packetTimeSteps = 40  # number of hex pairs (header chars / 2)
packetReverse = False  # reverse the order of packets ala seq2seq
# pad short sessions/packets at beginning(True) or end (False)
padOldTimeSteps = True
# extracts only length,protocol,frag,srcIP,dstIP,srcport,dstport from header
onlyEssentials = True
if onlyEssentials:
    packetTimeSteps = 16

runname = 'TEST4smallattn0'  # 'attn8full4class'
rnnType = 'gru'  # gru or lstm
attentionEnc = False
attentionContext = False

wtstd = 0.2  # standard dev for Isotropic weight initialization
dimIn = 257  # hex has 256 characters + the <EOP> character
dim = 100  # dimension reduction size
clippings = 1  # for gradient clipping
batch_size = 20
binaryTarget = False

if binaryTarget:
    numClasses = 2
else:
    numClasses = 4

epochs = 50
lr = 0.0001
decay = 0.9
trainPercent = 0.9  # training testing split

module_logger = logging.getLogger(__name__)


def pickleFile(thing2save, file2save2=None, filePath='/work/notebooks/drawModels/', fileName='myModels'):  # pragma: no cover

    if file2save2 is None:
        f = file(filePath + fileName + '.pickle', 'wb')
    else:
        f = file(filePath + file2save2, 'wb')

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
        if np.min(paclens) < 80:
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
            val = '0' + val
        hexDict[val] = key  # dictionary k=hex, v=int

    return hexDict


def srcIpDict(hexSessionDict):  # pragma: no cover
    '''
    input: dictionary of key = sessions, value = list of HEX HEADERS of packets in session
    output: dictionary of key = source IP, value/subkey = dictionary of destination IPs,
                                           subvalue = [[sport], [dport], [plen], [protocol]]

    '''
    srcIpDict = OrderedDict()
    uniqIPs = []  # some ips are dest only. this will collect all ips, not just srcIpDict.keys()

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
                dstIpSubDict[dstip] = [
                    [sport],
                    [dport],
                    [plen],
                    [protocol],
                    [sourceMAC],
                    [destMAC]]
                srcIpDict[srcip] = dstIpSubDict

            if dstip not in srcIpDict[srcip]:
                srcIpDict[srcip][dstip] = [[sport], [dport], [
                    plen], [protocol], [sourceMAC], [destMAC]]
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
    # dictCopy
    for key in dictOdictsOlistOlists.keys():
        for subkey in dictOdictsOlistOlists[key].keys():
            for sublist in xrange(len(dictOdictsOlistOlists[key][subkey])):
                dictOdictsOlistOlists[key][subkey][sublist] = list(
                    set(dictOdictsOlistOlists[key][subkey][sublist]))

    return dictOdictsOlistOlists


def oneHot(index, granular='hex'):  # pragma: no cover
    if granular == 'hex':
        vecLen = 257
    else:
        vecLen = 17

    zeroVec = np.zeros(vecLen)
    zeroVec[index] = 1.0

    return zeroVec


# TODO: add character level encoding
def oneSessionEncoder(
        sessionPackets,
        hexDict,
        maxPackets,
        packetTimeSteps,
        packetReverse=False,
        charLevel=False,
        padOldTimeSteps=True,
        onlyEssentials=False):

    sessionCollect = []
    packetCollect = []

    # TODO: add character-level encoding
    if charLevel:
        vecLen = 17
    else:
        vecLen = 257

    if len(sessionPackets) > maxPackets:  # crop the number of sessions to maxPackets
        sessionList = copy(sessionPackets[:maxPackets])
    else:
        sessionList = copy(sessionPackets)

    for rawpacket in sessionList:
        packet = copy(rawpacket)

        if onlyEssentials:  # cat of length,protocol,frag,srcIP,dstIP,srcport,dstport
            packet = packet[32:36] + packet[44:46] + packet[46:48] + \
                packet[52:60] + packet[60:68] + packet[68:72] + packet[72:76]

        packet = [hexDict[packet[i:i + 2]]
                  for i in xrange(0, len(packet) - 2 + 1, 2)]  # get hex pairs

        if len(
                packet) >= packetTimeSteps:  # crop packet to length packetTimeSteps rel to hex pairs
            packet = packet[:packetTimeSteps]

        packet = packet + [256]  # add <EOP> end of packet token

        packetCollect.append(packet)

        # one hot encoding of packet into a matrix
        pacMat = np.array([oneHot(x) for x in packet])
        pacMatLen = len(pacMat)

        # padding packet
        if packetReverse:
            pacMat = pacMat[::-1]

        if pacMatLen < packetTimeSteps:
            # pad by stacking zeros on top of data so that earlier timesteps do not have information
            # padding the packet such that zeros are after the actual info for
            # better translation
            if padOldTimeSteps:
                pacMat = np.vstack(
                    (np.zeros((packetTimeSteps - pacMatLen, vecLen)), pacMat))
            else:
                pacMat = np.vstack(
                    (pacMat, np.zeros(
                        (packetTimeSteps - pacMatLen, vecLen))))

        if pacMatLen > packetTimeSteps:
            pacMat = pacMat[:packetTimeSteps, :]

        sessionCollect.append(pacMat)

    # padding session
    sessionCollect = np.asarray(sessionCollect, dtype=theano.config.floatX)
    numPacketsInSession = sessionCollect.shape[0]
    if numPacketsInSession < maxPackets:
        # pad sessions to fit the
        sessionCollect = np.vstack((sessionCollect, np.zeros(
            (maxPackets - numPacketsInSession, packetTimeSteps, vecLen))))

    return sessionCollect, packetCollect


def predictClass(
        predictFun,
        hexSessionsDict,
        comsDict,
        uniqIPs,
        hexDict,
        hexSessionsKeys,
        binaryTarget,
        numClasses,
        onlyEssentials,
        trainPercent=0.9,
        dimIn=257,
        maxPackets=2,
        packetTimeSteps=16,
        padOldTimeSteps=True):

    testCollect = []
    predtargets = []
    actualtargets = []
    trainPercent = 0.9
    trainIndex = int(len(hexSessionsKeys) * trainPercent)

    start = trainIndex
    end = len(hexSessionsKeys)

    trainingSessions = []
    trainingTargets = []

    for trainKey in range(start, end):
        sessionForEncoding = list(
            hexSessionsDict[hexSessionsKeys[trainKey]][0])

        adfun = adversarialfunctions.Adversary(sessionForEncoding)
        adversaryList = [
            sessionForEncoding,
            adfun.dstIpSwapOut(
                comsDict,
                uniqIPs),
            adfun.portDirSwitcher(),
            adfun.ipDirSwitcher(),
            adfun.noisyPacketMaker(
                maxPackets,
                packetTimeSteps,
                percentNoisy=0.2)]
        if binaryTarget:
            # choose normal and one of the abnormal types
            abbyIndex = random.sample(
                [0, random.sample(xrange(1, len(adversaryList)), 1)[0]], 1)[0]
            if abbyIndex == 0:
                targetClasses = [1, 0]
            else:
                targetClasses = [0, 1]
        else:
            assert len(adversaryList) == numClasses
            abbyIndex = random.sample(range(len(adversaryList)), 1)[0]
            targetClasses = [0] * numClasses
            targetClasses[abbyIndex] = 1

        abbyIndex = random.sample(range(len(adversaryList)), 1)[0]
        abbyOneHotSes = oneSessionEncoder(adversaryList[abbyIndex],
                                          hexDict=hexDict,
                                          packetReverse=packetReverse,
                                          padOldTimeSteps=padOldTimeSteps,
                                          maxPackets=maxPackets,
                                          packetTimeSteps=packetTimeSteps)

        trainingSessions.append(abbyOneHotSes[0])
        trainingTargets.append(
            np.array(
                targetClasses,
                dtype=theano.config.floatX))

    sessionsMinibatch = np.asarray(
        trainingSessions, dtype=theano.config.floatX) .reshape(
        (-1, packetTimeSteps, 1, dimIn))
    targetsMinibatch = np.asarray(trainingTargets, dtype=theano.config.floatX)

    predcostfun = predictFun(sessionsMinibatch)
    testCollect.append(
        np.mean(
            np.argmax(
                predcostfun,
                axis=1) == np.argmax(
                targetsMinibatch,
                axis=1)))

    predtargets = np.argmax(predcostfun, axis=1)
    actualtargets = np.argmax(targetsMinibatch, axis=1)

    print "TEST accuracy:         ", np.mean(testCollect)
    print

    return predtargets, actualtargets, np.mean(testCollect)


def binaryPrecisionRecall(predictions, targets, numClasses=4):  # pragma: no cover
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

        # 1 - (how much junk did we give user)
        precision = float(truePos) / (truePos + falsePos + 0.00001)
        # 1 - (how much good stuff did we miss)
        recall = float(truePos) / (truePos + falseNeg + 0.00001)
        f1 = 2 * ((precision * recall) / (precision + recall + 0.00001))

        module_logger.info('class ' + str(cla) + ' precision: ', precision)
        module_logger.info('class ' + str(cla) + ' recall:    ', recall)
        module_logger.info('class ' + str(cla) + ' f1:        ', f1)


def save_model(model):
    """
    Takes a model class to be saved and
    serializes it, saves to a file, and
    then adds to db.
    """
    cPickle.dump(model,
                 open('deep_predict.pickle', 'wb'),
                 cPickle.HIGHEST_PROTOCOL)

    try:
        # uses lowest protocol for utf8 compliance when request is serialized
        model_str = cPickle.dumps(model, 0)
        uri = 'http://' + os.environ['POSEIDON_HOST'] + ':' + STORAGE_PORT + \
            '/v1/storage/add_one_doc/{database}/{collection}'.format(database=DATABASE,
                                                                     collection=COLLECTION)
        payload = {'model': model_str}
        resp = requests.post(uri, data=json.dumps(payload))
        if resp.status_code != 200:
            module_logger.debug(str(resp.status_code))
    except BaseException:
        module_logger.debug('connection to storage-interface failed')


def training(runname, rnnType, maxPackets, packetTimeSteps, packetReverse, padOldTimeSteps, wtstd,
             lr, decay, clippings, dimIn, dim, attentionEnc, attentionContext, numClasses, batch_size, epochs,
             trainPercent, dataPath, loadPrepedData, channel):  # pragma: no cover
    print locals()
    print

    X = T.tensor4('inputs')
    Y = T.matrix('targets')
    linewt_init = IsotropicGaussian(wtstd)
    line_bias = Constant(1.0)
    rnnwt_init = IsotropicGaussian(wtstd)
    rnnbias_init = Constant(0.0)
    classifierWts = IsotropicGaussian(wtstd)

    learning_rateClass = theano.shared(
        np.array(lr, dtype=theano.config.floatX))
    learning_decay = np.array(decay, dtype=theano.config.floatX)

    # DATA PREP
    print 'loading data'
    if loadPrepedData:
        hexSessions = loadFile(dataPath)

    else:
        sessioner = sessionizer.HexSessionizer(dataPath)
        hexSessions = sessioner.read_pcap()
        hexSessions = removeBadSessionizer(hexSessions)

    numSessions = len(hexSessions)
    print str(numSessions) + ' sessions found'
    hexSessionsKeys = order_keys(hexSessions)
    hexDict = hexTokenizer()

    print 'creating dictionary of ip communications'
    comsDict, uniqIPs = srcIpDict(hexSessions)
    comsDict = dictUniquerizer(comsDict)

    print 'initializing network graph'
    # ENCODER
    if rnnType == 'gru':
        rnn = GatedRecurrent(
            dim=dim,
            weights_init=rnnwt_init,
            biases_init=rnnbias_init,
            name='gru')
        dimMultiplier = 2
    else:
        rnn = LSTM(
            dim=dim,
            weights_init=rnnwt_init,
            biases_init=rnnbias_init,
            name='lstm')
        dimMultiplier = 4

    fork = Fork(
        output_names=[
            'linear',
            'gates'],
        name='fork',
        input_dim=dimIn,
        output_dims=[
            dim,
            dim *
            dimMultiplier],
        weights_init=linewt_init,
        biases_init=line_bias)

    # CONTEXT
    if rnnType == 'gru':
        rnnContext = GatedRecurrent(
            dim=dim,
            weights_init=rnnwt_init,
            biases_init=rnnbias_init,
            name='gruContext')
    else:
        rnnContext = LSTM(
            dim=dim,
            weights_init=rnnwt_init,
            biases_init=rnnbias_init,
            name='lstmContext')

    forkContext = Fork(
        output_names=[
            'linearContext',
            'gatesContext'],
        name='forkContext',
        input_dim=dim,
        output_dims=[
            dim,
            dim * dimMultiplier],
        weights_init=linewt_init,
        biases_init=line_bias)

    forkDec = Fork(
        output_names=[
            'linear',
            'gates'],
        name='forkDec',
        input_dim=dim,
        output_dims=[
            dim,
            dim *
            dimMultiplier],
        weights_init=linewt_init,
        biases_init=line_bias)

    # CLASSIFIER
    bmlp = BatchNormalizedMLP(activations=[Tanh(), Tanh()],
                              dims=[dim, dim, numClasses],
                              weights_init=classifierWts,
                              biases_init=Constant(0.0001))

    # initialize the weights in all the functions
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

    # (mini*numPackets, packetLen, 1, hexdictLen)
    hEnc, _ = theano.scan(onestepEnc, X)
    if attentionEnc:

        attentionmlpEnc = MLP(
            activations=[
                Tanh()], dims=[
                dim, 1], weights_init=attnWts, biases_init=Constant(1.0))
        attentionmlpEnc.initialize()

        hEncAttn = T.reshape(hEnc, (-1, packetTimeSteps, dim))

        def onestepEncAttn(hEncAttn):

            preEncattn = attentionmlpEnc.apply(hEncAttn)
            attEncsoft = Softmax()
            attEncpyx = attEncsoft.apply(preEncattn.flatten())
            attEncpred = attEncpyx.flatten()
            attenc = T.mul(
                hEncAttn.dimshuffle(
                    1, 0), attEncpred).dimshuffle(
                1, 0)

            return attenc

        attenc, _ = theano.scan(onestepEncAttn, hEncAttn)

        hEncReshape = T.reshape(T.sum(attenc, axis=1),
                                (-1, maxPackets, 1, dim))

    else:
        # [:,-1] takes the last rep for each packet
        hEncReshape = T.reshape(hEnc[:, -1], (-1, maxPackets, 1, dim))
        #(mini, numPackets, 1, dimReduced)  #[:,-1] takes the last rep for each packet
        #(mini, numPackets, 1, dimReduced)

    def onestepContext(hEncReshape):

        data3, data4 = forkContext.apply(hEncReshape)

        if rnnType == 'gru':
            hContext = rnnContext.apply(data3, data4)
        else:
            hContext, _ = rnnContext.apply(data4)

        return hContext

    hContext, _ = theano.scan(onestepContext, hEncReshape)

    if attentionContext:
        attentionmlpContext = MLP(
            activations=[
                Tanh()], dims=[
                dim, 1], weights_init=attnWts, biases_init=Constant(1.0))
        attentionmlpContext.initialize()

        hContextAttn = T.reshape(hContext, (-1, maxPackets, dim))

        def onestepContextAttn(hContextAttn):

            preContextatt = attentionmlpContext.apply(hContextAttn)
            attContextsoft = Softmax()
            attContextpyx = attContextsoft.apply(preContextatt.flatten())
            attContextpred = attContextpyx.flatten()
            attcontext = T.mul(
                hContextAttn.dimshuffle(
                    1, 0), attContextpred).dimshuffle(
                1, 0)

            return attcontext

        attcontext, _ = theano.scan(onestepContextAttn, hContextAttn)
        hContextReshape = T.sum(attcontext, axis=1)

    else:
        hContextReshape = T.reshape(hContext[:, -1], (-1, dim))

    data5, _ = forkDec.apply(hContextReshape)
    pyx = bmlp.apply(data5)
    softmax = Softmax()
    softoutClass = softmax.apply(pyx)
    costClass = T.mean(CategoricalCrossEntropy().apply(Y, softoutClass))

    # CREATE GRAPH
    cgClass = ComputationGraph([costClass])
    paramsClass = VariableFilter(roles=[PARAMETER])(cgClass.variables)
    learning = learningfunctions.Learning(
        costClass,
        paramsClass,
        learning_rateClass,
        l1=0.,
        l2=0.,
        maxnorm=0.,
        c=clippings)
    updatesClass = learning.Adam()

    module_logger.info('starting graph compilation')
    classifierTrain = theano.function([X,
                                       Y],
                                      [costClass,
                                       hEnc,
                                       hContext,
                                       pyx,
                                       softoutClass],
                                      updates=updatesClass,
                                      allow_input_downcast=True)
    classifierPredict = theano.function(
        [X], softoutClass, allow_input_downcast=True)
    module_logger.info('graph compilation finished')
    print 'finished graph compilation'

    trainIndex = int(len(hexSessionsKeys) * trainPercent)

    epochCost = []
    gradNorms = []
    trainAcc = []
    testAcc = []

    costCollect = []
    trainCollect = []

    module_logger.info('beginning training')
    iteration = 0
    # epoch
    for epoch in xrange(epochs):

        # iteration/minibatch
        for start, end in zip(range(0, trainIndex, batch_size),
                              range(batch_size, trainIndex, batch_size)):

            trainingTargets = []
            trainingSessions = []

            # create one minibatch with 0.5 normal and 0.5 abby normal traffic
            for trainKey in range(start, end):
                sessionForEncoding = list(
                    hexSessions[hexSessions.keys()[trainKey]][0])

                adfun = adversarialfunctions.Adversary(sessionForEncoding)
                adversaryList = [sessionForEncoding,
                                 adfun.dstIpSwapOut(comsDict, uniqIPs),
                                 adfun.portDirSwitcher(),
                                 adfun.ipDirSwitcher()]
                abbyIndex = random.sample(range(len(adversaryList)), 1)[0]

                targetClasses = [0] * numClasses
                targetClasses[abbyIndex] = 1
                abbyTarget = np.array(
                    targetClasses, dtype=theano.config.floatX)
                trainingSessions.append(abbyOneHotSes[0])
                trainingTargets.append(abbyTarget)

            sessionsMinibatch = np.asarray(trainingSessions).reshape(
                (-1, packetTimeSteps, 1, dimIn))
            targetsMinibatch = np.asarray(trainingTargets)

            costfun = classifierTrain(sessionsMinibatch, targetsMinibatch)

            if iteration % (numSessions / (10 * batch_size)) == 0:
                costCollect.append(costfun[0])
                trainCollect.append(
                    np.mean(np.argmax(costfun[-1], axis=1) == np.argmax(targetsMinibatch, axis=1)))
                module_logger.info('   Iteration: ', iteration)
                module_logger.info('   Cost: ', np.mean(costCollect))
                module_logger.info(
                    '   TRAIN accuracy: ',
                    np.mean(trainCollect))
                print '   Iteration: ', iteration
                print '   Cost: ', np.mean(costCollect)
                print '   TRAIN accuracy: ', np.mean(trainCollect)

            iteration += 1

            # testing accuracy
            if iteration % (numSessions / (2 * batch_size)) == 0:
                predtar, acttar, testCollect = predictClass(classifierPredict, hexSessions, comsDict, uniqIPs, hexDict,
                                                            hexSessionsKeys,
                                                            numClasses, trainPercent, dimIn, maxPackets, packetTimeSteps,
                                                            padOldTimeSteps)
                binaryPrecisionRecall(predtar, acttar, numClasses)
                module_logger.info(str(testCollect))

            # save the models
            if iteration % (numSessions / (5 * batch_size)) == 0:
                save_model(classifierPredict)

        epochCost.append(np.mean(costCollect))
        trainAcc.append(np.mean(trainCollect))

        module_logger.info('Epoch: ', epoch)
        module_logger.info('Epoch cost average: ', epochCost[-1])
        module_logger.info('Epoch TRAIN accuracy: ', trainAcc[-1])
        print 'Epoch: ', epoch
        print 'Epoch cost average: ', epochCost[-1]
        print 'Epoch TRAIN accuracy: ', trainAcc[-1]

    return classifierTrain, classifierPredict


def run_plugin(path, host):  # pragma: no cover
    exchange = 'topic-poseidon-internal'
    queue_name = 'dl_algos_deep_classifier'
    binding_key = 'poseidon.deep_classifier'
    fd = open('temp_file', 'w+')
    channel, connection = rabbit_init(host=host,
                                      exchange=exchange,
                                      queue_name=queue_name,
                                      rabbit_rec=False)
    train, predict = training(runname, rnnType, maxPackets, packetTimeSteps, packetReverse, padOldTimeSteps, wtstd,
                              lr, decay, clippings, dimIn, dim, attentionEnc, attentionContext, numClasses, batch_size, epochs,
                              trainPercent, path, loadPrepedData, channel)


if __name__ == '__main__':
    path_name = get_path()
    host = get_host()
    if path_name and host:
        run_plugin(path_name, host)

    print 'program completed'
