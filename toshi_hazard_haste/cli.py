"""Console script for toshi_hazard_haste."""

import logging
import sys

import click
import toml
from nzshm_common.grids import RegionGrid

from toshi_hazard_haste.gridded_hazard import calc_gridded_hazard

log = logging.getLogger()
logging.basicConfig(level=logging.INFO)
logging.getLogger('nshm_toshi_client.toshi_client_base').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('botocore').setLevel(logging.INFO)
logging.getLogger('pynamodb').setLevel(logging.INFO)
logging.getLogger('toshi_hazard_post').setLevel(logging.DEBUG)
logging.getLogger('toshi_hazard_store').setLevel(logging.INFO)
logging.getLogger('gql.transport.requests').setLevel(logging.WARN)

formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)
log.addHandler(screen_handler)


@click.command()
@click.option('-H', '--hazard_model_ids', help='comma-delimted list of hazard model ids.')
@click.option('-L', '--site-lists', help='One or more site list ENUMs.')
@click.option('-I', '--imts', help='comma-delimited list of imts.')
@click.option('-A', '--aggs', help='comma-delimited list of aggs.')
@click.option('-V', '--vs30s', help='comma-delimited list of vs30s.')
@click.option('-c', '--config', type=click.Path(exists=True))  # help="path to a valid THU configuration file."
@click.option('-lsl', '--list-site-lists', help='print the list of sites list ENUMs and exit', is_flag=True)
@click.option('-v', '--verbose', is_flag=True)
@click.option('-D', '--dry-run', is_flag=True)
def cli_gridded_hazard(hazard_model_ids, site_lists, imts, aggs, vs30s, config, list_site_lists, verbose, dry_run):
    """Process gridded hazard for a given set of arguments."""

    if list_site_lists:
        click.echo("ENUM name\tDetails")
        click.echo("===============\t======================================================================")
        for rg in RegionGrid:
            click.echo(f"{rg.name}\t{rg.value}")
        return

    site_lists = site_lists.split(',') if site_lists else None

    hazard_model_ids = hazard_model_ids.split(',') if hazard_model_ids else None
    imts = imts.split(',') if imts else None
    vs30s = vs30s.split(',') if vs30s else None
    aggs = aggs.split(',') if aggs else None

    if config:
        conf = toml.load(config)
        if verbose:
            click.echo(f"using settings in {config} for export")

        site_lists = site_lists or conf.get('site_lists', [])
        hazard_model_ids = hazard_model_ids or conf.get('hazard_model_ids')
        imts = imts or conf.get('imts')
        vs30s = vs30s or conf.get('vs30s')
        aggs = aggs or conf.get('aggs')

    if verbose:
        click.echo(f"{hazard_model_ids} {imts} {vs30s}")

    if dry_run:
        click.echo(f"dry-run {hazard_model_ids} {imts} {vs30s}")
        return

    # haggs = query_v3.get_hazard_curves(locations, vs30s, hazard_model_ids, imts=imts, aggs=aggs)
    click.echo('Done!')


if __name__ == "__main__":
    cli_gridded_hazard()  # pragma: no cover
