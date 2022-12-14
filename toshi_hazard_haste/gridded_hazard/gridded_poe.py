"""Calculate hazard at a given probablity of exceedance level from a hazard curve."""

# import json
# from itertools import product
from typing import Iterable  # Any, Iterator, List, Tuple

import numpy as np

# import pandas as pd


def compute_hazard_at_poe(
    poe: float, ground_accels: Iterable[float], annual_poes: Iterable[float], investigation_time: int
) -> float:
    """Compute hazard at given poe using numpy.interpolate().

    see https://numpy.org/doc/stable/reference/generated/numpy.interp.html?highlight=interp
    """
    return_period = -investigation_time / np.log(1 - poe)

    xp = np.flip(np.log(annual_poes))  # type: ignore
    yp = np.flip(np.log(ground_accels))  # type: ignore

    assert np.all(np.diff(xp) >= 0)  # raise is x_accel_levels not increasing or at least not dropping,

    return np.exp(np.interp(np.log(1 / return_period), xp, yp))  # type: ignore


# def enumerated_product(*args: List[Any]) -> Iterator[Tuple[Tuple[Any, ...], Any]]:
#     """Get an enumeration over an arbitrary number of lists.

#     https://stackoverflow.com/a/56430867
#     """
#     yield from zip(product(*(range(len(x)) for x in args)), product(*args))  # type: ignore


# if __name__ == '__main__':

#     slt_df = pd.read_csv('SCRATCH/slt_tag_final.grid-NZ_0_1_NB_1_0.csv')
#     accel_levels = [float(col[4:]) for col in filter(lambda x: x.startswith('poe-'), list(slt_df.columns))]

#     site_count = 3618

#     investigation_time = 1
#     COMPRESS = False

#     imts = ["PGA", "SA(0.5)", "SA(1.5)"]
#     aggs = ["mean", "0.995"]  # "0.005", "0.1", "0.2", "0.5", "0.8", "0.9", "0.995"]
#     vs30s = [400]
#     poes = [0.1]  # 0.02]

#     result = dict(imts=imts, aggs=aggs, vs30s=vs30s, poes=poes, grid_data='numpy.ndarray.tolist')

#     results_array: np.ndarray = np.ndarray((site_count, len(imts), len(aggs), len(vs30s), len(poes)), np.float64)

#     for idx, keys in enumerated_product(imts, aggs, vs30s, poes):
#         """eg idx, keys: (0, 0, 0, 0) ('PGA', 'mean', 400, 0.02)"""
#         flat_array = []

#         imt, agg, vs30, poe = keys
#         filtered_df = slt_df[(slt_df['imt'] == imt) & (slt_df['agg'] == agg) & (slt_df['vs30'] == vs30)]
#         site_idx = 0
#         for index, row in filtered_df.iterrows():
#             # print(index, *row[:5], compute_hazard_at_poe(levels, row.tolist()[5:], poe, investigation_time))
#             try:
#                 poe_values = row.tolist()[5:]
#                 computed_acceleration_at_poe = compute_hazard_at_poe(poe, accel_levels,
#                     poe_values, investigation_time)
#             except AssertionError:
#                 print("ASSERT", row)
#                 raise

#             results_array[site_idx, idx] = computed_acceleration_at_poe
#             flat_array.append(computed_acceleration_at_poe)
#             site_idx += 1

#         print(imt, agg, vs30, poe, filtered_df.shape)
#         print(f'{imt} max of {agg} accel (g): {max(flat_array)}')
#         print(f'{imt} min of {agg} accel (g): {min(flat_array)}')
#         print(f'{imt} avg of {agg} accel (g): {sum(flat_array)/len(flat_array)}')
#         print()

#     # if COMPRESS:
#     #     result['poes'] = compress_string(json.dumps(flat_array))  # results_array.tolist()
#     # else:
#     #     result['poes'] = flat_array
#     # json.dump(result, open('SCRATCH/slt_tag_final.grid-NZ_0_1_NB_1_0.poe-lzma.json', 'w'))
#     print('DONE')
