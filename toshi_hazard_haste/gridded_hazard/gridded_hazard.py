# coding: utf-8

import itertools
from typing import Iterable, Iterator

from nzshm_common.grids import RegionGrid
from nzshm_common.location import CodedLocation
from toshi_hazard_store import query_v3

from toshi_hazard_haste import model

from .gridded_poe import compute_hazard_at_poe


def calc_gridded_hazard(
    location_grid_id: str,
    poe_levels: Iterable[float],
    hazard_model_ids: Iterable[str],
    vs30s: Iterable[float],
    imts: Iterable[str],
    aggs: Iterable[str],
) -> Iterator[model.GriddedHazard]:

    count = 0
    grid = RegionGrid[location_grid_id]
    grid_locs = grid.load()

    # build a dictionary of CodedLocations
    locations = {}
    for loc in list(map(lambda x: CodedLocation(x[0], x[1], resolution=0.001), grid_locs))[500:600]:
        locations[loc.code] = dict(loc=loc)
    location_keys = list(locations.keys())
    # print(location_keys)
    # assert 0

    for (poe_lvl, hazard_model_id, vs30, imt, agg) in itertools.product(
        poe_levels, hazard_model_ids, vs30s, imts, aggs
    ):
        grid_poes = [None for i in range(len(locations))]
        for haz in query_v3.get_hazard_curves(location_keys, [vs30], [hazard_model_id], imts=[imt], aggs=[agg]):
            accel_levels = [val.lvl for val in haz.values]
            poe_values = [val.val for val in haz.values]
            index = location_keys.index(haz.nloc_001)
            grid_poes[index] = compute_hazard_at_poe(poe_lvl, accel_levels, poe_values, 1)
            print('replaced', index, grid_poes[index])
            # assert 0

        yield model.GriddedHazard.new_model(
            hazard_model_id=hazard_model_id,
            location_grid_id=location_grid_id,
            vs30=vs30,
            imt=imt,
            agg=agg,
            poe=poe_lvl,
            grid_poes=grid_poes,
        )
        count += 1

    print('calc_gridded_hazard() produced %s gridded_hazard rows ' % count)
