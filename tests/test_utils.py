"""Tests for utility functions."""

import pytest
from app.utils import normalize_amount, format_date, clean_provider_name


class TestNormalizeAmount:
    """Tests for normalize_amount function."""

    @pytest.mark.parametrize("value,expected", [
        ("$3,000,000.00", 3000000),  # Full format with commas and decimals
        ("S$49.25", 49),              # Singapore dollar
        ("SGD 1,234.56", 1234),       # SGD prefix
        ("USD 100.99", 100),          # USD prefix
        ("3.65", 3),                  # Simple decimal
        ("500", 500),                 # Plain number
        ("99.99", 99),                # Number with cents
        ("$10,000,000.50", 10000000), # Large number
        ("  $100.00  ", 100),         # Whitespace handling
    ])
    def test_valid_amounts(self, value: str, expected: int) -> None:
        """Test various valid amount formats."""
        assert normalize_amount(value) == expected

    def test_integer_input(self) -> None:
        """Test integer passthrough."""
        assert normalize_amount(1000) == 1000

    def test_float_input(self) -> None:
        """Test float truncation."""
        assert normalize_amount(99.99) == 99

    @pytest.mark.parametrize("value", [None, "", "   ", "not a number"])
    def test_invalid_inputs_return_none(self, value) -> None:
        """Test None, empty, whitespace, and invalid inputs return None."""
        assert normalize_amount(value) is None


class TestFormatDate:
    """Tests for format_date function."""

    @pytest.mark.parametrize("value,expected", [
        ("30-Nov-2022", "30/11/2022"),     # Day-Month abbrev-Year
        ("04-JAN-2023", "04/01/2023"),     # Uppercase month
        ("01/01/2025", "01/01/2025"),      # Already correct format
        ("2022-11-30", "30/11/2022"),      # ISO format
        ("15-06-2023", "15/06/2023"),      # Dash separated
        ("15.06.2023", "15/06/2023"),      # Dot separated
        ("15-December-2022", "15/12/2022"), # Full month name
        ("  30-Nov-2022  ", "30/11/2022"), # Whitespace handling
    ])
    def test_valid_dates(self, value: str, expected: str) -> None:
        """Test various valid date formats."""
        assert format_date(value) == expected

    @pytest.mark.parametrize("value", [None, "", "   ", "not a date"])
    def test_invalid_inputs_return_none(self, value) -> None:
        """Test None, empty, whitespace, and invalid inputs return None."""
        assert format_date(value) is None


class TestCleanProviderName:
    """Tests for clean_provider_name function."""

    @pytest.mark.parametrize("value,expected", [
        ("ABC Clinic - Fullerton Health", "ABC Clinic"),  # Suffix removal
        ("Fullerton Health - ABC Clinic", "ABC Clinic"),  # Prefix removal
        ("ABC - FULLERTON HEALTH", "ABC"),                # Case insensitive
        ("ABC - fullerton health", "ABC"),                # Lowercase
        ("XYZ Medical Center", "XYZ Medical Center"),     # No Fullerton Health
        ("  ABC Clinic  ", "ABC Clinic"),                 # Whitespace handling
    ])
    def test_valid_provider_names(self, value: str, expected: str) -> None:
        """Test various provider name scenarios."""
        assert clean_provider_name(value) == expected

    def test_standalone_fullerton_health_returns_none(self) -> None:
        """Test standalone 'Fullerton Health' returns None."""
        assert clean_provider_name("Fullerton Health") is None

    @pytest.mark.parametrize("value", [None, "", "   "])
    def test_invalid_inputs_return_none(self, value) -> None:
        """Test None, empty, and whitespace inputs return None."""
        assert clean_provider_name(value) is None

    def test_double_spaces_cleaned(self) -> None:
        """Test multiple spaces are cleaned up."""
        result = clean_provider_name("ABC  Clinic   Fullerton Health")
        assert "  " not in result
