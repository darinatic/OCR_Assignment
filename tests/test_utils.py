"""Tests for utility functions."""

import pytest
from app.utils import normalize_amount, format_date, clean_provider_name


class TestNormalizeAmount:
    """Tests for normalize_amount function."""

    def test_full_format_with_commas_and_decimals(self) -> None:
        """Test $3,000,000.00 → 3000000."""
        assert normalize_amount("$3,000,000.00") == 3000000

    def test_singapore_dollar(self) -> None:
        """Test S$49.25 → 49."""
        assert normalize_amount("S$49.25") == 49

    def test_simple_decimal(self) -> None:
        """Test 3.65 → 3."""
        assert normalize_amount("3.65") == 3

    def test_sgd_prefix(self) -> None:
        """Test SGD prefix removal."""
        assert normalize_amount("SGD 1,234.56") == 1234

    def test_usd_prefix(self) -> None:
        """Test USD prefix removal."""
        assert normalize_amount("USD 100.99") == 100

    def test_plain_number(self) -> None:
        """Test plain number without formatting."""
        assert normalize_amount("500") == 500

    def test_number_with_cents(self) -> None:
        """Test number with cents truncates."""
        assert normalize_amount("99.99") == 99

    def test_integer_input(self) -> None:
        """Test integer passthrough."""
        assert normalize_amount(1000) == 1000

    def test_float_input(self) -> None:
        """Test float truncation."""
        assert normalize_amount(99.99) == 99

    def test_none_input(self) -> None:
        """Test None returns None."""
        assert normalize_amount(None) is None

    def test_empty_string(self) -> None:
        """Test empty string returns None."""
        assert normalize_amount("") is None

    def test_whitespace_only(self) -> None:
        """Test whitespace only returns None."""
        assert normalize_amount("   ") is None

    def test_invalid_string(self) -> None:
        """Test invalid string returns None."""
        assert normalize_amount("not a number") is None

    def test_whitespace_handling(self) -> None:
        """Test whitespace is handled correctly."""
        assert normalize_amount("  $100.00  ") == 100

    def test_large_number(self) -> None:
        """Test large numbers are handled."""
        assert normalize_amount("$10,000,000.50") == 10000000


class TestFormatDate:
    """Tests for format_date function."""

    def test_day_month_abbrev_year(self) -> None:
        """Test 30-Nov-2022 → 30/11/2022."""
        assert format_date("30-Nov-2022") == "30/11/2022"

    def test_day_month_abbrev_uppercase(self) -> None:
        """Test 04-JAN-2023 → 04/01/2023."""
        assert format_date("04-JAN-2023") == "04/01/2023"

    def test_already_correct_format(self) -> None:
        """Test 01/01/2025 stays as 01/01/2025."""
        assert format_date("01/01/2025") == "01/01/2025"

    def test_iso_format(self) -> None:
        """Test ISO format 2022-11-30 → 30/11/2022."""
        assert format_date("2022-11-30") == "30/11/2022"

    def test_dash_separated(self) -> None:
        """Test 15-06-2023 → 15/06/2023."""
        assert format_date("15-06-2023") == "15/06/2023"

    def test_dot_separated(self) -> None:
        """Test 15.06.2023 → 15/06/2023."""
        assert format_date("15.06.2023") == "15/06/2023"

    def test_full_month_name(self) -> None:
        """Test full month name format."""
        assert format_date("15-December-2022") == "15/12/2022"

    def test_none_input(self) -> None:
        """Test None returns None."""
        assert format_date(None) is None

    def test_empty_string(self) -> None:
        """Test empty string returns None."""
        assert format_date("") is None

    def test_whitespace_only(self) -> None:
        """Test whitespace only returns None."""
        assert format_date("   ") is None

    def test_invalid_date(self) -> None:
        """Test invalid date returns None."""
        assert format_date("not a date") is None

    def test_whitespace_handling(self) -> None:
        """Test whitespace is trimmed."""
        assert format_date("  30-Nov-2022  ") == "30/11/2022"


class TestCleanProviderName:
    """Tests for clean_provider_name function."""

    def test_removes_fullerton_health_suffix(self) -> None:
        """Test removal of 'Fullerton Health' suffix."""
        assert clean_provider_name("ABC Clinic - Fullerton Health") == "ABC Clinic"

    def test_removes_fullerton_health_prefix(self) -> None:
        """Test removal of 'Fullerton Health' prefix."""
        assert clean_provider_name("Fullerton Health - ABC Clinic") == "ABC Clinic"

    def test_removes_fullerton_health_standalone(self) -> None:
        """Test standalone 'Fullerton Health' returns None."""
        assert clean_provider_name("Fullerton Health") is None

    def test_case_insensitive_removal(self) -> None:
        """Test case-insensitive removal."""
        assert clean_provider_name("ABC - FULLERTON HEALTH") == "ABC"
        assert clean_provider_name("ABC - fullerton health") == "ABC"

    def test_no_fullerton_health(self) -> None:
        """Test provider name without Fullerton Health passes through."""
        assert clean_provider_name("XYZ Medical Center") == "XYZ Medical Center"

    def test_none_input(self) -> None:
        """Test None returns None."""
        assert clean_provider_name(None) is None

    def test_empty_string(self) -> None:
        """Test empty string returns None."""
        assert clean_provider_name("") is None

    def test_whitespace_only(self) -> None:
        """Test whitespace only returns None."""
        assert clean_provider_name("   ") is None

    def test_whitespace_handling(self) -> None:
        """Test whitespace is handled correctly."""
        assert clean_provider_name("  ABC Clinic  ") == "ABC Clinic"

    def test_double_spaces_cleaned(self) -> None:
        """Test multiple spaces are cleaned up."""
        result = clean_provider_name("ABC  Clinic   Fullerton Health")
        assert "  " not in result
