# -*- coding: utf-8 -*-
"""Build standard APT indexes from debs/.

A plain repository build: scan debs, add missing Icon fields, write Packages,
compress it and regenerate the Release checksums. No application-specific
metadata or overrides are involved.

Run by .github/workflows/release.yml and .github/workflows/deploy-pages.yml.
"""
import hashlib
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE_URL = 'https://ynyy0.github.io/repoconsole-test/'
ICON_BASE = BASE_URL + 'icons/'
DEFAULT_ICON = BASE_URL + 'CydiaIcon.png'
INDEX_FILES = ('Packages', 'Packages.bz2', 'Packages.xz', 'Packages.zst')
NL = '\n'


def scan_packages():
    """dpkg-scanpackages with a fixed UTF-8 locale (its output carries raw
    control-field bytes, which must not depend on the runner's LANG)."""
    env = dict(os.environ, LC_ALL='C.UTF-8', LANG='C.UTF-8')
    result = subprocess.run(
        ['dpkg-scanpackages', '-m', 'debs', '/dev/null'],
        cwd=ROOT, capture_output=True, check=False, env=env,
        encoding='utf-8', errors='replace',
    )
    if result.returncode != 0:
        print('dpkg-scanpackages reported issues (bad debs are skipped):')
        print(result.stderr.strip()[:2000])
    if '\ufffd' in result.stdout:
        for line in result.stdout.splitlines():
            if '\ufffd' in line:
                print('WARN: non-UTF-8 byte in dpkg output:', line.strip()[:120])
    return result.stdout


def add_icons(stdout):
    """Fill in Icon: for stanzas whose deb control does not provide one."""
    stanzas = [s for s in stdout.rstrip(NL).split(NL + NL) if s.strip()]
    out = []
    for stanza in stanzas:
        lines = stanza.splitlines()
        fields = {}
        for line in lines:
            if ': ' in line:
                key, value = line.split(': ', 1)
                fields[key] = value
        if 'Icon:' not in fields:
            package = fields.get('Package', '')
            candidate = ROOT / 'icons' / (package + '.png')
            if not candidate.is_file() and package:
                matches = [p for p in (ROOT / 'icons').glob('*.png')
                           if p.stem.lower() == package.lower()]
                candidate = matches[0] if matches else candidate
            url = ICON_BASE + candidate.name if candidate.is_file() else DEFAULT_ICON
            lines.append('Icon: ' + url)
        out.append(NL.join(lines))
    return (NL + NL).join(out) + NL


def compress():
    """Create the three compressed indexes. Tooling is available on runners;
    missing tools only mean that variant is skipped (Release lists what exists)."""
    plain = (ROOT / 'Packages').read_bytes()
    (ROOT / 'Packages.bz2').write_bytes(__import__('bz2').compress(plain, 9))
    (ROOT / 'Packages.xz').write_bytes(__import__('lzma').compress(
        plain, format=__import__('lzma').FORMAT_XZ, preset=9))
    try:
        subprocess.run(
            ['zstd', '--ultra', '-22', '-q', '-f', '-o', 'Packages.zst', 'Packages'],
            cwd=ROOT, check=True, capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        print('WARN: zstd unavailable, Packages.zst not refreshed')


def write_release():
    """Keep the Release header as written by the repo owner, recompute checksums."""
    release_file = ROOT / 'Release'
    header = []
    if release_file.is_file():
        for line in release_file.read_text(encoding='utf-8').splitlines():
            if line.rstrip() in ('MD5Sum:', 'SHA1:', 'SHA256:'):
                break
            header.append(line)
    header = [line for line in header if line.strip()]

    def section(title, algo):
        rows = [title + ':']
        for name in INDEX_FILES:
            f = ROOT / name
            if f.is_file():
                rows.append(' %s %d %s' % (
                    hashlib.new(algo, f.read_bytes()).hexdigest(), f.stat().st_size, name))
        return rows

    text = (NL.join(header) + NL + NL
            + NL.join(section('MD5Sum', 'md5')) + NL + NL
            + NL.join(section('SHA1', 'sha1')) + NL + NL
            + NL.join(section('SHA256', 'sha256')) + NL)
    release_file.write_text(text, encoding='utf-8')


def main():
    text = add_icons(scan_packages())
    (ROOT / 'Packages').write_text(text, encoding='utf-8')
    compress()
    write_release()
    print('Indexed %d packages' % len(re.findall(r'^Package: ', text, re.M)))


if __name__ == '__main__':
    main()
