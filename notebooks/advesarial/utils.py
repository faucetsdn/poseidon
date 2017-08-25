import cPickle


# load and save files and models
def pickleFile(
        thing2save,
        file2save2=None,
        filePath='/work/notebooks/drawModels/',
        fileName='myModels'):

    if file2save2 is None:
        f = file(filePath + fileName + '.pickle', 'wb')
    else:
        f = file(filePath + file2save2, 'wb')

    cPickle.dump(thing2save, f, protocol=cPickle.HIGHEST_PROTOCOL)

    f.close()


def loadFile(filePath):
    file2open = file(filePath, 'rb')
    loadedFile = cPickle.load(file2open)
    file2open.close()

    return loadedFile


def hexTokenizer():
    hexstring = '0, 1,  2,  3,  4,  5,  6,  7,  8,  9,  A,  B,  C,  D,  E,  F,  10, 11, 12, 13, 14, 15, 16, 17, 18, 19\
    ,   1A, 1B, 1C, 1D, 1E, 1F, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 2A, 2B, 2C, 2D, 2E, 2F, 30, 31, 32, 33, 34, 35\
    ,   36, 37, 38, 39, 3A, 3B, 3C, 3D, 3E, 3F, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 4A, 4B, 4C, 4D, 4E, 4F, 50, 51\
    ,   52, 53, 54, 55, 56, 57, 58, 59, 5A, 5B, 5C, 5D, 5E, 5F, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 6A, 6B, 6C, 6D\
    ,   6E, 6F, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 7A, 7B, 7C, 7D, 7E, 7F, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89\
    ,   8A, 8B, 8C, 8D, 8E, 8F, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 9A, 9B, 9C, 9D, 9E, 9F, A0, A1, A2, A3, A4, A5\
    ,   A6, A7, A8, A9, AA, AB, AC, AD, AE, AF, B0, B1, B2, B3, B4, B5, B6, B7, B8, B9, BA, BB, BC, BD, BE, BF, C0, C1\
    ,   C2, C3, C4, C5, C6, C7, C8, C9, CA, CB, CC, CD, CE, CF, D0, D1, D2, D3, D4, D5, D6, D7, D8, D9, DA, DB, DC, DD\
    ,   DE, DF, E0, E1, E2, E3, E4, E5, E6, E7, E8, E9, EA, EB, EC, ED, EE, EF, F0, F1, F2, F3, F4, F5, F6, F7, F8, F9\
    ,   FA, FB, FC, FD, FE, FF'.replace('\t', '')

    hexList = [x.strip() for x in hexstring.lower().split(',')]
    hexList.append('<EOP>')  # End Of Packet token
    # EOS token??????
    hexDict = {}

    for key, val in enumerate(hexList):
        if len(val) == 1:
            val = '0' + val
        hexDict[val] = key  # dictionary: k=hex, v=int

    return hexDict


def srcIpDict(hexSessionDict):
    '''
    input: dictionary of key = sessions, value = list of HEX HEADERS of packets in session
    output: dictionary of key = source IP, value/subkey = dictionary of destination IPs,
                                           subvalue = [[sport], [dport], [plen], [protocol]]

    '''

    srcIpDict = {}
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


def dictUniquerizer(dictOdictsOlistOlists):
    '''
    input is the output of srcIpDict
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
