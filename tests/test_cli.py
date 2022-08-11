#!/usr/bin/env python
"""Tests for `toshi_hazard_haste` package."""

import pytest
from click.testing import CliRunner

from toshi_hazard_haste import cli


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string
    del response


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.calc_gridded_hazard)
    assert result.exit_code == 0


def test_cli_help():
    runner = CliRunner()
    help_result = runner.invoke(cli.calc_gridded_hazard, ['--help'])
    assert help_result.exit_code == 0
    assert 'Show this message and exit.' in help_result.output


def test_cli_list_site_lists():
    runner = CliRunner()
    help_result = runner.invoke(cli.calc_gridded_hazard, ['--list-site-lists'])
    assert help_result.exit_code == 0
    assert 'ENUM name' in help_result.output


def test_cli_dry_run():
    runner = CliRunner()
    help_result = runner.invoke(cli.calc_gridded_hazard, ['--dry-run'])
    assert help_result.exit_code == 0
    assert 'dry-run None None None' in help_result.output
