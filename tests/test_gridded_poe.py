#!/usr/bin/env python
"""Tests for `toshi_hazard_haste` package."""

# import pytest
# import unittest
from toshi_hazard_haste.gridded_hazard import compute_hazard_at_poe


def test_compute_hazard_at_poe_some_level_of_acceleration():
    """Basic test cases from https://numpy.org/doc/stable/reference/generated/numpy.interp.html?highlight=interp."""

    accel_levels = [0.01, 0.02, 0.04, 0.06, 0.08, 0.1]
    poe_values = [
        0.008537745373114913,
        0.0040060533686281374,
        0.0016329920838922263,
        0.000809913284701147,
        0.00046319636749103665,
        0.0002899981045629829,
    ]

    # iterate all the levels and check that the xp crossing is ~close enough~ equal to the desired acceleration level
    for idx in range(len(poe_values)):
        computed_acceleration_at_poe = compute_hazard_at_poe(poe_values[idx], accel_levels, poe_values, 1)
        print(idx, poe_values[idx], computed_acceleration_at_poe)
        assert round(accel_levels[idx], 4) == round(computed_acceleration_at_poe, 4)
