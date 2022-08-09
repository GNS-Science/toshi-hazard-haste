"""Useful utility & helpers."""
import base64
import io
import zipfile
from pathlib import Path, PurePath
from typing import Union


def archive(source_path: str, output_zip: Union[str, PurePath]) -> str:
    """Zip contents of source path and return the full archive path.

    Handles both single file and a folder.
    """
    with zipfile.ZipFile(output_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zip:
        if Path(source_path).is_file():
            zip.write(source_path, PurePath(source_path).name)
        else:
            for filename in Path(source_path).rglob('*'):
                zip.write(filename, arcname=str(Path(filename).relative_to(source_path)))
    return str(output_zip)


def compress_config(config: str) -> str:
    """Use LZMA compression to pack this config into a much smaller string."""
    compressed = io.BytesIO()
    with zipfile.ZipFile(compressed, 'w', compression=zipfile.ZIP_LZMA) as zf:
        zf.writestr('0', config)
        zf.close()
    compressed.seek(0)
    b64 = base64.b64encode(compressed.read())
    return b64.decode('ascii')


def decompress_config(compressed: str) -> str:
    """Decompress an LZMA compressed config."""
    base64_bytes = compressed.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)

    ## Decompression
    zfout = zipfile.ZipFile(io.BytesIO(message_bytes))
    msg_out = io.BytesIO(zfout.read('0'))
    msg_out.seek(0)
    return msg_out.read().decode('ascii')
