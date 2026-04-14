import io
import textwrap

from beancount.parser import printer

from . import CheckingImporter


def _unindent(indented):
    return textwrap.dedent(indented).lstrip()


def _stringify_directives(directives):
    f = io.StringIO()
    printer.print_entries(directives, file=f)
    return f.getvalue()


def test_identifies_mercury_file(tmp_path):
    mercury_file = tmp_path / 'transactions-dummy-to-feb052022.csv'
    mercury_file.write_text(
        _unindent("""
            Date (UTC),Description,Amount,Status,Bank Description,Reference,Note
            02-04-2022,Joe Vendor,-550.00,Sent,Send Money transaction initiated on Mercury,"From Dummy, LLC for bowling balls",
            """)
    )

    assert CheckingImporter(account='Assets:Checking:Mercury').identify(
        str(mercury_file)
    )


def test_extracts_single_transaction_without_matching_account(tmp_path):
    mercury_file = tmp_path / 'transactions-dummy-to-feb052022.csv'
    mercury_file.write_text(
        _unindent("""
            Date (UTC),Description,Amount,Status,Bank Description,Reference,Note
            02-04-2022,Joe Vendor,-550.00,Sent,Send Money transaction initiated on Mercury,"From Dummy, LLC for bowling balls",
            """)
    )

    directives = CheckingImporter(account='Assets:Checking:Mercury').extract(
        str(mercury_file)
    )

    assert (
        _unindent(
            """
        2022-02-04 * "Joe Vendor" "Send Money transaction initiated on Mercury - From Dummy, LLC for bowling balls"
          Assets:Checking:Mercury  -550.00 USD
        """.rstrip()
        )
        == _stringify_directives(directives).strip()
    )


# Mercury changed the file format in 2022-11 to add UTC after the date column
# label, so verify we can still read the old format.
def test_extracts_single_transaction_without_matching_account_legacy_format(
    tmp_path,
):
    mercury_file = tmp_path / 'transactions-dummy-to-feb052022.csv'
    mercury_file.write_text(
        _unindent("""
            Date,Description,Amount,Status,Bank Description,Reference,Note
            02-04-2022,Joe Vendor,-550.00,Sent,Send Money transaction initiated on Mercury,"From Dummy, LLC for bowling balls",
            """)
    )

    directives = CheckingImporter(account='Assets:Checking:Mercury').extract(
        str(mercury_file)
    )

    assert (
        _unindent(
            """
        2022-02-04 * "Joe Vendor" "Send Money transaction initiated on Mercury - From Dummy, LLC for bowling balls"
          Assets:Checking:Mercury  -550.00 USD
        """.rstrip()
        )
        == _stringify_directives(directives).strip()
    )


def test_extracts_single_transaction_with_matching_account(tmp_path):
    mercury_file = tmp_path / 'transactions-dummy-to-feb052022.csv'
    mercury_file.write_text(
        _unindent("""
            Date (UTC),Description,Amount,Status,Bank Description,Reference,Note
            02-04-2022,Bowlers Paradise,-550.00,Sent,Send Money transaction initiated on Mercury,"From Dummy, LLC for bowling balls",
            """)
    )

    directives = CheckingImporter(
        account='Assets:Checking:Mercury',
        account_patterns={
            'Expenses:Equipment:Bowling-Balls:Bowlers-Paradise': [
                '^Bowlers Paradise$',
            ],
        },
    ).extract(str(mercury_file))

    assert (
        _unindent(
            """
        2022-02-04 * "Bowlers Paradise" "Send Money transaction initiated on Mercury - From Dummy, LLC for bowling balls"
          Assets:Checking:Mercury                            -550.00 USD
          Expenses:Equipment:Bowling-Balls:Bowlers-Paradise   550.00 USD
        """.rstrip()
        )
        == _stringify_directives(directives).strip()
    )


