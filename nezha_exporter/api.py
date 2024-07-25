from fastapi import FastAPI, Response, HTTPException, status
import httpx
from prometheus_client import Gauge, generate_latest, CollectorRegistry, Info
import uvicorn
import argparse
from tsc_base import merge_dict
from pprint import pprint


app = FastAPI()


def get_args():
    parser = argparse.ArgumentParser(
        description="Prometheus metrics nezha exporter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--web.listen-address', dest='web_listen_address', type=str, default=':9221', help='Address to listen on for web interface and telemetry.')
    parser.add_argument('--web.telemetry-path', dest='web_telemetry_path', type=str, default='/metrics', help='Path under which to expose metrics.')
    parser.add_argument('-e', '--endpoint', type=str, required=True, help='Nezha dashboard site, e.g. http://dashboard.example.com:8008')
    parser.add_argument('-t', '--endpoint-token', type=str, required=True, help='Authorization token for the nezha API.')
    return parser.parse_args()


args = get_args()


async def get_nezha_info(url: str) -> dict:
    headers = {
        "Authorization": args.endpoint_token
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
        except BaseException as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={'error': str(e), 'url': url})
        
        if response.status_code != 200:
            response_content = await response.aread()
            raise HTTPException(status_code=response.status_code, detail=response_content)
        
    ret = response.json()
    if not ret.get('result'):
        detail = {'error': 'Failed to get nezha info', 'nezha': ret, 'url': url}
        print(detail)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    return ret['result']


def value_norm(v):
    if isinstance(v, (int, float)):
        return v
    return str(v)


@app.get(args.web_telemetry_path)
async def metrics():
    server_details: list[dict] = await get_nezha_info(f"{args.endpoint}/api/v1/server/details?id=")
    labels = [
        'id',
        'ipv4',
        'ipv6',
        'name',
        'tag',
        'valid_ip',
    ]
    one_server = merge_dict(server_details)
    # pprint(one_server)
    
    registry = CollectorRegistry()
    host_info = Info('nezha_host_info', 'Host static information', labels, registry=registry)
    last_active = Gauge('nezha_last_active', 'Last active time of the server', labels, registry=registry)
    # status
    status_metrics = {
        k: Gauge(f'nezha_status_{k}', f'status of {k}', labels, registry=registry) 
        for k, v in (one_server.get('status') or {}).items() if isinstance(v, (int, float))}
    # status.Temperatures
    temperatures_metrics: dict[str, Gauge] = {}
    temperatures: list[dict] = (one_server.get('status') or {}).get('Temperatures')
    if temperatures:
        for temp_obj in temperatures:
            name = temp_obj.get('Name')
            if name and name not in temperatures_metrics:
                temperatures_metrics[name] = Gauge(
                    f'nezha_temperature_{name}', f'Temperature of the server {name}', labels, registry=registry)
    
    for details in server_details:
        if not isinstance(details, dict):
            continue
        labels_values = [value_norm(details.get(l)) for l in labels]
        
        host_info.labels(*labels_values).info({
            str(k): str(v) for k, v in details.get('host', {}).items()
        })
        if isinstance(details.get('last_active'), (int, float)):
            last_active.labels(*labels_values).set(details.get('last_active'))
        # status
        for k, v in (details.get('status') or {}).items():
            if not isinstance(v, (int, float)):
                continue
            status_metrics[k].labels(*labels_values).set(v)
        # status.Temperatures
        temperatures: list[dict] = (details.get('status') or {}).get('Temperatures')
        if temperatures:
            for temp_obj in temperatures:
                name = temp_obj.get('Name')
                temp = temp_obj.get('Temperature')
                if name and isinstance(temp, (int, float)):
                    temperatures_metrics[name].labels(*labels_values).set(temp)
                    
    return Response(generate_latest(registry), media_type='text/plain')


def main():
    listen_address, listen_port = args.web_listen_address.split(':')
    uvicorn.run(app, host=listen_address, port=int(listen_port))


if __name__ == '__main__':
    main()
