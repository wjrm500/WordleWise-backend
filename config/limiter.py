from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize limiter without app (will be initialized later with init_app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
    headers_enabled=True
)
