"""Console script for toshi_hazard_haste."""

import logging
import sys

import click
import geopandas as gpd
import matplotlib as mpl
import matplotlib.cm
import matplotlib.colors
import toml
from nzshm_common.geometry.geometry import create_square_tile
from nzshm_common.grids import RegionGrid
from nzshm_common.location import CodedLocation
from toshi_hazard_store import model

from toshi_hazard_haste.gridded_hazard import calc_gridded_hazard

log = logging.getLogger()
logging.basicConfig(level=logging.INFO)
logging.getLogger('nshm_toshi_client.toshi_client_base').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('botocore').setLevel(logging.INFO)
logging.getLogger('pynamodb').setLevel(logging.INFO)
logging.getLogger('toshi_hazard_haste').setLevel(logging.INFO)
logging.getLogger('toshi_hazard_store').setLevel(logging.INFO)
logging.getLogger('gql.transport.requests').setLevel(logging.WARN)

formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)
log.addHandler(screen_handler)


@click.group()
def thh():
    pass


@thh.command(name='geojson')
@click.option('-H', '--hazard_model_ids', help='comma-delimted list of hazard model ids.')
@click.option('-L', '--site-list', help='A site list ENUM.')
@click.option('-I', '--imts', help='comma-delimited list of imts.')
@click.option('-A', '--aggs', help='comma-delimited list of aggs.')
@click.option('-V', '--vs30s', help='comma-delimited list of vs30s.')
@click.option('-P', '--poes', help='comma-delimited list of poe_levels.')
@click.option('-c', '--config', type=click.Path(exists=True))  # help="path to a valid THU configuration file."
def cli_geojson(hazard_model_ids, site_list, imts, aggs, vs30s, poes, config):
    """Query gridded hazard and build geojson."""

    hazard_model_ids = hazard_model_ids.split(',') if hazard_model_ids else None
    imts = imts.split(',') if imts else None
    vs30s = [float(v) for v in vs30s.split(',')] if vs30s else None
    aggs = aggs.split(',') if aggs else None
    poes = [float(v) for v in poes.split(',')] if poes else None

    if config:
        conf = toml.load(config)

        site_list = site_list or conf.get('site_list')
        hazard_model_ids = hazard_model_ids or conf.get('hazard_model_ids')
        imts = imts or conf.get('imts')
        vs30s = vs30s or conf.get('vs30s')
        aggs = aggs or conf.get('aggs')
        poes = poes or conf.get('poes')

    region_grid = RegionGrid[site_list]
    grid = region_grid.load()
    loc, geometry = [], []
    cmap = mpl.cm.get_cmap("jet")
    norm = mpl.colors.Normalize(vmin=0.0, vmax=3.0)

    for pt in grid:
        loc.append((pt[1], pt[0]))
        geometry.append(create_square_tile(region_grid.resolution, pt[1], pt[0]))

    def fix_nan(poes):
        for i in range(len(poes)):
            if poes[i] is None:
                log.debug('Nan at %s' % i)
                poes[i] = 0.0
        return poes

    count = 0
    poe_count = 0
    for ghaz in model.get_gridded_hazard(hazard_model_ids, [site_list], vs30s, imts, aggs, poes):
        poe_count += len(list(filter(lambda x: x is not None, ghaz.grid_poes)))
        count += 1
        poes = fix_nan(ghaz.grid_poes)
        color_values = [mpl.colors.to_hex(cmap(norm(v)), keep_alpha=True) for v in poes]
        gdf = gpd.GeoDataFrame(
            data=dict(
                loc=loc,
                geometry=geometry,
                value=ghaz.grid_poes,
                fill=color_values,
                stroke=color_values,
                fill_opacity=[0.75 for n in poes],
                stroke_width=[0.5 for n in poes],
                stroke_opacity=[0.75 for n in poes],
                # style = [{"color":"0x000FFF"} for v in ghaz.grid_poes],
            )
        )
        gdf = gdf.rename(
            columns={'fill_opacity': 'fill-opacity', 'stroke_width': 'stroke-width', 'stroke_opacity': 'stroke-opacity'}
        )
        with open(f'test_{count}.json', 'w') as output:
            output.write(gdf.to_json())

    click.echo('table scan produced %s gridded_hazard rows and %s poe levels' % (count, poe_count))


