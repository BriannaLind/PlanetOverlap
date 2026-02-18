import os
import requests


def create_session() -> requests.Session:
    """
    Create authenticated Planet API session.
    """
    api_key = os.getenv("PLANET_API_KEY")

    if not api_key:
        raise EnvironmentError("PLANET_API_KEY not set.")

    session = requests.Session()
    session.auth = (api_key, "")
    return session
