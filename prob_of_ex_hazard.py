# coding: utf-8
import pandas as pd
import numpy as np
import json

from itertools import product
from typing import Iterable, Iterator, Tuple, Any, List
from util import compress_config


def compute_hazard_at_poe(
    x_levels: Iterable[float], y_values: Iterable[float], poe: float, investigation_time: int
) -> float:
    """Compute hazard at given poe using numpy.interpolate().

    see https://numpy.org/doc/stable/reference/generated/numpy.interp.html?highlight=interp
    """
    rp = -investigation_time / np.log(1 - poe)
    xp = np.log(x_levels)  # type: ignore
    yp = np.flip(np.log(y_values))  # type: ignore

    assert np.all(np.diff(xp) >= 0)  # raise is xp is not increasing or at least not dropping,

    return np.exp(np.interp(np.log(1 / rp), xp, yp))  # type: ignore


def enumerated_product(*args: List[Any]) -> Iterator[Tuple[Tuple[Any, ...], Any]]:
    """Get a enumeration over an arbitrary number of lists.

    https://stackoverflow.com/a/56430867
    """
    yield from zip(product(*(range(len(x)) for x in args)), product(*args))  # type: ignore


if __name__ == '__main__':

    slt_df = pd.read_csv('SCRATCH/slt_tag_final.grid-NZ_0_1_NB_1_0.csv')
    levels = [float(col[4:]) for col in filter(lambda x: x.startswith('poe-'), list(slt_df.columns))]

    site_count = 3618

    investigation_time = 1

    imts = [
        "PGA",
    ]  # "SA(0.5)", "SA(1.5)" ]
    aggs = [
        "mean",
    ]  # "0.005", "0.1", "0.2", "0.5", "0.8", "0.9", "0.995"]
    vs30s = [400]
    poes = [
        0.10,
    ]  # 0.02]

    result = dict(imts=imts, aggs=aggs, vs30s=vs30s, poes=poes, grid_data='numpy.ndarray.tolist')

    results_array: np.ndarray = np.ndarray((site_count, len(imts), len(aggs), len(vs30s), len(poes)), np.float64)

    flat_array = []
    for idx, keys in enumerated_product(imts, aggs, vs30s, poes):
        """eg idx, keys: (0, 0, 0, 0) ('PGA', 'mean', 400, 0.02)"""

        imt, agg, vs30, poe = keys
        filtered_df = slt_df[(slt_df['imt'] == imt) & (slt_df['agg'] == agg) & (slt_df['vs30'] == vs30)]
        print(imt, agg, vs30, poe, filtered_df.shape)
        site_idx = 0
        for index, row in filtered_df.iterrows():
            # print(index, *row[:5], compute_hazard_at_poe(levels, row.tolist()[5:], poe, investigation_time))
            try:
                haz_at_poe = compute_hazard_at_poe(levels, row.tolist()[5:], poe, investigation_time)
            except AssertionError:
                print("ASSERT", row)
                raise

            results_array[site_idx, idx] = haz_at_poe
            flat_array.append(haz_at_poe)
            site_idx += 1

    result['poes'] = compress_config(json.dumps(flat_array))  # results_array.tolist()

    json.dump(result, open('SCRATCH/slt_tag_final.grid-NZ_0_1_NB_1_0.poe-lzma.json', 'w'))
    print('DONE')
