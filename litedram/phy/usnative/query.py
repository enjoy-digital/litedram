#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""Run Vivado device queries with optional, validated local-only caching."""

import os
import re
import json
import shutil
import hashlib
import tempfile
import subprocess

from pathlib import Path

from .topology import vivado_query, parse_vivado_map
from .auxiliary import vivado_auxiliary_query, parse_auxiliary_map


def tcl_path(path):
    value = Path(path).resolve().as_posix()
    if any(c in value for c in '{}\n\r'):
        raise ValueError('Path cannot be represented safely as a Tcl literal')
    return '{' + value + '}'


_CACHE_SCHEMA  = 1
_QUERY_SOURCES = ('query.py', 'pins.py', 'topology.py', 'auxiliary.py')


def _cache_identity(pin_map, executable, timeout):
    # Ask the selected installation each time: its device database is not
    # interchangeable with another Vivado release, even at the same path.
    result = subprocess.run([executable, '-version'], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    version = result.stdout.decode('utf-8', errors='replace').strip()
    # Some Windows Vivado launchers return 1 for a successful -version. Only
    # accept that observed launcher behavior with the complete version/build
    # banner, never with an error message or arbitrary nonempty output.
    complete = (re.search(r'(?im)^\s*(?:\*+\s*)?Vivado v[0-9]{4}\.[0-9]+', version)
        and re.search(r'(?m)^\s*(?:\*+\s*)?SW Build [0-9]+', version)
        and not re.search(r'(?im)^\s*(?:error|fatal)\b', version))
    if result.returncode not in (0, 1) or not complete:
        raise RuntimeError('Vivado version query failed or returned no complete identity')
    tool = Path(executable).resolve()
    stat = tool.stat()
    return dict(schema=_CACHE_SCHEMA, part=pin_map.part, family=pin_map.family,
        pin_fingerprint=pin_map.fingerprint, executable=str(tool),
        executable_size=stat.st_size, executable_mtime_ns=stat.st_mtime_ns,
        tool_version=version, inputs={name: hashlib.sha256(
            Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in _QUERY_SOURCES})


def _read_cache(pin_map, directory, identity):
    try:
        provenance = json.loads((directory / 'provenance.json').read_text())
        if provenance['cache_identity'] != identity:
            return None
        for name in ('physical.tsv', 'auxiliary.tsv', 'version.txt'):
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != provenance['files'][name]:
                return None
        version = (directory / 'version.txt').read_text().strip()
        if not version or provenance['vivado_version'] != version:
            return None
        sites = parse_vivado_map(pin_map, (directory / 'physical.tsv').read_text(),
            vivado_version=version)
        aux = parse_auxiliary_map(pin_map, sites, (directory / 'auxiliary.tsv').read_text(),
            vivado_version=version)
        return sites, aux, directory
    except (OSError, ValueError, KeyError, TypeError):
        # Incomplete, corrupt or obsolete entries must trigger a fresh query.
        return None


def _publish_cache(directory, cache_root, key, identity):
    # An immutable entry is visible only after every file and its manifest have
    # been written. Unique suffixes avoid replacing another process's entry.
    staging = Path(tempfile.mkdtemp(prefix='.incomplete-', dir=cache_root))
    try:
        for name in ('physical.tsv', 'auxiliary.tsv', 'version.txt', 'provenance.json'):
            shutil.copyfile(directory / name, staging / name)
        provenance = json.loads((staging / 'provenance.json').read_text())
        provenance['cache_identity'] = identity
        provenance['files']['version.txt'] = hashlib.sha256((staging / 'version.txt').read_bytes()).hexdigest()
        (staging / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
        os.replace(staging, cache_root / (key + '-' + staging.name.removeprefix('.incomplete-')))
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def query_device(pin_map, output_dir, *, vivado='vivado', timeout=600,
                 cache_dir=None, force_refresh=False):
    """Return validated physical and auxiliary maps and their local directory.

    By default every call queries Vivado afresh. An explicit ``cache_dir`` allows
    reuse only for an identical part, pin map, tool and query implementation.
    ``force_refresh`` bypasses cache reads and records a new validated entry.
    Query results and logs are build artifacts, never source-controlled inputs.
    Failed queries leave logs for diagnosis and never fall back to stale data.
    """
    executable = shutil.which(str(vivado))
    if executable is None:
        raise OSError(f'Vivado executable not found: {vivado}')
    # Validate embedded Tcl tokens even when a matching cache entry exists.
    vivado_query(pin_map)
    identity = cache_root = key = None
    if cache_dir is not None:
        identity   = _cache_identity(pin_map, executable, timeout)
        key        = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        cache_root = Path(cache_dir).resolve()
        cache_root.mkdir(parents=True, exist_ok=True)
        # Never hide source files if a caller accidentally selects a checkout
        # or another occupied directory as the cache root.
        for child in cache_root.iterdir():
            if child.name == '.gitignore':
                continue
            if child.is_dir() and re.fullmatch(r'(?:[0-9a-f]{64}-|\.incomplete-)[A-Za-z0-9_-]+', child.name):
                continue
            raise ValueError(f'Cache directory contains non-cache content: {child}')
        # This local guard also protects caches placed inside a checkout.
        ignore   = cache_root / '.gitignore'
        existing = ignore.read_text() if ignore.exists() else ''
        if '*' not in existing.splitlines():
            with ignore.open('a') as stream:
                stream.write(('\n' if existing and not existing.endswith('\n') else '') + '*\n')
        if not force_refresh:
            for entry in sorted(cache_root.glob(key + '-*'), reverse=True):
                cached = _read_cache(pin_map, entry, identity)
                if cached is not None:
                    return cached
    parent = Path(output_dir).resolve()
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='usnative-query-', dir=parent))
    stub      = directory / 'query_top.v'
    stub.write_text('module query_top(input a, output b); assign b = a; endmodule\n')
    version_file = directory / 'version.txt'
    prefix = (f'create_project -in_memory -part {pin_map.part}\n'
              f'read_verilog {tcl_path(stub)}\n'
              f'synth_design -top query_top -part {pin_map.part}\n'
              f'set vf [open {tcl_path(version_file)} w]\n'
              'puts $vf [version -short]\nclose $vf\n')

    def run(name, body):
        script = directory / (name + '.tcl')
        script.write_text(prefix + body + '\nclose_design\n')
        log = directory / (name + '_console.log')
        with log.open('wb') as stream:
            result = subprocess.run([executable, '-mode', 'batch', '-source', str(script),
                '-log', str(directory / (name + '.log')),
                '-journal', str(directory / (name + '.jou'))],
                cwd=directory, stdin=subprocess.DEVNULL, stdout=stream,
                stderr=subprocess.STDOUT, timeout=timeout)
        if result.returncode:
            raise RuntimeError(f'Vivado native query failed: {log}')

    physical = directory / 'physical.tsv'
    run('physical', vivado_query(pin_map) + '\nusnative_query ' + tcl_path(physical))
    version   = version_file.read_text().strip()
    sites     = parse_vivado_map(pin_map, physical.read_text(), vivado_version=version)
    auxiliary = directory / 'auxiliary.tsv'
    run('auxiliary', vivado_auxiliary_query(pin_map, sites) +
        '\nusnative_auxiliary_query ' + tcl_path(auxiliary))
    if version_file.read_text().strip() != version:
        raise RuntimeError('Vivado version changed during native query')
    aux = parse_auxiliary_map(pin_map, sites, auxiliary.read_text(), vivado_version=version)
    provenance = dict(part=pin_map.part, pin_fingerprint=pin_map.fingerprint,
        vivado_version=version, executable=executable, fresh_device_queries=True,
        files={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (physical, auxiliary)})
    (directory / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    if cache_root is not None:
        _publish_cache(directory, cache_root, key, identity)
    return sites, aux, directory
