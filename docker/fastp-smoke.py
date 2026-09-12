#!/usr/bin/env python3
"""离线独立 tiny 回归；每个 mode 有唯一可写目录，失败保留阶段与有界日志。"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import threading
import zlib

SEQ = 'ACGTTGCATGTCAGTACGATCGTACAGTCA'

# 独立于 checksum 清单的必要成员集，防止删掉文件和对应清单行后仍假通过。
# source-notices 保留固定 fastp 源码的完整原文，来源 SHA 见 source-archives.txt。
REQUIRED_NOTICES = frozenset((
    'LICENSE', 'isa-l/LICENSE', 'libdeflate/COPYING',
    'highway/LICENSE', 'highway/LICENSE-BSD3',
    'source-notices/src/cmdline.h', 'source-notices/src/writer.cpp',
    'source-notices/src/writer.h', 'source-notices/src/fastqreader.cpp',
    'source-notices/src/fastqreader.h',
    'source-notices/src/singleproducersingleconsumerlist.h',
))

def verify_notices(root=Path('/usr/local/share/doc/fastp')):
    root = Path(root)
    def regular(relative):
        path = root / relative
        if any((root / parent).is_symlink() for parent in (Path(relative), *Path(relative).parents)):
            raise ValueError('notice symlink is not allowed: ' + relative)
        if not path.is_file():
            raise ValueError('missing notice file: ' + relative)
        return path
    manifest = regular('notices.sha256')
    entries = {}
    for line in manifest.read_text().splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9._/-]+)', line)
        if not match:
            raise ValueError('malformed notice inventory row')
        digest, name = match.groups()
        if name not in REQUIRED_NOTICES:
            raise ValueError('unexpected notice member: ' + name)
        if name in entries:
            raise ValueError('duplicate notice member: ' + name)
        entries[name] = digest
    missing = REQUIRED_NOTICES - entries.keys()
    if missing:
        raise ValueError('incomplete notice inventory: ' + ', '.join(sorted(missing)))
    for name, digest in entries.items():
        if hashlib.sha256(regular(name).read_bytes()).hexdigest() != digest:
            raise ValueError('notice checksum mismatch: ' + name)
        print('notice OK:', name, flush=True)
    return len(entries)

def fq(name, seq=SEQ, quality='I'):
    return f'@{name}\n{seq}\n+\n{quality * len(seq)}\n'.encode()

def bgzf(data):
    compressor = zlib.compressobj(wbits=-15)
    payload = compressor.compress(data) + compressor.flush()
    header = bytes.fromhex('1f8b08040000000000ff060042430200')
    return header + struct.pack('<H', len(payload) + 25) + payload + struct.pack('<II', zlib.crc32(data), len(data))

def run(argv, input=None, expected=0):
    print('stage:', ' '.join(map(str, argv)), flush=True)
    r = subprocess.run(argv, input=input, capture_output=True, timeout=60)
    if r.returncode != expected:
        raise RuntimeError(f'rc={r.returncode}, expected={expected}\n' + (r.stdout+r.stderr).decode(errors='replace')[-10000:])
    return r

def report(name='report.json', count=1):
    d = json.loads(Path(name).read_text())
    assert d['summary']['fastp_version'] == '1.3.7', d['summary']
    assert d['summary']['before_filtering']['total_reads'] == count, d['summary']
    return d

def fastp(*args, input=None):
    return run(['fastp', '-w', '1', '-A', '-G', '-h', 'report.html', '-j', 'report.json', *args], input=input)

def check(mode):
    Path('reads.fq').write_bytes(fq('good') + fq('bad', quality='!'))
    if mode in ('se', 'buildtime'):
        fastp('-i', 'reads.fq', '-o', 'clean.fq')
        assert Path('clean.fq').read_bytes() == fq('good')
        assert report(count=2)['summary']['after_filtering']['total_reads'] == 1
        assert Path('report.html').stat().st_size > 1000
    elif mode == 'thread-cap':
        r = fastp('-i', 'reads.fq', '-o', 'clean.fq', '-w', '9999')
        assert b'Reduce worker threads to ' in r.stderr
        assert Path('clean.fq').read_bytes() == fq('good')
    elif mode == 'stdin':
        r = fastp('--stdin', '--stdout', input=Path('reads.fq').read_bytes())
        assert r.stdout == fq('good')
        report(count=2)
    elif mode == 'paired':
        Path('r1.fq.gz').write_bytes(gzip.compress(fq('pair/1')))
        Path('r2.fq.gz').write_bytes(gzip.compress(fq('pair/2', SEQ[::-1])))
        fastp('-i', 'r1.fq.gz', '-I', 'r2.fq.gz', '-o', 'o1.gz', '-O', 'o2.gz')
        assert gzip.decompress(Path('o1.gz').read_bytes()) == fq('pair/1')
        assert gzip.decompress(Path('o2.gz').read_bytes()) == fq('pair/2', SEQ[::-1])
        assert report(count=2)['summary']['after_filtering']['total_reads'] == 2
    elif mode == 'bgzf':
        # 两个独立有效 BGZF 流直接拼接；中间 EOF 空块不能丢掉后面的 reads。
        original = fq('first') + fq('second')
        compressed = bgzf(fq('first')) + bgzf(b'') + bgzf(fq('second')) + bgzf(b'')
        assert gzip.decompress(compressed) == original
        Path('concat.fq.gz').write_bytes(compressed)
        fastp('-i', 'concat.fq.gz', '-o', 'clean.fq')
        assert Path('clean.fq').read_bytes() == original
        assert report(count=2)['summary']['after_filtering']['total_reads'] == 2
    elif mode == 'fifo':
        os.mkfifo('input.fq')
        def writer():
            with open('input.fq', 'wb') as stream:
                stream.write(fq('fifo'))
        t = threading.Thread(target=writer, daemon=True)
        t.start()
        # 保留自动 evaluation 路径，验证 FIFO 不会被预读消耗/再次打开阻塞。
        run(['fastp', '-w', '1', '-i', 'input.fq', '-o', 'clean.fq', '-h', 'report.html', '-j', 'report.json'])
        t.join(timeout=2)
        assert not t.is_alive()
        assert Path('clean.fq').read_bytes() == fq('fifo')
        report()
    elif mode == 'batch':
        Path('directory_R1_test').mkdir()
        Path('directory_R1_test/sample_R1.fq').write_bytes(fq('pair/1'))
        Path('directory_R1_test/sample_R2.fq').write_bytes(fq('pair/2', SEQ[::-1]))
        run(['parallel.py', '-i', 'directory_R1_test', '-o', 'clean', '-r', 'reports', '-p', '1', '-a', '-w 1 -A -G'])
        assert gzip.decompress(Path('clean/sample_R1.clean.fastq.gz').read_bytes()) == fq('pair/1')
        assert gzip.decompress(Path('clean/sample_R2.clean.fastq.gz').read_bytes()) == fq('pair/2', SEQ[::-1])
        assert report('reports/sample_pe.fq.json', 2)['summary']['after_filtering']['total_reads'] == 2
        assert Path('reports/overall.html').stat().st_size > 1000
        run(['fastp-report-offline', 'reports/overall.html', 'overall.offline.html'])
        assert 'taffish-fastp-offline-assets' in Path('overall.offline.html').read_text()
    elif mode == 'offline-report':
        fastp('-i', 'reads.fq', '-o', 'clean.fq')
        original = Path('report.html').read_bytes()
        run(['fastp-report-offline', 'report.html', 'offline.html'])
        assert Path('report.html').read_bytes() == original
        output = Path('offline.html').read_bytes()
        assert b'taffish-fastp-offline-assets' in output
        assert b"<script src='https://opengene.org" not in output
        run(['fastp-report-offline', 'report.html', 'offline.html'], expected=1)
        assert Path('offline.html').read_bytes() == output
        Path('invalid.html').write_text('<html>invalid</html>')
        run(['fastp-report-offline', 'invalid.html', 'invalid-out.html'], expected=1)
        assert not Path('invalid-out.html').exists()
        run(['fastp-report-offline', 'missing.html', 'missing-out.html'], expected=1)
    elif mode == 'negative':
        run(['fastp', '-i', 'missing.fq'], expected=255)
        fastp('-i', 'reads.fq', '-o', 'clean.fq')
        digest = hashlib.sha256(Path('clean.fq').read_bytes()).hexdigest()
        run(['fastp', '-i', 'reads.fq', '-o', 'clean.fq', '--dont_overwrite'], expected=255)
        assert hashlib.sha256(Path('clean.fq').read_bytes()).hexdigest() == digest
    elif mode == 'licenses':
        print('stage: complete original-notice inventory and SHA256', flush=True)
        verify_notices()
    print('PASS', mode, flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['buildtime','se','thread-cap','stdin','paired','bgzf','fifo','batch','offline-report','negative','licenses'])
    a = p.parse_args()
    with tempfile.TemporaryDirectory(prefix='fastp-smoke-') as directory:
        os.chdir(directory)
        check(a.mode)
