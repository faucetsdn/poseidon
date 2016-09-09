import Sessionizer
import sys
import logging
import json
import subprocess
import numpy as np

module_logger = logging.getLogger(__name__)

class HexSessionizer():
    def __init__(self, path):
        self.path = path
        self.hex_sessions = {}

    def read_pcap(self):  # pragma: no cover
        print 'starting reading pcap file'
        module_logger.debug('start reading pcap file {0}'.format(self.path))
        self.hex_sessions = {} 
        
        proc = subprocess.Popen('tcpdump -nn -tttt -xx -r '+self.path,
                                shell=True,
                                stdout=subprocess.PIPE)
        insert_num = 0  # keeps track of insertion order into dict
        for packet in Sessionizer.process_packet(proc.stdout):
            if not is_clean_packet(packet):
                continue
            if 'data' in packet:
                key = (packet['src_ip']+":"+packet['src_port'], packet['dest_ip']+":"+packet['dest_port'])
                rev_key = (key[1], key[0])
                if key in self.hex_sessions:
                    self.hex_sessions[key][0].append(packet['data'])
                elif rev_key in self.hex_sessions:
                    self.hex_sessions[rev_key][0].append(packet['data'])
                else:
                    self.hex_sessions[key] = ([packet['data']], insert_num)
                    insert_num += 1
        module_logger.debug('finished reading pcap file {0}'.format(self.path))
        print 'finished reading pcap file'
        return self.hex_sessions


    def internal_order_keys(self):
        return Sessionizer.order_keys(self.hex_sessions)


def removeBadSessionizer(hex_sessions, minPacketLen=80, saveFile=False, dataPath=None, fileName=None):
    for ses in hex_sessions.keys():
        paclens = []
        for pac in hex_sessions[ses][0]:
            paclens.append(len(pac))
        if np.min(paclens)<minPacketLen:
            del hex_sessions[ses]

    if saveFile:
        print 'pickling sessions'
        pickleFile(hex_sessions, filePath=dataPath, fileName=fileName)
        
    return hex_sessions

    
def order_keys(hex_sessions):
    """
    Returns list of the hex sessions in (rough) time order.
    """
    orderedKeys = []

    for key in sorted(hex_sessions.keys(), key=lambda key: hex_sessions[key][1]):
        orderedKeys.append(key)

    return orderedKeys


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