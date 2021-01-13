import json
import urllib3


def get_ip_ranges(events, context):
    if 'Region' not in events or 'AwsServiceName' not in events or 'DestinationIpAddressRanges' not in events:
        raise KeyError('Requires Region,AwsServiceName,DestinationIpAddressRanges  in events')

    # Fetch ips based on aws service
    http = urllib3.PoolManager()
    r = http.request('GET', 'https://ip-ranges.amazonaws.com/ip-ranges.json')

    ip_ranges = json.loads(r.data.decode('utf-8'))['prefixes']

    ips = []
    for item in ip_ranges:
        if item["service"] == events['AwsServiceName'] and item["region"] == events['Region']:
            ips.append(item['ip_prefix'])

    # Add additional ip ranges specified
    for ip in events['DestinationIpAddressRanges']:
        ips.append(ip)

    # Return ip ranges as string separated by whitespace
    return {'IpAddressRanges': " ".join(ips)}
