// Where the frontend finds the API.
// Local development (backend run with `python app.py`):
window.API_BASE = "http://127.0.0.1:5000";
// The Docker image replaces this file with `window.API_BASE = "";`
// so requests go to the same origin and nginx proxies /api to the backend.
