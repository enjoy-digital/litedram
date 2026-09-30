#
# This file is part of LiteDRAM.
#
# SPDX-License-Identifier: BSD-2-Clause

"""External query failures must not fall back to stale local connectivity."""

import json
import hashlib
import tempfile
import unittest

from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from litedram.phy.usnative.query import query_device, tcl_path, _cache_identity
from test.test_usnative_topology import topology_fixture, encode
from test.test_usnative_auxiliary import fixture as auxiliary_fixture


class TestUSNativeQuery(unittest.TestCase):
    def test_missing_tool_fails_before_creating_output(self):
        pins, _ = topology_fixture()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'new'
            with patch('litedram.phy.usnative.query.shutil.which', return_value=None):
                with self.assertRaises(OSError):
                    query_device(pins, output)
            self.assertFalse(output.exists())

    def test_failed_query_never_reads_stale_map(self):
        pins, _ = topology_fixture()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            stale = output / 'physical.tsv'
            stale.write_text('stale device data')
            with patch('litedram.phy.usnative.query.shutil.which', return_value='vivado'), \
                 patch('litedram.phy.usnative.query.subprocess.run',
                       return_value=SimpleNamespace(returncode=1)) as run:
                for _ in range(2):
                    with self.assertRaisesRegex(RuntimeError, 'query failed'):
                        query_device(pins, output)
                self.assertEqual(run.call_count, 2)
            self.assertEqual(stale.read_text(), 'stale device data')
            self.assertEqual(len(list(output.glob('usnative-query-*'))), 2)

    def test_tcl_path_rejects_delimiter_injection(self):
        for value in ('query{bad}', 'query\nexit'):
            with self.assertRaises(ValueError):
                tcl_path(value)


