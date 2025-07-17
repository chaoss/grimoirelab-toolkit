from urllib.parse import urlparse, urlunparse

def build_url(base_url, username, password=None, token=None):
    """Build URL with credentials, preserving the original path and query.
    Used to build the URLs for kibiter and elasticsearch if secrets manager is active in the config.

    Args:
        base_url: Original URL from config
        username: Username
        password: Password
        token : Token api token, access token
    Returns:
         str: The url formatted with the corresponding credentials if provided
    """
    # If there's no username or password/token, return the original URL
    if not (username and (password or token)):
        return base_url

    parsed = urlparse(base_url)
    # Prefer token over password if both are somehow provided
    auth_password = token or password

    # Build the 'netloc' part of the URL, which includes credentials
    new_netloc = f"{username}:{auth_password}@{parsed.hostname}"
    if parsed.port:
        new_netloc += f":{parsed.port}"

    # Reconstruct the full URL, preserving the path, query, etc.
    return urlunparse(parsed._replace(netloc=new_netloc))