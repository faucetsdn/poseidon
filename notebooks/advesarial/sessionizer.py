import subprocess
import numpy as np

#module_logger = logging.getLogger(_name_)


class Sessionizer():
    def __init__(self, path):
        self.path = path
        self.hex_packets = {}
        self.orderedKeys = []
        #self.hex_sessions = {}

    def packetizer(self, qacheck=False):
        '''
        returns a dictionary of hex headers for individual packets

        path = string path to pcap file
        qacheck = dictionary of packets that cannot be processed
        '''
        proc = subprocess.Popen(
            'tcpdump -nn -tttt -xx -r ' +
            self.path,
            shell=True,
            stdout=subprocess.PIPE)
        insert_num = 0
        badPackets = {}
        for packet in process_packet(proc.stdout):
            if not is_clean_packet(packet):
                if qacheck:
                    badPackets[(packet['src_ip'] +
                                ":" +
                                packet['src_port'], packet['dest_ip'] +
                                ":" +
                                packet['dest_port'], insert_num)] = packet['data']
                continue

            if 'data' in packet:
                key = (
                    packet['src_ip'] +
                    ":" +
                    packet['src_port'],
                    packet['dest_ip'] +
                    ":" +
                    packet['dest_port'],
                    insert_num)
                self.hex_packets[key] = packet['data']
            insert_num += 1
        #module_logger.debug('finished reading pcap file {0}'.format(self.path))
        print('finished reading pcap file')
        if qacheck:
            return self.hex_packets, badPackets
        else:
            return self.hex_packets

    def order_keys(self):
        """
        Returns list of the hex sessions in (rough) time order.
        """
        def getitem(item):
            return item[-1]
        for key in sorted(self.hex_packets.keys(), key=getitem):
            self.orderedKeys.append(key)
        return self.orderedKeys

    def hexSessionizer(self):
        '''
        collects packets into sessions
        dictOpackets = dictionary of packets, k=(srcip:srcport, dstip:dstport)
        orderedKeys = list of time ordered keys for dictOpackets
        '''
        hex_sessions = {}
        for pair in self.orderedKeys:
            if pair[:2] not in hex_sessions or pair[:2][::-
                                                        1] not in hex_sessions:
                hex_sessions[pair[:2]] = [self.hex_packets[pair]]
            else:
                hex_sessions[pair[:2]].append(self.hex_packets[pair])
        return hex_sessions


def removeBadSessionizer(
        hex_sessions,
        minPacketLen=80,
        saveFile=False,
        dataPath=None,
        fileName=None):
    for ses in hex_sessions.keys():
        paclens = []
        for pac in hex_sessions[ses][0]:
            paclens.append(len(pac))
        if np.min(paclens) < minPacketLen:
            del hex_sessions[ses]

    if saveFile:
        print('pickling sessions')
        pickleFile(hex_sessions, filePath=dataPath, fileName=fileName)

    return hex_sessions


def parse_header(line):  # pragma: no cover
    ret_dict = {}
    h = line.split()
    if h[2] == 'IP6':

        #Conditional formatting based on ethernet type.
        #IPv4 format: 0.0.0.0.port
        #IPv6 format (one of many): 0:0:0:0:0:0.port

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
                except BaseException:
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
    if not packet['src_port'].isdigit():
        return False
    if not packet['dest_port'].isdigit():
        return False

    if packet['src_ip'].isalpha():
        return False
    if packet['dest_ip'].isalpha():
        return False

    return True
