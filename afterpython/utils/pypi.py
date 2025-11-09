import httpx


async def fetch_pypi_json(client: httpx.AsyncClient, package_name: str) -> dict | None:
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        # Return None if package doesn't exist or network fails
        print(f"Warning: Could not fetch PyPI JSON for {package_name}: {e}")
        return None
