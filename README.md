# TODO


# venv
- .\.venv\Scripts\Activate.ps1
- deactivate

# prequisites:
- pip install newspaper3k pandas
- pip install pandas
- pip install "lxml[html_clean]"
# reset
- pip install prompt_toolkit rich
- pip install setuptools

- Grafana downloaden: https://grafana.com/grafana/download?platform=windows
- http://localhost:3000/

# chroma gateway usage:
- python chroma_gateway.py add --collection emails --text "patrick@beispiel.com in Leak gefunden" --metadata '"{""quelle"": ""leak"", ""timestamp"": ""2025-06-22""}"'
- python chroma_gateway.py query --collection emails --query "Holunder Leak LinkedIn" --n 5
- python chroma_gateway.py update --collection emails --id doc_1145699800071594998 --text "Neuer Text" --metadata '{""confidence"": 0.99}'
