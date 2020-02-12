#!/usr/bin/python3


import argparse
import csv
import io
import gzip
import ipaddress
import glob
import os
import subprocess
import sys
import netaddr


BCAST_EUI = netaddr.EUI('ff:ff:ff:ff:ff:ff', dialect=netaddr.mac_unix_expanded)



def get_pcap_mac_ips(pcap_dirs):
    pcaps = []
    for pcap_dir in pcap_dirs:
        if os.path.isdir(pcap_dir):
            pcaps.extend([
                pcap for pcap in glob.glob(os.path.join(pcap_dir, '**/*cap'), recursive=True)
                if os.path.isfile(pcap)])
    pcap_pairs = {}
    for pcap in pcaps:
        tshark_args = ['tshark', '-T', 'fields', '-r', pcap, '-s', '256']
        fields = ('eth.src', 'eth.dst', 'ipv6.src_host', 'ipv6.dst_host', 'ip.src', 'ip.dst')
        for field in fields:
            tshark_args.extend(['-e', field])
        try:
            tshark_proc = subprocess.Popen(tshark_args, stdout=subprocess.PIPE)
        except FileNotFoundError:
            sys.stderr.write('Please install tshark.\n')
            sys.exit(-1)
        pairs = set()
        for tshark_line in tshark_proc.stdout.readlines():
            tshark_line_list = tshark_line.decode('utf-8').rstrip('\n').split('\t')
            eth_src_str, eth_dst_str, ipv6_src, ipv6_dst, ipv4_src, ipv4_dst = tshark_line_list
            eth_src = netaddr.EUI(eth_src_str, dialect=netaddr.mac_unix_expanded)
            eth_dst = netaddr.EUI(eth_dst_str, dialect=netaddr.mac_unix_expanded)
            for src_ip_str in (ipv4_src, ipv6_src):
                try:
                    ip_src = ipaddress.ip_address(src_ip_str)
                except ValueError:
                    continue
                pairs.add((eth_src, ip_src))
            if eth_dst != BCAST_EUI:
                for dst_ip_str in (ipv4_dst, ipv6_dst):
                    try:
                        ip_dst = ipaddress.ip_address(dst_ip_str)
                    except ValueError:
                        continue
                    if ip_dst.is_multicast or ip_dst.is_unspecified:
                        continue
                    pairs.add((eth_dst, ip_dst))
        pcap_pairs[pcap] = pairs
    return pcap_pairs


def gen_manifest(pcap_pairs, csv_output):
    with gzip.open(csv_output, 'wb') as csv_out:
        writer = csv.DictWriter(io.TextIOWrapper(
            csv_out, newline='', write_through=True), fieldnames=('eth', 'ip', 'pcap'))
        writer.writeheader()
        for pcap, pairs in sorted(pcap_pairs.items()):
            for eth, ipa in pairs:
                writer.writerow({'eth': str(eth), 'ip': str(ipa), 'pcap': pcap})


def main():
    arg_parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description='Generate a compressed CSV of MAC/IP/file mappings from pcaps',
        usage="""

    Example:

        --pcapdirs=/some/dir,/some/other/dir --csv=/some/csvfile.csv.gz
""")
    arg_parser.add_argument(
        '-p', '--pcapdirs', help='list of pcap dirs')
    arg_parser.add_argument(
        '-c', '--csv', help='compressed csv file to write')
    try:
        args = arg_parser.parse_args(sys.argv[1:])
    except (KeyError, IndexError):
        arg_parser.print_usage()
        sys.exit(-1)

    if not (args.pcapdirs and args.csv):
        arg_parser.print_usage()
        sys.exit(-1)

    pcap_pairs = get_pcap_mac_ips(args.pcapdirs.split(','))
    gen_manifest(pcap_pairs, args.csv)


if __name__ == '__main__':
    main()
