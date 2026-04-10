PYTHON ?= python3
PACKAGE ?= brotherizer
DEFAULT_DB ?= data/corpus/brotherizer.db
DEFAULT_PACKS ?= data/donor_packs/english_v3.ndjson data/donor_packs/ptbr_v2.ndjson
STYLE_RADAR_INPUT ?= configs/style_radar_seed_signals.json

.PHONY: dev-install test run-api build-corpus build-style-radar build-embeddings docker-build

dev-install:
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m py_compile api/brotherizer_api.py brotherize.py runtime/service.py storage/runtime_db.py tests/test_runtime_service.py tests/test_runtime_api.py
	$(PYTHON) -m unittest tests/test_runtime_service.py tests/test_runtime_api.py

run-api:
	$(PYTHON) -m api.brotherizer_api

build-corpus:
	$(PYTHON) -m storage.build_corpus_db --inputs $(DEFAULT_PACKS) --db $(DEFAULT_DB)

build-style-radar:
	$(PYTHON) -m storage.build_style_radar_db --input $(STYLE_RADAR_INPUT) --db data/corpus/style_radar.db

build-embeddings:
	$(PYTHON) -m storage.build_embedding_index --db $(DEFAULT_DB)

docker-build:
	docker build -t $(PACKAGE):local .
