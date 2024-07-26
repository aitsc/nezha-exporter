from fastapi import FastAPI, Response, HTTPException, status
import httpx
from prometheus_client import Gauge, generate_latest, CollectorRegistry
import uvicorn
import argparse
from tsc_base import merge_dict, dict_to_pair, get
from pprint import pprint
import json


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
    elif isinstance(v, (list, dict)):
        try:
            return json.dumps(v, ensure_ascii=False)
        except:
            ...
    return str(v)


@app.get(args.web_telemetry_path)
async def metrics():
    server_details: list[dict] = await get_nezha_info(f"{args.endpoint}/api/v1/server/details?id=")
    one_server = merge_dict(server_details)
    # pprint(one_server)
    
    labels_keys: dict[str, list[str]] = {}
    for keys, v in dict_to_pair(one_server):
        label = '_'.join(keys)
        if not isinstance(v, (int, float)) and (
            isinstance(v, str) or
            keys[0] == 'host'
        ):
            labels_keys[label] = keys
    labels = list(labels_keys)
    
    registry = CollectorRegistry()
    metrics_warp: dict[str, Gauge] = {}
    
    for details in server_details:
        if not isinstance(details, dict):
            continue
        labels_values = [value_norm(get(keys, details, '')) for keys in labels_keys.values()]
        
        for keys, v in dict_to_pair(details):
            metric = '_'.join(keys)
            if metric in labels_keys:
                continue
            
            if isinstance(v, (int, float)):
                if metric not in metrics_warp:
                    metrics_warp[metric] = Gauge(f'nezha_{metric}', f'nezha {keys}', labels, registry=registry)
                metrics_warp[metric].labels(*labels_values).set(v)
                
            elif isinstance(v, list) and keys[-1] == 'Temperatures':
                for temp_obj in v:
                    if not isinstance(temp_obj, dict):
                        continue
                    name = temp_obj.get('Name')
                    temp = temp_obj.get('Temperature')
                    if not (name and isinstance(temp, (int, float))):
                        continue
                    metric_ = f'{metric}_{name}'
                    if metric_ not in metrics_warp:
                        metrics_warp[metric_] = Gauge(f'nezha_{metric_}', f'nezha {keys + [name]}', labels, registry=registry)
                    metrics_warp[metric_].labels(*labels_values).set(temp)
                    
    return Response(generate_latest(registry), media_type='text/plain')


def main():
    listen_address, listen_port = args.web_listen_address.split(':')
    uvicorn.run(app, host=listen_address, port=int(listen_port))


if __name__ == '__main__':
    main()
