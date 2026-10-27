#!/bin/bash
cd /home/demon/shorts_studio
source venv/bin/activate
python -m app.script.pipeline --topic "Using Perplexity Pages to create a shareable research report" --out data/metadata_strong.json
