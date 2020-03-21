import etw
import etw.evntrace
import json
import threading
import sys


class RpcServersConfig(object):
    def __init__(self, rpc_servers_map):
        self.rpc_servers_map = rpc_servers_map

    def get_rpc_info(self, interface_uuid, func_opnum):
        interface_uuid = interface_uuid.lower()

        if interface_uuid not in self.rpc_servers_map:
            return {}

        rpc_server = self.rpc_servers_map[interface_uuid]

        rpc_info = {
            'FileName': rpc_server['FileName']
        }

        if rpc_server['ServiceDisplayName']:
            rpc_info['ServiceDisplayName'] = rpc_server['ServiceDisplayName']

        if rpc_server['ServiceName']:
            rpc_info['ServiceName'] = rpc_server['ServiceName']

        if func_opnum >= len(rpc_server['Procedures']):
            return rpc_info

        rpc_info['ProcedureName'] = rpc_server['Procedures'][func_opnum]['Name']

        return rpc_info

    @staticmethod
    def load(file_path):
        with open(file_path, 'r') as rpc_servers_file:
            rpc_servers_json = json.load(rpc_servers_file)

        rpc_servers_map = {}

        for rpc_server in rpc_servers_json:
            uuid_key = '{' + rpc_server['InterfaceUuid'].lower() + '}'

            if uuid_key in rpc_servers_map:
                # Ignore duplicate RPC servers
                continue

            rpc_servers_map[uuid_key] = rpc_server

        return RpcServersConfig(rpc_servers_map)


class RpcMonitor(object):
    def __init__(self):
        self.config = RpcServersConfig.load('rpc_servers.json')
        self.events = []
        self.lock = threading.Lock()
        self.session = etw.ETW(
            providers=[
                etw.ProviderInfo(
                    name='Microsoft-Windows-RPC',
                    guid=etw.GUID("{6ad52b32-d609-4be9-ae07-ce8dae937e39}"),
                    level=etw.evntrace.TRACE_LEVEL_VERBOSE,
                    any_keywords=0xffffffffffffffff
                )
            ],
            event_callback=self.etw_callback
        )

    def etw_callback(self, event):
        if not self.is_rpc_client_call(event):
            return

        event = self.parse_rpc_event(event)

        with self.lock:
            self.events.append(event)

    def start(self):
        self.session.start()

    def stop(self):
        self.session.stop()

    def is_rpc_client_call(self, e):
        return e[0] == 5

    def parse_rpc_event(self, e):
        e = e[1]
        event = {
                'ProcessId': e['EventHeader']['ProcessId'],
                'ThreadId': e['EventHeader']['ThreadId'],
                'Timestamp': e['EventHeader']['TimeStamp'],
                'InterfaceUuid': e['InterfaceUuid'],
                'ProcedureNum': int(e['ProcNum'][2:], 16),
                'Endpoint': e['Endpoint'],
                'Protocol': e['Protocol']
            }

        rpc_info = self.config.get_rpc_info(event['InterfaceUuid'], event['ProcedureNum'])
        event.update(rpc_info)
        return event


def main():
    output_filename = sys.argv[1]
    monitor = RpcMonitor()
    print('Starting RPC session..')
    monitor.start()

    try:
        print("Press enter to close session..")
        input()
    except KeyboardInterrupt:
        pass

    print('Stopping monitor...')
    monitor.stop()

    print('Writing output...')
    with open(output_filename, 'w') as output_file:
        json.dump(monitor.events, output_file, indent=4)


if __name__ == '__main__':
    main()
