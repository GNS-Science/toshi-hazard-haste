#!/usr/bin/env python
"""Tests for `toshi_hazard_haste` package."""

# import pytest
import unittest

# import random
import itertools

# import io
# import csv

from moto import mock_dynamodb

from nzshm_common.grids.region_grid import load_grid

# from nzshm_common.location.code_location import CodedLocation
from nzshm_common.location.coded_location import CodedLocation

from toshi_hazard_store import model

HAZARD_MODEL_ID = "MYHAZID"
GRID_02 = load_grid('NZ_0_2_NB_1_1')
VS30S = [250, 350, 450]
IMTS = ['PGA', 'SA(0.5)']
AGGS = ['mean', '0.10']
LOCS = [CodedLocation(*o, 0.001) for o in GRID_02[20:50]]
N_LVLS = 29


def build_hazard_aggregation_models():

    lvps = list(map(lambda x: model.LevelValuePairAttribute(lvl=x / 1e3, val=(x / 1e6)), range(1, N_LVLS)))
    for loc, vs30, agg in itertools.product(LOCS, VS30S, AGGS):
        for imt, val in enumerate(IMTS):
            yield model.HazardAggregation(
                values=lvps,
                vs30=vs30,
                agg=agg,
                imt=val,
                hazard_model_id=HAZARD_MODEL_ID,
            ).set_location(loc)


@mock_dynamodb
class HighLevelHazard(unittest.TestCase):
    def setUp(self):
        model.migrate()
        with model.HazardAggregation.batch_write() as batch:
            for item in build_hazard_aggregation_models():
                batch.save(item)

    def no_first_test(self):
        pass
