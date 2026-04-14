import csv
import datetime
import os
import re

import beangulp
import titlecase
from beancount.core import amount, data, flags
from beancount.core import number as beancount_number

_COLUMN_DATE = 'Date (UTC)'
# Prior to 2022-11, the date column label didn't have the UTC designation.
_COLUMN_DATE_LEGACY = 'Date'
_COLUMN_PAYEE = 'Description'
_COLUMN_DESCRIPTION = 'Bank Description'
_COLUMN_REFERENCE = 'Reference'
_COLUMN_AMOUNT = 'Amount'
_COLUMN_STATUS = 'Status'

_FILENAME_PATTERN = re.compile(r'transactions-.+\.CSV', re.IGNORECASE)


class CheckingImporter(beangulp.Importer):
    def __init__(self, account, currency='USD', account_patterns=None):
        self._account = account
        self._currency = currency
        self._account_patterns = []
        if account_patterns:
            for account_name, patterns in account_patterns.items():
                for pattern in patterns:
                    self._account_patterns.append(
                        (
                            re.compile(pattern, flags=re.IGNORECASE),
                            account_name,
                        )
                    )

    def _parse_amount(self, amount_raw):
        return amount.Amount(
            beancount_number.D(amount_raw.replace('$', '')), self._currency
        )

    def date(self, filepath):
        return max(map(lambda x: x.date, self.extract(filepath)))

    def account(self, filepath):
        return self._account

    def identify(self, filepath):
        return _FILENAME_PATTERN.search(os.path.basename(filepath))

    def extract(self, filepath, existing=None):
        transactions = []

        with open(filepath, encoding='utf-8') as csv_file:
            for index, row in enumerate(csv.DictReader(csv_file)):
                metadata = data.new_metadata(filepath, index)
                transaction = self._extract_transaction_from_row(row, metadata)
                if not transaction:
                    continue
                transactions.append(transaction)

        return transactions

    def _extract_transaction_from_row(self, row, metadata):
        if row[_COLUMN_STATUS] and row[_COLUMN_STATUS] == 'Failed':
            return None

        date_raw = None
        if _COLUMN_DATE in row:
            date_raw = row[_COLUMN_DATE]
        else:
            date_raw = row[_COLUMN_DATE_LEGACY]

        transaction_date = datetime.datetime.strptime(
            date_raw, '%m-%d-%Y'
        ).date()

        payee = titlecase.titlecase(row[_COLUMN_PAYEE])

        narration_list = []
        description = row[_COLUMN_DESCRIPTION]
        if description:
            narration_list.append(description)
        reference = row[_COLUMN_REFERENCE]
        if reference:
            narration_list.append(reference)
        narration = ' - '.join(narration_list)

        if row[_COLUMN_AMOUNT]:
            transaction_amount = self._parse_amount(row[_COLUMN_AMOUNT])
        else:
            return None  # 0 dollar transaction

        if transaction_amount == amount.Amount(
            beancount_number.D(0), self._currency
        ):
            return None

        postings = [
            data.Posting(
                account=self._account,
                units=transaction_amount,
                cost=None,
                price=None,
                flag=None,
                meta=None,
            )
        ]
        for pattern, account_name in self._account_patterns:
            if pattern.search(payee) or pattern.search(narration):
                postings.append(
                    data.Posting(
                        account=account_name,
                        units=-transaction_amount,
                        cost=None,
                        price=None,
                        flag=None,
                        meta=None,
                    )
                )
                break

        return data.Transaction(
            meta=metadata,
            date=transaction_date,
            flag=flags.FLAG_OKAY,
            payee=payee,
            narration=narration,
            tags=data.EMPTY_SET,
            links=data.EMPTY_SET,
            postings=postings,
        )
