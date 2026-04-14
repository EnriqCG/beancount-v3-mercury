# beancount-v3-mercury

[![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](LICENSE)

beancount-v3-mercury provides an Importer for converting CSV exports of Mercury checking transactions into [Beancount](https://github.com/beancount/beancount) format.

## Installation

```bash
pip install beancount-v3-mercury
# or
uv add beancount-v3-mercury
```

## Usage

Create an import script (e.g. `import.py`) as follows:

```python
import beancount_mercury
from beangulp import Ingest

importers = [
    beancount_mercury.CheckingImporter(
        'Assets:Checking:Mercury',
        currency='USD',
        account_patterns=[
          # These are example patterns. You can add your own.
          ('GITHUB', 'Expenses:Cloud-Services:Source-Hosting:Github'),
          ('Fedex',  'Expenses:Postage:FedEx'),
        ]
    ),
]

if __name__ == '__main__':
    Ingest(importers).cli()
```

The `account_patterns` parameter is a list of (regex, account) pairs. For each line in your Mercury CSV, `CheckingImporter` will attempt to create a matching posting on the transaction by matching the payee or narration to the regexes. The regexes are in priority order, with earlier patterns taking priority over later patterns.

Once this configuration is in place, you can extract transactions from a Mercury CSV export:

```bash
python import.py extract mercury-transactions.csv
```

## Resources

See [awesome-beancount](https://awesome-beancount.com/) for other publicly available Beancount importers.