def test_matches_transactions_by_priority(tmp_path):
    mercury_file = tmp_path / 'transactions-dummy-to-feb052022.csv'
    mercury_file.write_text(
        _unindent("""
            Date (UTC),Description,Amount,Status,Bank Description,Reference,Note
            02-04-2022,Bowlers Paradise,-550.00,Sent,Send Money transaction initiated on Mercury,"From Dummy, LLC for bowling balls",
            02-05-2022,Paradise Golf,-150.75,Sent,PARADISE GOLF,,
            """)
    )

    directives = CheckingImporter(
        account='Assets:Checking:Mercury',
        account_patterns={
            'Expenses:Equipment:Bowling-Balls:Bowlers-Paradise': [
                '^Bowlers Paradise$',
            ],
            'Expenses:Training:Paradise-Golf': ['Paradise'],
        },
    ).extract(str(mercury_file))

    assert (
        _unindent(
            """
        2022-02-04 * "Bowlers Paradise" "Send Money transaction initiated on Mercury - From Dummy, LLC for bowling balls"
          Assets:Checking:Mercury                            -550.00 USD
          Expenses:Equipment:Bowling-Balls:Bowlers-Paradise   550.00 USD

        2022-02-05 * "Paradise Golf" "PARADISE GOLF"
          Assets:Checking:Mercury          -150.75 USD
          Expenses:Training:Paradise-Golf   150.75 USD
        """.rstrip()
        )
        == _stringify_directives(directives).strip()
    )


def test_matches_multiple_patterns_per_account(tmp_path):
    mercury_file = tmp_path / 'transactions-dummy-to-feb052022.csv'
    mercury_file.write_text(
        _unindent("""
            Date (UTC),Description,Amount,Status,Bank Description,Reference,Note
            02-04-2022,REWE Supermarket,-23.50,Sent,REWE SUPERMARKET,,
            02-05-2022,ALDI Store,-15.75,Sent,ALDI STORE,,
            """)
    )

    directives = CheckingImporter(
        account='Assets:Checking:Mercury',
        account_patterns={
            'Expenses:Supermarket': ['REWE', 'ALDI'],
        },
    ).extract(str(mercury_file))

    assert (
        _unindent(
            """
        2022-02-04 * "REWE Supermarket" "REWE SUPERMARKET"
          Assets:Checking:Mercury  -23.50 USD
          Expenses:Supermarket      23.50 USD

        2022-02-05 * "ALDI Store" "ALDI STORE"
          Assets:Checking:Mercury  -15.75 USD
          Expenses:Supermarket      15.75 USD
        """.rstrip()
        )
        == _stringify_directives(directives).strip()
    )


def test_extracts_incoming_transaction(tmp_path):
    mercury_file = tmp_path / 'transactions-dummy-to-feb052022.csv'
    mercury_file.write_text(
        _unindent("""
            Date (UTC),Description,Amount,Status,Bank Description,Reference,Note
            01-30-2022,Charlie Customer,694.04,Sent,CHARLIE CUSTOMER,,
            """)
    )

    directives = CheckingImporter(
        account='Assets:Checking:Mercury',
        account_patterns={
            'Income:Sales': ['^Charlie Customer$'],
        },
    ).extract(str(mercury_file))

    assert (
        _unindent(
            """
        2022-01-30 * "Charlie Customer" "CHARLIE CUSTOMER"
          Assets:Checking:Mercury   694.04 USD
          Income:Sales             -694.04 USD
        """.rstrip()
        )
        == _stringify_directives(directives).strip()
    )


def test_ignores_failed_transaction(tmp_path):
    mercury_file = tmp_path / 'transactions-dummy-to-feb052022.csv'
    mercury_file.write_text(
        _unindent("""
            Date (UTC),Description,Amount,Status,Bank Description,Reference,Note
            01-29-2021,Expensivo's Diamond Emporium,-5876.95,Failed,Expensivo's Diamond Emporium; TRANSACTION_BLOCKED --  C10 -- User is not allowed to send over 5000.0 per 1 day(s).,,
            """)
    )

    directives = CheckingImporter(account='Assets:Checking:Mercury').extract(
        str(mercury_file)
    )

    assert len(directives) == 0
