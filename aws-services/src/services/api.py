import httpx


def execute_get_request(endpoint: str, query_params: dict) -> dict | None:
    try:
        with httpx.Client() as client:
            response = client.get(endpoint, params=query_params, timeout=3.0)

            response.raise_for_status()

            return response.json()

    except httpx.HTTPStatusError as exc:
        print(f"Error de estado HTTP: {exc.response.status_code} - {exc.response.text}")
        return None
    except httpx.RequestError as exc:
        print(f"Error de red/conexión con el servidor: {exc}")
        return None
