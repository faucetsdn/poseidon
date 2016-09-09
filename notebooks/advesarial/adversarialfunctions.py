import random
from copy import copy


class Adversary(object):
    def __init__(self, hexSessionList):
        self.hexSessionList = hexSessionList


    def ipDirSwitcher(self):
        '''
        switches both ip and mac addresses
        input is a list of packets from ONE session
        '''
        
        ipdirsession = []   
        for p in self.hexSessionList:
            sourceMAC = p[:12]
            destMAC = p[12:24]
            sourceIP = p[52:60]
            destIP = p[60:68]

            ipdirsession.append(destMAC + sourceMAC + p[24:52] + destIP + sourceIP + p[68:])

        return ipdirsession


    def portDirSwitcher(self):
        '''
        input is a list of packets from ONE session
        '''
        
        portdirsession = []
        for p in self.hexSessionList:
            sport = p[68:72]
            dport = p[72:76]

            portdirsession.append(p[:68]+dport+sport+p[76:])

        return portdirsession


    #TODO: fix the mac switchout
    def dstIpSwapOut(self, dictOcoms, listOuniqIPs):
        #srcIpDict[srcip][dstip] = [[sport], [dport], [plen], [protocol]]
        
        swapSession = []
        sourceMAC = self.hexSessionList[0][:12]#[0] assumes first packet contains true initial direction
        destMAC = self.hexSessionList[0][12:24]
        srcip = self.hexSessionList[0][52:60] 
        dstip = self.hexSessionList[0][60:68]
        normDstIps = dictOcoms[srcip].keys()+[srcip] #get list of dstIPs that srcIP talks to
        abbynormIps = copy(listOuniqIPs)
        
        for normIp in normDstIps:
            abbynormIps.remove(normIp) #remove itself and know dstIPs from list of consideration.
        
        abbynormDestIp = random.sample(abbynormIps, 1)[0] #get random ip that srcip doesn't talk to

        for rawpacket in self.hexSessionList:
            packet = copy(rawpacket)
            
            if packet[60:68] == dstip:
                packet = packet[:60] + abbynormDestIp + packet[68:] #
            elif packet[60:68] == srcip:
                packet = packet[:52] + abbynormDestIp + packet[60:] #in case direction switches for packet in session
                
            swapSession.append(packet)

        return swapSession


    #TODO: should port/ip/mac address be ignored? yes
    def noisyPacketMaker(self, maxPackets, packetTimeSteps, percentNoisy = 0.2):
        noisySession = copy(self.hexSessionList)
        hexChars = 'abcdef1234567890'
        
        if len(noisySession) > maxPackets:
            sessionLen = maxPackets
        else:
            sessionLen = len(noisySession)
            
        packetForNoising = random.sample(xrange(sessionLen), 1)[0]
        noisyPacket = noisySession[packetForNoising]
        noisiness = int(len(xrange(24,52))*percentNoisy) #preserve mac, ip, and port by using only xrange(24,52)
        mutationIndex = random.sample(xrange(24,52), noisiness)
        
        for num in mutationIndex:
            randomReplacement = random.sample(hexChars, 1)[0]
            
            if num == 0:
                noisyPacket = randomReplacement + noisyPacket[1:]
            else:
                noisyPacket = noisyPacket[:num] + randomReplacement + noisyPacket[num+1:]
        
        return noisySession
