# taf-fastp

TAFFISH tool app for [fastp](https://github.com/OpenGene/fastp): preprocessing,
filtering, adapter trimming and quality control of short-read FASTQ data.

## Package and upstream

| Field | Value |
|---|---|
| Package / command | fastp / taf-fastp |
| Version | 1.3.7-r1 |
| Image | ghcr.io/taffish/fastp:1.3.7-r1 |
| Native platforms | linux/amd64, linux/arm64 |
| Upstream | OpenGene/fastp v1.3.7 |
| Source commit | 8a2397b6628ae14127efdb7566f67fc05f9aea56 |

[Upstream 1.3.7](https://github.com/OpenGene/fastp/releases/tag/v1.3.7)
fixes concatenated BGZF inputs containing embedded EOF blocks, avoids
pre-evaluating non-seekable inputs, fixes pairing when a batch directory name
contains R1, and creates BINDIR during installation. This package does not
patch fastp's algorithms or the upstream batch script.

## Installation

```sh
taf update
taf install fastp
taf install fastp 1.3.7-r1
```

The exact release is available through the public index only after publication.

## Quick start

Work in a writable analysis directory containing your inputs:

```sh
taf-fastp fastp -i reads.fq -o clean.fq -h fastp.html -j fastp.json -w 4
taf-fastp fastp-report-offline fastp.html fastp.offline.html
```

Open `fastp.offline.html` directly in a local browser. No server, display,
GPU, exposed port or browser inside the container is needed.

Paired-end gzip/BGZF input and gzip output:

```sh
taf-fastp fastp -i R1.fq.gz -I R2.fq.gz -o clean_R1.fq.gz -O clean_R2.fq.gz -h sample.html -j sample.json -w 4
cat reads.fq | taf-fastp fastp --stdin --stdout -h stream.html -j stream.json -w 1 > clean.fq
```

Input pairing/order is the user's responsibility. Choose adapter, UMI, merge,
deduplication and filtering options according to the experiment; tiny smoke
tests do not qualify every scientific option combination. fastp is intended for
short reads; upstream's separate fastplong project targets long reads.

## Commands and wrapper boundary

```sh
taf-fastp --help
taf-fastp --version
taf-fastp fastp --help
taf-fastp -- --version
taf-fastp parallel.py -h
taf-fastp fastp-report-offline --help
```

The entry remains the two-line container tag plus `fastp ::*ARGV*::`.
Automatic command mode exposes fastp, parallel.py, python and python3.
Name `fastp` explicitly to avoid confusing wrapper help with upstream's
`-h HTML` option. The offline helper is an additional report-only utility,
not a replacement entrypoint.

TAFFISH 0.11.0 reconstructs shell arguments: retain literal quotes for values
containing spaces. These forms are included in wrapper validation:

```sh
taf-fastp fastp -i "'reads with spaces.fq'" -o "'clean with spaces.fq'" -h report.html -j report.json --report_title "'Tiny sample QC'" -w 1
taf-fastp fastp-report-offline report.html "'offline report.html'"
```

## Batch processing

```sh
taf-fastp parallel.py -i raw_fastq -o clean_fastq -r fastp_reports -p 1 -a "'-w 2 --detect_adapter_for_pe'"
taf-fastp fastp-report-offline fastp_reports/overall.html fastp_reports/overall.offline.html
```

Use simple path/file names without spaces or shell metacharacters for
`parallel.py`: upstream constructs unquoted shell commands internally.
For paths with spaces, call `fastp` directly using the tested quoting above.
Batch input/output/report directories must be separate; set both `-o` and
`-r` explicitly. Upstream does not reliably propagate child fastp failures;
verify each expected clean FASTQ and per-sample JSON, not only the batch exit
status or overall.html. No wrapper is added to conceal that upstream boundary.

The converted aggregate's charts are self-contained; its per-sample `View`
links are not embedded reports. Keep the aggregate beside the original HTML
files to preserve these relative links. They open original CDN-dependent
reports; for offline per-sample viewing, convert that HTML separately and open
the new file, for example:

```sh
taf-fastp fastp-report-offline fastp_reports/sample_pe.fq.html fastp_reports/sample.offline.html
```

## Inputs, outputs and runtime writes

Inputs: plain, gzip or BGZF FASTQ; optional experiment-specific adapter FASTA.
Outputs: filtered FASTQ (gzip when the output name ends in .gz), per-run JSON
statistics and HTML reports. Set `-h`/`-j` to avoid the default filenames.

Run in a new directory or use `--dont_overwrite` for fastp output protection.
The offline helper takes exactly INPUT OUTPUT, refuses any existing output
(including symlinks), leaves the original unchanged, and atomically creates a
new HTML file. Its temporary file is confined to the output's parent directory.

No network is needed for processing or offline conversion. No runtime writes
to /opt, /usr or the SIF root are required. Smoke uses a unique private /tmp
directory; persistent outputs are written only to the current working directory
or explicit writable binds.

## Backends and shared inputs

All three backends use the same installed commands:

```sh
TAFFISH_CONTAINER_BACKEND=docker taf-fastp fastp -i reads.fq -o clean.fq -h report.html -j report.json
TAFFISH_CONTAINER_BACKEND=podman taf-fastp fastp -i reads.fq -o clean.fq -h report.html -j report.json
TAFFISH_CONTAINER_BACKEND=apptainer taf-fastp fastp -i reads.fq -o clean.fq -h report.html -j report.json
```

Use a fresh output directory for each example. For read-only shared inputs
outside the working directory, set the corresponding site/run policy:

```sh
TAFFISH_CONTAINER_BACKEND=docker TAFFISH_DOCKER_RUN_ARGS="-v /srv/reads:/inputs:ro" taf-fastp fastp -i /inputs/reads.fq -o clean.fq -h report.html -j report.json
TAFFISH_CONTAINER_BACKEND=podman TAFFISH_PODMAN_RUN_ARGS="-v /srv/reads:/inputs:ro" taf-fastp fastp -i /inputs/reads.fq -o clean.fq -h report.html -j report.json
TAFFISH_CONTAINER_BACKEND=apptainer TAFFISH_APPTAINER_RUN_ARGS="--bind /srv/reads:/inputs:ro" taf-fastp fastp -i /inputs/reads.fq -o clean.fq -h report.html -j report.json
```

The same bind can supply an adapter FASTA via `--adapter_fasta /inputs/adapters.fa`.
The administrator may provision shared read-only inputs once; normal users
need read/traverse access and their own writable output directory. Input
FASTQ/adapter FASTA are project-specific, not a mechanically downloadable
database/model family. Small built-in adapter strings are compiled into fastp.
Thus there is no model installer, implicit download, discovery override or
system-wide model cache; neither root nor a repeated per-user download is needed.

Apptainer requires native Linux. On macOS, use Docker or Podman, or run on a
matching Linux server and copy HTML/JSON back for local viewing.

## Static HTML and offline browser assets

The GUI surface is a static report, not a desktop or service. Official source,
README, entrypoints and companion links were checked: the Galaxy integration
is a separate hosted platform, not an omitted in-container GUI dependency.
FastQC, MultiQC, fastplong and aligners are separate analysis tools.

Original upstream per-sample HTML uses remote Plotly 1.2.0; parallel.py uses
remote Plotly, Chart.js and normalize CSS. Generate reports offline, then run
`fastp-report-offline` before viewing without network. It recognizes the
pinned upstream templates, verifies all packaged asset SHA256 values, embeds
the assets plus notices in a new file, and rejects unknown templates or
unexpected external runtime references. It does not change FASTQ, JSON,
statistics, figures' source data or the original report.

Pinned assets are Plotly 1.58.5 (both report types, the legacy plotly-latest
line), Chart.js 4.5.1 and modern-normalize 2.0.0. The converter replaces the
single-report 1.2.0 reference because its PNG export fails in current Chrome;
the fixed 1.58.5 renderer passes actual button-driven PNG export. This affects
only the converted HTML's rendering library, not data, analysis or raw reports.
Original library notices are embedded with the converted report. Links to
upstream/citations remain normal user-initiated links. Do not publish reports
containing sensitive sample names, command paths or read identifiers without
review; only open reports from trusted data and sources.

## Container, dependencies and size

Debian 12-slim is pinned by multiarch digest. Source archives are SHA256-pinned:
fastp 1.3.7, ISA-L 2.31.0, libdeflate 1.25 and Highway 1.3.0.
ISA-L is a resolved shared library; libdeflate and Highway are statically linked.
A separate builder stage keeps compilers, headers and source trees out of the
runtime. Debug sections are stripped without deleting runtime symbols.
The runtime contains Python 3 for upstream parallel.py and the small
report/smoke helpers; no Conda, browser, GUI desktop or large reference bundle.

Original licenses and source identities live in `/usr/local/share/doc/fastp`.
`source-notices/src/` also preserves six unmodified source files containing
the bundled cmdline BSD-3-Clause notice (Hideyuki Tanaka) and the file-level
MIT notice (Shifu Chen). These come from the same checksum-pinned fastp archive,
not from a different cmdline release. `notices.sha256` binds all 11 original
notice files; smoke independently requires every member, rejecting missing
inventory rows, missing/corrupt files, duplicate entries and symlinks.
Browser assets, checksums and original notices are in
`/usr/local/share/fastp/report-assets`. Debian package copyright files under
/usr/share/doc remain intact. Apt lists are removed in the same install layer.
Final image sizes and runtime-directory measurements are recorded in the
maintainer evidence rather than inferred from the Dockerfile.

## Validation and development

From this checkout:

```sh
taf check
taf build
./target/taf-fastp-v1.3.7-r1 fastp --version
taf run -b docker -- fastp --version
docker build --platform linux/arm64 -f docker/Dockerfile -t ghcr.io/taffish/fastp:1.3.7-r1 .
taf publish --build --release --dry-run
```

The canonical Action uses app-root context `.` and native amd64/arm64 runners.
The old standard workflow was replaced byte-for-byte from fresh `taf new`;
no app-specific workflow edits. Build-time checks are version/help, dynamic
library resolution, original notices and one small single-threaded SE path;
browser rendering, thread-cap, FIFO/BGZF and full smoke stay at runtime.

Manifest commands are independent fresh-container tests: existence, version,
help, linkage, SE, thread cap, stdin, gzip PE, concatenated BGZF, FIFO, batch
pairing, report conversion/error boundaries and notices. Release evidence
also covers normal/read-only Docker/Podman, actual read-only Apptainer SIF,
ordinary-user generated wrappers, actual shared read-only binds, host output
ownership and browser interaction. These are engineering tests, not full
scientific validation of every filter or sequencing technology.

Final current-image evidence: native amd64 Docker/Podman normal and read-only,
actual Apptainer SIF, plus native arm64 Podman normal/read-only; 140 independent
manifest checks and 84 ordinary-user wrapper checks passed. The three backend
axis is fully covered on xjp Linux amd64. Docker arm64 runtime was not separately
revalidated after this notice-only repair; an earlier candidate encountered an
engine startup interruption (Created, PID 0), not a current-image PASS.
Arm64 Apptainer was not separately validated. There is no backend-specific
argument or architecture coupling requiring the full Cartesian product.
Final image sizes after the notice repair: amd64 124,241,296 bytes;
arm64 148,207,338 bytes (about 48 KB added per image). The complete 11-file
notice inventory passes current-image validation and failure injection on
both native platforms; 15 host-side unit tests cover the verifier's boundaries.
Browser checks cover single/aggregate charts, collapse/zoom and actual PNG
downloads, with no runtime network requests or console errors. Static
single-sample reports retain upstream's wide layout and may require horizontal
scrolling on narrow screens. Batch View links have the explicit boundary above.

Current validation receipts and final status:
`docs-for-codex/app-update-evidence/fastp-1.3.7-r1-notice-fix-20260911/` in the Hub
maintainer workspace. Publication, Action/GHCR success and accepted Index
coverage are separate steps; this checkout does not imply any is complete.

## License and citation

Wrapper/helper code: Apache-2.0. Upstream fastp and libdeflate: MIT;
ISA-L: BSD-3-Clause; Highway: Apache-2.0/BSD-3-Clause notices retained.
The cmdline code bundled inside fastp retains its original BSD-3-Clause
copyright/conditions/disclaimer, and file-level MIT copyrights are retained
alongside fastp's top-level MIT license; they are not replaced by it.
Plotly, Chart.js and modern-normalize retain their original MIT notices.

- Chen 2025: doi:10.1002/imt2.70078; PMID:41112039.
- Chen 2023: doi:10.1002/imt2.107.
- Chen et al. 2018: doi:10.1093/bioinformatics/bty560; PMID:30423086.
