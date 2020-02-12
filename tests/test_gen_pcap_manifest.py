#!/usr/bin/env python3
import gzip
import os
import tempfile


def test_gen_pcap_manifest():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    gen_pcap_manifest = os.path.sep.join(
        (test_dir, '..', 'bin', 'gen_pcap_manifest'))
    pcap_file = os.path.join(test_dir, 'test-ipv4.pcap')
    with tempfile.TemporaryDirectory() as tempdir:
        csv_file = os.path.join(tempdir, 'out.csv.gz')
        os.system(' '.join((gen_pcap_manifest, '-p', test_dir, '-c', csv_file)))
        with gzip.open(csv_file, 'r') as csv_out:
            all_csv_out = [line.decode('utf-8')
                           for line in csv_out.readlines()]
            assert all_csv_out == [
                'eth,ip,pcap\r\n', '00:00:00:00:00:00,127.0.0.1,%s\r\n' % pcap_file]
