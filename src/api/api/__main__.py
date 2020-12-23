def main():
    import argparse
    import os
    import subprocess

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--port', '-p', help='Port to run the API webserver on', type=int, default=8000)
    parser.add_argument(
        '--prom_addr', '-a', help='Prometheus address connected to Poseidon, i.e. "prometheus:9090"', default='prometheus:9090')
    args = parser.parse_args()

    os.environ['PROM_ADDR'] = args.prom_addr
    process = subprocess.Popen(['gunicorn', '-b :'+str(args.port), '-k eventlet', '-w 4', '--reload', 'poseidon_api.api'],
                               stdout=subprocess.PIPE,
                               universal_newlines=True)

    while True:
        output = process.stdout.readline()
        print(output.strip())
        return_code = process.poll()
        if return_code is not None:
            for output in process.stdout.readlines():
                print(output.strip())
            break
