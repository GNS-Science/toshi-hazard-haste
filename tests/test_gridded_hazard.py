#!/usr/bin/env python
"""Tests for `toshi_hazard_haste` package."""

# import pytest
import unittest
import csv
from pathlib import Path

from toshi_hazard_haste.gridded_hazard import calc_gridded_hazard
from toshi_hazard_haste import model

from moto import mock_dynamodb

from toshi_hazard_store import model as ths_model

# from nzshm_common.grids import RegionGrid
from nzshm_common.location import CodedLocation

HAZARD_MODEL_ID = 'MODEL_THE_FIRST'


def get_csv_sample_ranges(csv_path, limit=200):
    locations, vs30s, imts, aggs = set(), set(), set(), set()
    csvdata = csv.reader(open(csv_path, 'r'))
    next(csvdata)
    for row in list(csvdata)[:limit]:
        agg, imt, lat, lon, vs30 = row[:5]
        aggs.add(agg)
        imts.add(imt)
        vs30s.add(float(vs30))
        locations.add(CodedLocation(float(lat), float(lon), resolution=0.001).code)
    return list(locations), list(vs30s), list(imts), list(aggs)


def hazard_aggregation_models(csv_path, limit=200):

    csvdata = csv.reader(open(csv_path, 'r'))
    header = next(csvdata)
    poe_accels = [float(val[4:]) for val in header[5:]]
    for row in list(csvdata)[:limit]:
        agg, imt, lat, lon, vs30 = row[:5]
        poe_values = row[5:]
        lvps = list(
            map(
                lambda x: ths_model.LevelValuePairAttribute(lvl=float(x[0]), val=float(x[1])),
                zip(poe_accels, poe_values),
            )
        )
        loc = CodedLocation(float(lat), float(lon), resolution=0.001)
        yield ths_model.HazardAggregation(
            values=lvps,
            vs30=float(vs30),
            agg=agg,
            imt=imt,
            hazard_model_id=HAZARD_MODEL_ID,
        ).set_location(loc)


def setup_fixtures():
    pass


@mock_dynamodb
class GriddedHazardTest(unittest.TestCase):
    def setUp(self):
        model.migrate()
        ths_model.migrate()
        self._csv_hazard = Path(__file__).parent / 'fixtures' / 'sample_hazard_data.csv'
        super(GriddedHazardTest, self).setUp()

    def tearDown(self):
        model.drop_tables()
        ths_model.drop_tables()
        return super(GriddedHazardTest, self).tearDown()

    def test_calculate_gridded_hazard(self):
        # load fixture and create sample hazard_curves

        with ths_model.HazardAggregation.batch_write() as batch:
            for haz in hazard_aggregation_models(self._csv_hazard):
                batch.save(haz)

        # query the hazard_curves, building and saving the gridded poes
        locations, vs30s, imts, aggs = get_csv_sample_ranges(self._csv_hazard)

        # builing & saving the models
        poe_levels = [0.02, 0.1]
        location_grid_id = "NZ_0_2_NB_1_1"  # the NZ 0.2 degree grid
        with model.GriddedHazard.batch_write() as batch:
            for gridded_haz in calc_gridded_hazard(location_grid_id, poe_levels, [HAZARD_MODEL_ID], vs30s, imts, aggs):
                batch.save(gridded_haz)

        # test we can retrieve something
        count = 0
        poes = 0
        for ghaz in model.GriddedHazard.scan():
            poes += len(list(filter(lambda x: x is not None, ghaz.grid_poes)))
            count += 1

        print('table scan produced %s gridded_hazard rows and %s poe levels' % (count, poes))
