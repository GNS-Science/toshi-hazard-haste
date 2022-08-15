# coding: utf-8

import itertools
import logging
from typing import Iterable, Iterator, List

from nzshm_common.grids import RegionGrid
from nzshm_common.location import CodedLocation
from toshi_hazard_store import query_v3

from toshi_hazard_haste import model

from .gridded_poe import compute_hazard_at_poe

log = logging.getLogger(__name__)
INVESTIGATION_TIME = 50


def calc_gridded_hazard(
    location_grid_id: str,
    poe_levels: Iterable[float],
    hazard_model_ids: Iterable[str],
    vs30s: Iterable[float],
    imts: Iterable[str],
    aggs: Iterable[str],
    filter_locations: Iterable[CodedLocation] = None,
) -> Iterator[model.GriddedHazard]:

    log.debug(
        'calc_gridded_hazard( grid: %s poes: %s models: %s vs30s: %s imts: %s aggs: %s'
        % (location_grid_id, poe_levels, hazard_model_ids, vs30s, imts, aggs)
    )
    count = 0
    grid = RegionGrid[location_grid_id]

    print(grid.resolution)
    locations = list(
        map(lambda grd_loc: CodedLocation(grd_loc[0], grd_loc[1], resolution=grid.resolution), grid.load())
    )

    if filter_locations:
        locations = list(set(locations).intersection(set(filter_locations)))

    location_keys = [loc.resample(0.001).code for loc in locations]

    log.debug('location_keys: %s' % location_keys)

    for (poe_lvl, hazard_model_id, vs30, imt, agg) in itertools.product(
        poe_levels, hazard_model_ids, vs30s, imts, aggs
    ):
        grid_poes: List = [None for i in range(len(locations))]
        for haz in query_v3.get_hazard_curves(location_keys, [vs30], [hazard_model_id], imts=[imt], aggs=[agg]):
            accel_levels = [val.lvl for val in haz.values]
            poe_values = [val.val for val in haz.values]
            index = location_keys.index(haz.nloc_001)
            grid_poes[index] = compute_hazard_at_poe(poe_lvl, accel_levels, poe_values, INVESTIGATION_TIME)
            log.debug('replaced %s with %s' % (index, grid_poes[index]))

        yield model.GriddedHazard.new_model(
            hazard_model_id=hazard_model_id,
            location_grid_id=location_grid_id,
            vs30=vs30,
            imt=imt,
            agg=agg,
            poe=poe_lvl,
            grid_poes=grid_poes,
        )
        log.debug(
            'calc_gridded_hazard() produced model with %s poes ' % len(list(filter(lambda x: x is not None, grid_poes)))
        )
        count += 1

    log.info('calc_gridded_hazard() produced %s gridded_hazard rows ' % count)
