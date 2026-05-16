# taf-fastp

TAFFISH wrapper for [fastp](https://github.com/OpenGene/fastp), the ultrafast
all-in-one FASTQ preprocessing and quality-control tool for short-read
sequencing data.

This repository packages upstream fastp 1.3.3 as a TAFFISH tool app. It builds
the official `v1.3.3` source release in a Debian 12 container image and exposes
the upstream `fastp` executable through the versioned `taf-fastp` command.

## Installation

Install from the public TAFFISH Hub index:

```sh
taf update
taf install fastp
```

Install the exact release:

```sh
taf install fastp 1.3.3-r1
```

For local testing before the app is published to the public index:

```sh
taf install --from .
```

## Usage

Show TAFFISH app help:

```sh
taf-fastp --help
```

Show the TAFFISH package version:

```sh
taf-fastp --version
```

Show the upstream fastp version:

```sh
taf-fastp fastp --version
taf-fastp -- --version
```

Show upstream command help:

```sh
taf-fastp fastp --help
taf-fastp -- --help
```

Process single-end FASTQ and write explicit HTML/JSON reports:

```sh
taf-fastp fastp \
  -i reads.fq \
  -o clean.fq \
  -h fastp.html \
  -j fastp.json \
  -w 4
```

Process paired-end gzip-compressed FASTQ:

```sh
taf-fastp fastp \
  -i sample_R1.fq.gz \
  -I sample_R2.fq.gz \
  -o clean_R1.fq.gz \
  -O clean_R2.fq.gz \
  -h sample.fastp.html \
  -j sample.fastp.json \
  -w 8
```

Use adapter detection, length filtering, and polyG trimming controls:

```sh
taf-fastp fastp \
  -i sample_R1.fq.gz \
  -I sample_R2.fq.gz \
  -o clean_R1.fq.gz \
  -O clean_R2.fq.gz \
  --detect_adapter_for_pe \
  --length_required 30 \
  --trim_poly_g \
  -w 8
```

Read from stdin and write passing reads to stdout:

```sh
cat reads.fq | taf-fastp fastp --stdin --stdout -w 4 > clean.fq
```

Batch process a folder of FASTQ files with the upstream helper:

```sh
taf-fastp parallel.py \
  -i raw_fastq \
  -o clean_fastq \
  -r fastp_reports \
  -p 4 \
  -a '-w 2 --detect_adapter_for_pe'
```

Because this is a command-mode TAFFISH tool, the first non-option argument is
the in-container command. For normal fastp usage, naming the upstream `fastp`
binary explicitly is the clearest form:

```sh
taf-fastp fastp -i reads.fq -o clean.fq -h fastp.html -j fastp.json
taf-fastp parallel.py -h
```

The app also accepts the common shorthand when the first argument is a fastp
option:

```sh
taf-fastp -i reads.fq -o clean.fq -h fastp.html -j fastp.json
```

This README lists common usage patterns, not the full upstream manual. Because
the TAFFISH wrapper calls the upstream `fastp` binary directly, official fastp
options are available as-is, including merge mode, split output, interleaved
input, unpaired/failed-read outputs, base correction, UMI handling,
deduplication, overrepresentation analysis, and low-complexity filtering. Use
the upstream help for the complete option list:

```sh
taf-fastp fastp --help
```

## Package

```text
name: fastp
command: taf-fastp
version: 1.3.3-r1
kind: tool
image: ghcr.io/taffish/fastp:1.3.3-r1
```

## Container

The container image is built from `docker/Dockerfile`. It starts from
`debian:12-slim`, downloads the upstream `v1.3.3` source archive from GitHub,
builds the required `isa-l`, `libdeflate`, and Google Highway libraries, and
installs fastp into `/usr/local/bin`.

The image includes these user-facing commands:

```text
fastp
parallel.py
python
python3
```

`parallel.py` is the upstream batch helper. It scans an input directory for
FASTQ files, pairs files by read-name flags such as `R1`/`R2`, runs `fastp`,
and writes per-sample reports plus an aggregate `overall.html`.

The fastp binary is built with the upstream compression dependencies:

```text
isa-l 2.31.0
libdeflate 1.25
Google Highway 1.3.0
```

`libdeflate` and Google Highway are linked into the fastp binary. `isa-l` is
provided as a runtime shared library so the same Dockerfile can build cleanly on
both amd64 and arm64.

This app intentionally does not bundle `fastplong`, FastQC, MultiQC, aligners,
or downstream analysis tools. fastp itself generates HTML and JSON reports, and
downstream aggregation or alignment should be handled by dedicated TAFFISH
tools or flows. The upstream `parallel.py` aggregate report references CDN
JavaScript libraries when viewed in a browser, so the file is created offline
but some interactive charts may need network access to render.

The image is built and validated for:

```text
linux/amd64
linux/arm64
```

The TAFFISH metadata declares a Docker smoke check:

```text
exist: fastp, parallel.py, python, python3
test:  fastp reports upstream version 1.3.3
test:  upstream fastp help is available
test:  upstream parallel.py help is available
test:  the fastp binary resolves the bundled isa-l runtime library
test:  a tiny single-end FASTQ can produce clean FASTQ plus HTML/JSON reports
test:  stdin/stdout mode works on a tiny FASTQ stream
test:  a tiny paired-end FASTQ pair can produce gzip-compressed outputs
test:  parallel.py can process a tiny paired-end folder and aggregate reports
```

During TAFFISH Hub indexing, this smoke metadata verifies that the published
image exposes the expected command surface, reports the pinned upstream
version, and can run minimal local FASTQ preprocessing/reporting workflows.
The smoke checks are intentionally small and deterministic; they verify the
container and representative fastp functionality, not every possible
combination of upstream options or full scientific correctness for every data
type.

## Upstream

- Project: fastp
- Source: <https://github.com/OpenGene/fastp>
- Release: <https://github.com/OpenGene/fastp/releases/tag/v1.3.3>
- Upstream license: MIT
- Primary citation: Chen 2025, doi:10.1002/imt2.70078, PMID:41112039
- Additional citations: Chen 2023, doi:10.1002/imt2.107; Chen et al. 2018,
  doi:10.1093/bioinformatics/bty560, PMID:30423086

## Maintainer Notes

Useful checks before publishing:

```sh
taf check
taf compile -- fastp --version
taf publish --release --dry-run
docker build -t ghcr.io/taffish/fastp:1.3.3-r1 -f docker/Dockerfile .
docker build --platform linux/amd64 -t ghcr.io/taffish/fastp:1.3.3-r1-amd64-test -f docker/Dockerfile .
docker build --platform linux/arm64 -t ghcr.io/taffish/fastp:1.3.3-r1-arm64-test -f docker/Dockerfile .
docker run --rm ghcr.io/taffish/fastp:1.3.3-r1 fastp --version
docker run --rm ghcr.io/taffish/fastp:1.3.3-r1 fastp --help
```

The repository wrapper files are licensed under Apache-2.0. Upstream fastp is
distributed under the MIT license, and third-party runtime components are
distributed under their own upstream licenses.
