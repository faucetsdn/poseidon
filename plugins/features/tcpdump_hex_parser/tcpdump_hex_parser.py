import pika
import subprocess
import sys

def get_path():
    try:
        path = sys.argv[1]
    except:
        print "no path provided, quitting."
        sys.exit()
    return path

def connections():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='rabbitmq'))
        channel = connection.channel()

        channel.exchange_declare(exchange='topic_recs',
                                 type='topic')
    except:
        print "unable to connect to rabbitmq, quitting."
        sys.exit()
    return channel, connection



def parse_header(line):
    ret_dict = {}
    h = line.split()
    date = h[0]
    time = h[1]
    if h[2] == 'IP':
        ret_dict['date'] = h[0]
        ret_dict['time'] = h[1]
        return ret_dict
    return ''

def parse_data(line):
    ret_str = ''
    h,d = line.split(':', 1)
    ret_str = d.strip().replace(' ','')
    return ret_str

def return_packet(line_source):
    ret_data = ''
    ret_header = {}
    ret_dict = {}
    for line in line_source:
        line_strip = line.strip()
        is_data = line_strip.startswith('0x')
        if is_data:
            data = parse_data(line_strip)
            ret_data += data
        else:
            if not ret_data:
                ret_dict.update(ret_header)
                ret_dict['data'] = ret_data
                yield ret_dict
            header = parse_header(line_strip)
            ret_data = ''

def run_tool(path):
    routing_key = "tcpdump_hex_parser"+path.replace("/", ".")
    print "processing pcap results..."
    channel, connection = connections()
    proc = subprocess.Popen('tcpdump -nn -tttt -xx -r '+path, shell=True, stdout=subprocess.PIPE)
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        else:
            if not line.strip().startswith("0x"):
                data = {}
                data['readable'] = line
                message = str(data)
                channel.basic_publish(exchange='topic_recs',
                                      routing_key=routing_key,
                                      body=message)
                print " [x] Sent %r:%r" % (routing_key, message)

       #packet_dict = return_packet(proc.stdout)
       #if not packet_dict:
       #    break;
       #else:
       #    for x in  packet_dict:
       #        print x

    try:
        connection.close()
    except:
        pass

if __name__ == '__main__':
    path = get_path()
    run_tool(path)
