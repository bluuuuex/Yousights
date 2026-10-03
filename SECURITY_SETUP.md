# Legacy service security setup

The services bind to loopback with the debugger disabled. Before exposing them,
use production WSGI hosting, TLS, authentication and network restrictions.
The backend requires nonempty YOUSIGHTS_BASIC_AUTH_USERNAME and
YOUSIGHTS_BASIC_AUTH_PASSWORD. Set YOUSIGHTS_MONGODB_URI in the runtime secret
store; MongoDB networking now has bounded timeouts and its URI is not logged.

A database credential and Google Maps key were present in source. Rotate/revoke
them at their providers. Removing them here does not erase historical Git
commits or revoke the credentials. Local copies of credential files remain
private: copy credentials.example.json to ignored credentials.json and protect
filesystem permissions. The examples contain no usable secrets.

YOUSIGHTS_MAPS_BROWSER_KEY enables Google Maps; use only a browser key restricted
to your deployment referrers and required APIs. A configured browser key is
visible to browsers. Maps is disabled when the setting is absent.

HTTP calls have connection/read timeouts. Meetup refresh secrets go in POST
bodies rather than URLs. The static frontend no longer has a log-reading route.
Deployment requires a preinstalled IBM Cloud CLI and IBM_CLOUD_API_KEY,
IBM_CLOUD_ORG, optionally IBM_CLOUD_SPACE. No remote installer is executed;
commands use argv lists and login arguments/output are not printed. Deployment
runs only as a script when MERGE_PULL_REQUEST=true.

Each service requirements file is self-contained for directory-based cloud staging.
The API stack migrates Flask-RESTPlus to maintained Flask-RESTX and
updates Flask/CORS/Requests/PyYAML. The non-NLP services select Python 3.12.
The analytics NLP/scientific libraries and bundled spaCy 2 model remain obsolete;
its Python 3.7 runtime declaration is incompatible with modern NLTK/shared
HTTP dependencies. Do not deploy analyticsAI until that stack/model and runtime
are migrated with real transcript integration tests. Offline security and API
schema tests cannot establish cloud or NLP deployability.

API request bodies are capped at 1 MiB. Cross-origin access is disabled by
default; YOUSIGHTS_CORS_ORIGINS may list trusted exact frontend origins. Wildcard
origins are ignored. Service-to-service Basic Auth comes from runtime secrets.