class TestUSNativeQueryCache(unittest.TestCase):
    # Fixtures are deliberately synthetic; no queried device data is committed.
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.tool = self.root / 'vivado'
        self.tool.write_text('synthetic executable identity')
        self.pins, rows = topology_fixture()
        self.physical = encode(self.pins, rows)
        _, _, self.auxiliary = auxiliary_fixture()
        self.cache = self.root / 'cache'
        self.output = self.root / 'build'
        self.version = '2026.1'
        self.queries = 0
        self.fail = False
        which = patch('litedram.phy.usnative.query.shutil.which', return_value=str(self.tool))
        runner = patch('litedram.phy.usnative.query.subprocess.run', side_effect=self.run_tool)
        which.start()
        runner.start()
        self.addCleanup(which.stop)
        self.addCleanup(runner.stop)

    def run_tool(self, command, **kwargs):
        if '-version' in command:
            return SimpleNamespace(returncode=0, stdout=('Vivado v' + self.version + '\nSW Build 6299465').encode())
        self.queries += 1
        if self.fail:
            return SimpleNamespace(returncode=1)
        directory = kwargs['cwd']
        script = Path(command[command.index('-source') + 1]).stem
        (directory / 'version.txt').write_text(self.version)
        text = self.physical if script == 'physical' else self.auxiliary
        (directory / (script + '.tsv')).write_text(text.replace('2026.1', self.version))
        return SimpleNamespace(returncode=0)

    def query(self, **kwargs):
        return query_device(self.pins, self.output, cache_dir=self.cache, **kwargs)

    def test_validated_hit_and_force_refresh(self):
        sites, aux, fresh = self.query()
        cached_sites, cached_aux, cached = self.query()
        self.assertEqual((sites, aux), (cached_sites, cached_aux))
        self.assertNotEqual(fresh, cached)
        self.assertEqual(self.queries, 2)
        self.assertEqual((self.cache / '.gitignore').read_text(), '*\n')
        self.query(force_refresh=True)
        self.assertEqual(self.queries, 4)
        self.assertFalse(list(self.cache.glob('.incomplete-*')))

    def test_default_remains_fresh(self):
        for _ in range(2):
            query_device(self.pins, self.output)
        self.assertEqual(self.queries, 4)
        self.assertFalse(self.cache.exists())

    def test_tool_version_and_executable_identity_invalidate(self):
        self.query()
        self.version = '2025.2'
        self.query()
        self.assertEqual(self.queries, 4)
        self.tool.write_text('updated executable identity and size')
        self.query()
        self.assertEqual(self.queries, 6)

    def test_query_schema_invalidates(self):
        self.query()
        with patch('litedram.phy.usnative.query._CACHE_SCHEMA', 2):
            self.query()
        self.assertEqual(self.queries, 4)

    def test_corrupt_or_missing_payload_requeries(self):
        for filename in ('physical.tsv', 'auxiliary.tsv', 'provenance.json', 'version.txt'):
            with self.subTest(filename=filename):
                self.query(force_refresh=True)
                for entry in self.cache.iterdir():
                    if entry.is_dir():
                        (entry / filename).write_text('broken')
                before = self.queries
                self.query()
                self.assertEqual(self.queries, before + 2)

    def test_semantically_invalid_payload_rejected_even_with_matching_hash(self):
        self.query()
        entry = next(p for p in self.cache.iterdir() if p.is_dir())
        payload = entry / 'physical.tsv'
        payload.write_text(self.physical.replace('END\t', 'INCOMPLETE\t'))
        manifest = entry / 'provenance.json'
        data = json.loads(manifest.read_text())
        data['files']['physical.tsv'] = hashlib.sha256(payload.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(data))
        self.query()
        self.assertEqual(self.queries, 4)

    def test_failed_force_refresh_does_not_fall_back(self):
        self.query()
        self.fail = True
        with self.assertRaisesRegex(RuntimeError, 'query failed'):
            self.query(force_refresh=True)
        self.assertEqual(len([p for p in self.cache.iterdir() if p.is_dir()]), 1)

    def test_incomplete_entries_are_not_reused(self):
        self.query()
        entry = next(p for p in self.cache.iterdir() if p.is_dir())
        entry.rename(self.cache / '.incomplete-interrupted')
        self.query()
        self.assertEqual(self.queries, 4)

    def test_pin_part_family_identity_is_keyed(self):
        original = _cache_identity(self.pins, str(self.tool), 600)
        for field in ('part', 'family', 'fingerprint'):
            pins = SimpleNamespace(part=self.pins.part, family=self.pins.family,
                fingerprint=self.pins.fingerprint)
            setattr(pins, field, 'different')
            self.assertNotEqual(original, _cache_identity(pins, str(self.tool), 600))

    def test_query_input_identity_invalidates(self):
        self.query()
        with patch('litedram.phy.usnative.query._QUERY_SOURCES', ('query.py',)):
            self.query()
        self.assertEqual(self.queries, 4)

    def test_existing_local_ignore_is_preserved(self):
        self.cache.mkdir()
        ignore = self.cache / '.gitignore'
        ignore.write_text('# local cache policy')
        self.query()
        self.assertEqual(ignore.read_text(), '# local cache policy\n*\n')

    def test_windows_version_launcher_exit_one_requires_complete_banner(self):
        from litedram.phy.usnative.query import _cache_identity
        with patch('litedram.phy.usnative.query.subprocess.run', return_value=SimpleNamespace(
                returncode=1, stdout=b'vivado v2025.2 (64-bit)\nSW Build 6299465')):
            self.assertIn('2025.2', _cache_identity(self.pins, str(self.tool), 600)['tool_version'])
        for output in (b'', b'Vivado v2025.2', b'failed to launch',
                       b'Vivado v2025.2\nSW Build 6299465\nERROR: device unavailable'):
            with patch('litedram.phy.usnative.query.subprocess.run', return_value=SimpleNamespace(
                    returncode=1, stdout=output)):
                with self.assertRaisesRegex(RuntimeError, 'version query'):
                    _cache_identity(self.pins, str(self.tool), 600)

    def test_cache_root_cannot_hide_source_or_repository(self):
        self.cache.mkdir()
        for name in ('.git', 'source.py'):
            source = self.cache / name
            source.write_text('must remain visible')
            with self.assertRaisesRegex(ValueError, 'non-cache content'):
                self.query()
            self.assertFalse((self.cache / '.gitignore').exists())
            self.assertEqual(source.read_text(), 'must remain visible')
            source.unlink()
