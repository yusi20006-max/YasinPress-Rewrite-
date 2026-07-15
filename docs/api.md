# API Documentation

The internal REST-style API is represented by `ApiApp`. Register route handlers with `route(path, handler)` and invoke requests with `handle(path)`. The built-in health route returns status code `200` and a JSON-style body containing `healthy` and `details` keys.
