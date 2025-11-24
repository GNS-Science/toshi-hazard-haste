# coding: utf-8

import itertools
import logging
import multiprocessing
from collections import namedtuple
from typing import Iterable, List, Optional

import numpy as np
from nzshm_common.grids import RegionGrid
from nzshm_common.location import CodedLocation
from toshi_hazard_store import model, query_v3

from .gridded_poe import compute_hazard_at_poe

log = logging.getLogger(__name__)
INVESTIGATION_TIME = 50
SPOOF_SAVE = False
COV_AGG_KEY = 'cov'

GridHazTaskArgs = namedtuple("GridHazTaskArgs", "location_keys poe_lvl location_grid_id hazard_model_id vs30 imt agg")


def process_gridded_hazard(location_keys, poe_lvl, location_grid_id, hazard_model_id, vs30, imt, agg):
    grid_accel_levels: List = [None for i in range(len(location_keys))]
    for haz in query_v3.get_hazard_curves(location_keys, [vs30], [hazard_model_id], imts=[imt], aggs=[agg]):
        accel_levels = [val.lvl for val in haz.values]
        poe_values = [val.val for val in haz.values]
        index = location_keys.index(haz.nloc_001)
        try:
            grid_accel_levels[index] = compute_hazard_at_poe(poe_lvl, accel_levels, poe_values, INVESTIGATION_TIME)
        except ValueError as err:
            log.warning(
                'Error in compute_hazard_at_poe: %s, poe_lvl %s, haz_mod %s, vs30 %s, imt %s, agg %s'
                % (err, poe_lvl, hazard_model_id, vs30, imt, agg)
            )
            continue
        log.debug('replaced %s with %s' % (index, grid_accel_levels[index]))

    if agg == 'mean':
        grid_covs: List = [None for i in range(len(location_keys))]
        for cov in query_v3.get_hazard_curves(location_keys, [vs30], [hazard_model_id], imts=[imt], aggs=[COV_AGG_KEY]):
            # cov_accel_levels = [val.lvl for val in cov.values]
            cov_values = [val.val for val in cov.values]
            index = location_keys.index(cov.nloc_001)
            grid_covs[index] = np.exp(
                np.interp(np.log(grid_accel_levels[index]), np.log(accel_levels), np.log(cov_values))
            )

        yield model.GriddedHazard.new_model(
            hazard_model_id=hazard_model_id,
            location_grid_id=location_grid_id,
            vs30=vs30,
            imt=imt,
            agg=COV_AGG_KEY,
            poe=poe_lvl,
            grid_poes=grid_covs,
        )

    yield model.GriddedHazard.new_model(
        hazard_model_id=hazard_model_id,
        location_grid_id=location_grid_id,
        vs30=vs30,
        imt=imt,
        agg=agg,
        poe=poe_lvl,
        grid_poes=grid_accel_levels,
    )


class GriddedHAzardWorkerMP(multiprocessing.Process):
    """A worker that batches and saves records to DynamoDB."""

    def __init__(self, task_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue

    def run(self):
        log.info("worker %s running." % self.name)
        proc_name = self.name

        while True:
            nt = self.task_queue.get()
            if nt is None:
                # Poison pill means shutdown
                self.task_queue.task_done()
                log.info('%s: Exiting' % proc_name)
                break

            with model.GriddedHazard.batch_write() as batch:
                for ghaz in process_gridded_hazard(*nt):
                    if SPOOF_SAVE is False:
                        batch.save(ghaz)
                        print('save', ghaz)

            self.task_queue.task_done()
            log.info('%s task done.' % self.name)


def calc_gridded_hazard(
    location_grid_id: str,
    poe_levels: Iterable[float],
    hazard_model_ids: Iterable[str],
    vs30s: Iterable[float],
    imts: Iterable[str],
    aggs: Iterable[str],
    num_workers: int,
    filter_locations: Optional[Iterable[CodedLocation]] = None,
):

    log.debug(
        'calc_gridded_hazard( grid: %s poes: %s models: %s vs30s: %s imts: %s aggs: %s'
        % (location_grid_id, poe_levels, hazard_model_ids, vs30s, imts, aggs)
    )
    count = 0
    grid = RegionGrid[location_grid_id]

    # print(grid.resolution)
    locations = list(
        map(lambda grd_loc: CodedLocation(grd_loc[0], grd_loc[1], resolution=grid.resolution), grid.load())
    )

    if filter_locations:
        locations = list(set(locations).intersection(set(filter_locations)))

    location_keys = [loc.resample(0.001).code for loc in locations]

    log.debug('location_keys: %s' % location_keys)

    task_queue: multiprocessing.JoinableQueue = multiprocessing.JoinableQueue()

    log.debug('Creating %d workers' % num_workers)
    workers = [GriddedHAzardWorkerMP(task_queue) for i in range(num_workers)]
    for w in workers:
        w.start()

    for poe_lvl, hazard_model_id, vs30, imt, agg in itertools.product(poe_levels, hazard_model_ids, vs30s, imts, aggs):

        t = GridHazTaskArgs(location_keys, poe_lvl, location_grid_id, hazard_model_id, vs30, imt, agg)
        task_queue.put(t)
        count += 1

    # Add a poison pill for each to signal we've done everything
    for i in range(num_workers):
        task_queue.put(None)

    # Wait for all of the tasks to finish
    task_queue.join()

    log.info('calc_gridded_hazard() produced %s gridded_hazard rows ' % count)