@thh.command(name='build')
@click.option('-H', '--hazard_model_ids', help='comma-delimted list of hazard model ids.')
@click.option('-L', '--site-list', help='A site list ENUM.')
@click.option('-I', '--imts', help='comma-delimited list of imts.')
@click.option('-A', '--aggs', help='comma-delimited list of aggs.')
@click.option('-V', '--vs30s', help='comma-delimited list of vs30s.')
@click.option('-P', '--poes', help='comma-delimited list of poe_levels.')
@click.option('-c', '--config', type=click.Path(exists=True))  # help="path to a valid THU configuration file."
@click.option('-lsl', '--list-site-lists', help='print the list of sites list ENUMs and exit', is_flag=True)
@click.option('-v', '--verbose', is_flag=True)
@click.option('-d', '--dry-run', is_flag=True)
@click.option('-m', '--migrate-tables', is_flag=True)
@click.option('-w', '--num-workers', default=4, show_default=True)
def cli_gridded_hazard(
    hazard_model_ids,
    site_list,
    imts,
    aggs,
    vs30s,
    poes,
    config,
    list_site_lists,
    verbose,
    dry_run,
    migrate_tables,
    num_workers,
):
    """Process gridded hazard for a given set of arguments."""

    if list_site_lists:
        click.echo("ENUM name\tDetails")
        click.echo("===============\t======================================================================")
        for rg in RegionGrid:
            click.echo(f"{rg.name}\t{rg.value}")
        return

    # site_lists = site_lists.split(',') if site_lists else None

    hazard_model_ids = hazard_model_ids.split(',') if hazard_model_ids else None
    vs30s = vs30s.split(',') if vs30s else None
    imts = imts.split(',') if imts else None
    aggs = aggs.split(',') if aggs else None
    poes = poes.split(',') if poes else None
    filter_sites = None

    if config:
        conf = toml.load(config)
        if verbose:
            click.echo(f"using settings in {config} for export")

        site_list = site_list or conf.get('site_list')
        hazard_model_ids = hazard_model_ids or conf.get('hazard_model_ids')
        imts = imts or conf.get('imts')
        vs30s = vs30s or conf.get('vs30s')
        aggs = aggs or conf.get('aggs')
        poes = poes or conf.get('poes')
        filter_sites = filter_sites or conf.get('filter_sites')

    if verbose:
        click.echo(f"{hazard_model_ids} {imts} {vs30s}")

    if dry_run:
        click.echo(f"dry-run {site_list} {hazard_model_ids} {imts} {vs30s}")
        return

    if migrate_tables:
        click.echo("Ensuring that dynamodb tables are available in target region & stage.")
        model.migrate()

    try:
        click.echo(filter_sites)
        filter_locations = (
            [CodedLocation(*[float(s) for s in site.split('~')], resolution=0.2) for site in filter_sites.split('')]
            if filter_sites
            else []
        )
        click.echo(filter_locations)
        calc_gridded_hazard(
            location_grid_id=site_list,
            poe_levels=poes,
            hazard_model_ids=hazard_model_ids,
            vs30s=vs30s,
            imts=imts,
            aggs=aggs,
            num_workers=num_workers,
            filter_locations=filter_locations,
        )
    except Exception as err:
        click.echo(err)
        raise click.UsageError('An error occurred, pls check usage.')

    # haggs = query_v3.get_hazard_curves(locations, vs30s, hazard_model_ids, imts=imts, aggs=aggs)
    click.echo('Done!')


if __name__ == "__main__":
    thh()  # pragma: no cover
