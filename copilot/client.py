import urllib.request
import json

def post(url, data, timeout=60):
    """Sends a JSON POST request to the local llama-server and returns the parsed JSON response."""
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        raise RuntimeError(f"HTTP POST failed to {url}: {e}")