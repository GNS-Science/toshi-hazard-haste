#!/usr/bin/env python
"""Tests for `toshi_hazard_haste` package."""

# import pytest
import unittest
import csv

# import time
from pathlib import Path

from toshi_hazard_haste import model
from toshi_hazard_haste.gridded_hazard import calc_gridded_hazard

from moto import mock_dynamodb

from toshi_hazard_store import model as ths_model

from nzshm_common.grids import RegionGrid
from nzshm_common.location import CodedLocation

HAZARD_MODEL_ID = 'MODEL_THE_FIRST'


def get_csv_sample_ranges(csv_path, limit=100):
    locations, vs30s, imts, aggs = set(), set(), set(), set()
    csvdata = csv.reader(open(csv_path, 'r'))
    next(csvdata)
    for row in list(csvdata)[:limit]:
        agg, imt, lat, lon, vs30 = row[:5]
        aggs.add(agg)
        imts.add(imt)
        vs30s.add(float(vs30))
        locations.add(CodedLocation(float(lat), float(lon), resolution=0.001))
    return list(locations), list(vs30s), list(imts), list(aggs)


def hazard_aggregation_models(csv_path, limit=100):

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


# @mock_dynamodb
# def setup_module():
#     model.migrate()
#     ths_model.migrate()
#     csv_hazard = Path(__file__).parent / 'fixtures' / 'sample_hazard_data.csv'
#     # load fixture and create sample hazard_curves
#     for haz in hazard_aggregation_models(csv_hazard):
#         haz.save()

#     return True
#     # for m in ths_model.HazardAggregation.scan():
#     #     time.sleep(0.01)
#     #     pass
#     # super(GriddedHazardTest, self).setUp()

# @mock_dynamodb
# def tearDown(self):
#     model.drop_tables()
#     ths_model.drop_tables()
#     return super(GriddedHazardTest, self).tearDown()


class GriddedHazardTest(unittest.TestCase):
    @mock_dynamodb
    def test_calculate_gridded_hazard(self):
        """This test is a TDD hack, iterating on the features and testing them all in one humungous test.

        TODO: split up this and test the parts individually.


        """
        model.migrate()
        ths_model.migrate()
        csv_hazard = Path(__file__).parent / 'fixtures' / 'sample_hazard_data.csv'
        # load fixture and create sample hazard_curves
        for haz in hazard_aggregation_models(csv_hazard, 200):
            haz.save()

        hag_cnt = 0
        for m in ths_model.HazardAggregation.scan():
            hag_cnt += 1

        assert hag_cnt == 200

        csv_hazard = Path(__file__).parent / 'fixtures' / 'sample_hazard_data.csv'

        # query the hazard_curves, building and saving the gridded poes
        locations, vs30s, imts, aggs = get_csv_sample_ranges(csv_hazard, 200)

        assert len(locations) == 5

        # builing & saving the models
        poe_levels = [0.02, 0.1]
        location_grid_id = "NZ_0_2_NB_1_1"  # the NZ 0.2 degree grid
        grid = RegionGrid[location_grid_id]

        # with model.GriddedHazard.batch_write() as batch:
        # TODO: why is calc_gridded_hazard producing falkey results - this is why tests fail
        saved = 0
        for gridded_haz in calc_gridded_hazard(
            location_grid_id,
            poe_levels,
            [HAZARD_MODEL_ID],
            vs30s,
            imts[:2],
            aggs[:2],
            [loc.resample(grid.resolution) for loc in locations],
        ):
            # gridded_haz.save()
            # time.sleep(0.05)
            # batch.save(gridded_haz)
            gridded_haz.save()
            saved += 1

        assert saved == 8

        # test we can retrieve something
        count = 0
        poes = 0
        for ghaz in model.get_gridded_hazard([HAZARD_MODEL_ID], [location_grid_id], vs30s, imts, aggs, poe_levels):
            poes += len(list(filter(lambda x: x is not None, ghaz.grid_poes)))
            count += 1

        print('table scan produced %s gridded_hazard rows and %s poe levels' % (count, poes))
        self.assertEqual(count, 8)  # 2 aggs * 2 imts * 2 poes
        self.assertEqual(poes, 40)  # 2 aggs * 2 imts * 2 poes * 5 sites
