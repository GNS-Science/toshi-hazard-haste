#!/usr/bin/env python
"""Tests for `toshi_hazard_haste` package."""

# import pytest
# import unittest
import numpy as np

from toshi_hazard_haste.gridded_hazard import compute_hazard_at_poe
from toshi_hazard_haste.gridded_hazard.gridded_poe import trim_poes


def test_trim_poes():
    # test max
    accel_levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    poe_values = [10, 9, 8, 9, 6, 5, 4, 3, 2, 1]
    actual_accel, actual_poes = trim_poes(0, 8, accel_levels, poe_values)
    assert [3, 5, 6, 7, 8, 9, 10] == actual_accel
    assert [8, 6, 5, 4, 3, 2, 1] == actual_poes

    # test min
    accel_levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    poe_values = [10, 9, 8, 9, 6, 5, 4, 3, 2, 1]
    actual_accel, actual_poes = trim_poes(3, 10, accel_levels, poe_values)
    assert [1, 2, 3, 4, 5, 6, 7, 8] == actual_accel
    assert [10, 9, 8, 9, 6, 5, 4, 3] == actual_poes

    # test both
    accel_levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    poe_values = [10, 9, 8, 9, 6, 5, 4, 3, 2, 1]
    actual_accel, actual_poes = trim_poes(3, 8, accel_levels, poe_values)
    assert [3, 5, 6, 7, 8] == actual_accel
    assert [8, 6, 5, 4, 3] == actual_poes


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


def test_compute_hazard_at_poe_not_monotone():
    accel_levels = [
        0.0001,
        0.0002,
        0.0004,
        0.0006,
        0.0008,
        0.001,
        0.002,
        0.004,
        0.006,
        0.008,
        0.01,
        0.02,
        0.04,
        0.06,
        0.08,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
        1.2,
        1.4,
        1.6,
        1.8,
        2.0,
        2.2,
        2.4,
        2.6,
        2.8,
        3.0,
        3.5,
        4.0,
        4.5,
        5.0,
        6.0,
        7.0,
        8.0,
        9.0,
        10.0,
    ]

    # not monotone in higher values
    poe_values = [
        6.38968165e-01,
        6.38984832e-01,
        6.38924165e-01,
        6.38617806e-01,
        6.37731501e-01,
        6.36442448e-01,
        6.20736015e-01,
        5.74451729e-01,
        5.26512111e-01,
        4.81553216e-01,
        4.41798316e-01,
        3.04196861e-01,
        1.75138679e-01,
        1.16094023e-01,
        8.31429645e-02,
        6.26495176e-02,
        2.27536245e-02,
        1.14596619e-02,
        6.72560090e-03,
        4.30892990e-03,
        2.92385190e-03,
        2.07031900e-03,
        1.51920210e-03,
        1.14742690e-03,
        8.85213900e-04,
        5.66035800e-04,
        3.75791900e-04,
        2.45817400e-04,
        1.65475200e-04,
        1.14433100e-04,
        8.09856000e-05,
        5.83670000e-05,
        4.27613000e-05,
        3.17869000e-05,
        2.39675000e-05,
        1.21926000e-05,
        6.62650000e-06,
        3.72450000e-06,
        2.15000000e-06,
        7.58300000e-07,
        3.16000000e-07,
        1.51300000e-07,
        7.73000000e-08,
        4.06000000e-08,
    ]

    # poe_values are not monotone
    assert not np.all(np.diff(poe_values) >= 0)

    for idx in [20, 25, 30, 35]:
        computed_acceleration_at_poe = compute_hazard_at_poe(poe_values[idx], accel_levels, poe_values, 1)
        print(idx, poe_values[idx], computed_acceleration_at_poe, accel_levels[idx])
        assert round(accel_levels[idx], 3) == round(computed_acceleration_at_poe, 3)

    accel_levels = [
        0.0001,
        0.0002,
        0.0004,
        0.0006,
        0.0008,
        0.001,
        0.002,
        0.004,
        0.006,
        0.008,
        0.01,
        0.02,
        0.04,
        0.06,
        0.08,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
        1.2,
        1.4,
        1.6,
        1.8,
        2.0,
        2.2,
        2.4,
        2.6,
        2.8,
        3.0,
        3.5,
        4.0,
        4.5,
        5.0,
        6.0,
        7.0,
        8.0,
        9.0,
        10.0,
    ]
    # not monotone at low values
    poe_values = [
        3.19377240e-01,
        3.19376911e-01,
        3.19352911e-01,
        3.18859070e-01,
        3.16647243e-01,
        3.12706010e-01,
        2.80898894e-01,
        2.41411558e-01,
        1.93387035e-01,
        1.58890034e-01,
        1.34048791e-01,
        7.21953604e-02,
        3.35497604e-02,
        1.99410510e-02,
        1.32755955e-02,
        9.36776000e-03,
        2.46211800e-03,
        9.04242900e-04,
        4.08742000e-04,
        2.08512000e-04,
        1.14830400e-04,
        6.61910000e-05,
        3.95460000e-05,
        2.46083000e-05,
        1.58572000e-05,
        6.97740000e-06,
        3.26310000e-06,
        1.53580000e-06,
        7.48900000e-07,
        3.68100000e-07,
        1.85600000e-07,
        9.15000000e-08,
        4.72000000e-08,
        2.49000000e-08,
        1.13000000e-08,
        2.20000000e-09,
        3.00000000e-10,
        1.00000000e-10,
        0.00000000e00,
        0.00000000e00,
        0.00000000e00,
        0.00000000e00,
        0.00000000e00,
        0.00000000e00,
    ]

    assert not np.all(np.diff(poe_values) >= 0)

    for idx in [20, 25, 30, 35]:
        computed_acceleration_at_poe = compute_hazard_at_poe(poe_values[idx], accel_levels, poe_values, 1)
        print(idx, poe_values[idx], computed_acceleration_at_poe, accel_levels[idx])
        assert round(accel_levels[idx], 3) == round(computed_acceleration_at_poe, 3)
