import yaml

from poseidon.poseidonMonitor.NorthBoundControllerAbstraction.proxy.faucet import connection
from poseidon.baseClasses.Logger_Base import Logger


def represent_none(dumper, _):
    return dumper.represent_scalar('tag:yaml.org,2002:null', '')

class Rule_Ops():

    def __init__(self, deviceList):
        self.deviceList = deviceList

    def writeRules(self, config_file):
        self.logger.info('writeRules entered')
        #Write rule based on devices in list
        if not config_file:
            # default to FAUCET default
            config_file = '/etc/faucet/faucet.yaml'

        try:
            stream = open(config_file, 'r')
            obj_doc = yaml.safe_load(stream)
            stream.close()

            found = False
            for rules in obj_doc['acls']:
                # Temporary check if the single rule is already there
                if (rules == "Block"):
                    found = True
                    break

            # Decide block rule
            obj_doc['acls']['Block'] = \
                [{'rule': {'actions': {'allow': False}}}]

            stream = open(config_file, 'w')
            yaml.add_representer(type(None), represent_none)
            yaml.dump(obj_doc, stream, default_flow_style=False)

        except Exception as e:
            self.logger.error("failed to load config")
            self.logger.error(str(e))
            return False

        return True