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
AnalyticsAI now selects Python 3.12.15 in Cloud Foundry's `runtime.txt`, replacing
the unsupported Python 3.7 runtime. `.python-version` selects the 3.12 series for
local tooling. Cloud Foundry staging requires a buildpack supporting 3.12.15;
the upstream manifest checked during review still lists 3.12.14. Update the
buildpack when 3.12.15 is available rather than silently selecting an older
runtime. Local compatibility tests used 3.12.13; cloud staging is unverified. Install from `analyticsAI/requirements.txt`; it includes a complete
version-pinned, hashed `requirements.lock`. Maintain direct dependencies in
`requirements.in` and regenerate the lock with:

```sh
uv pip compile analyticsAI/requirements.in --python-version 3.12 --generate-hashes --output-file analyticsAI/requirements.lock
```

The active NLP pipeline uses spaCy 3.8 and the official English 3.8.0 model
wheel, pinned by URL and hash. The old bundled spaCy 2 model is retained only as
legacy source data and is no longer installed. Unused PDF/summarization helpers
and their obsolete Tika/Gensim dependencies have been removed. Custom stopwords,
WordNet lemmatization and the TextRank algorithm remain in place; isolated graph
nodes now get deterministic zero normalization instead of uninitialized memory.
NLP rejects text above 100000 characters or 10000 tokens, transcripts above
10000 segments and TextRank graphs above 1000 unique candidate words. Limits
also cover DB/upstream transcripts before repeated period processing; each
dense matrix is at most 1000 by 1000. Graph edge deduplication uses a set while
preserving insertion order and existing weights. Oversized analyses fail rather
than allocating an unbounded graph.
New model weights can change POS tags, entities and keyword rankings relative
to the old model, so compare representative deployment transcripts before rollout.

Run offline migration checks (real local NLP, synthetic transcripts and mocked
MongoDB/cloud clients) in the installed environment:

```sh
python -m unittest discover -s analyticsAI/test -p test_nlp_runtime.py -v
python -m unittest discover -s tests -v
```

NLTK 3.10.3 still has the unfixed model-artifact path sandbox advisory
CVE-2026-81726 / GHSA-8mgp-746c-j5xp. This application uses bundled trusted
stopwords/WordNet and `word_tokenize(..., preserve_line=True)`, and does not call
the affected parser/perceptron model import/export APIs or let users select their
paths. Do not introduce those APIs with user-controlled paths. Dependency audit
cannot assess the official spaCy model because it is distributed outside PyPI;
the model's upstream compatibility and wheel hash are checked separately.
Offline tests establish local NLP/API compatibility, not cloud deployment or
live service correctness.

API request bodies are capped at 1 MiB. Cross-origin access is disabled by
default; YOUSIGHTS_CORS_ORIGINS may list trusted exact frontend origins. Wildcard
origins are ignored. Service-to-service Basic Auth comes from runtime secrets.
