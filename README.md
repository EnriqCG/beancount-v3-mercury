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
        account_patterns={
          # These are example patterns. You can add your own.
          'Expenses:Cloud-Services:Source-Hosting:Github': ['GITHUB'],
          'Expenses:Postage:FedEx': ['Fedex'],
          'Expenses:Supermarket': ['REWE', 'ALDI'],
        }
    ),
]

if __name__ == '__main__':
    Ingest(importers).cli()
```

The `account_patterns` parameter is a dictionary mapping account names to lists of regex patterns. For each line in your Mercury CSV, `CheckingImporter` will attempt to create a matching posting on the transaction by matching the payee or narration to the regexes. Accounts are checked in dictionary order, with earlier accounts taking priority over later accounts.

Once this configuration is in place, you can extract transactions from a Mercury CSV export:

```bash
python import.py extract mercury-transactions.csv
```

## Beancount v2 Compatibility

Although this package is designed for Beancount v3, it is also compatible with Beancount v2 since it depends on `beancount>=2.3.5` and uses [beangulp](https://github.com/beancount/beangulp) as the importer framework, which supports both versions.

## Resources

See [awesome-beancount](https://awesome-beancount.com/) for other publicly available Beancount importers.
