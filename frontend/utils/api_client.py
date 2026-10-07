import requests
from typing import Dict, Any, Optional

BACKEND_URL = "http://127.0.0.1:8000/api"

class APIClient:
    @staticmethod
    def get(endpoint: str, params: Optional[Dict[str, Any]] = None):
        url = f"{BACKEND_URL}{endpoint}"
        try:
            resp = requests.get(url, params=params, timeout=25.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def post(endpoint: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None):
        url = f"{BACKEND_URL}{endpoint}"
        try:
            resp = requests.post(url, json=json_data, params=params, timeout=35.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def upload_file(endpoint: str, files: Dict[str, Any], data: Dict[str, Any]):
        url = f"{BACKEND_URL}{endpoint}"
        try:
            resp = requests.post(url, files=files, data=data, timeout=60.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def delete(endpoint: str):
        url = f"{BACKEND_URL}{endpoint}"
        try:
            resp = requests.delete(url, timeout=15.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
