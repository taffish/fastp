taf-fastp 1.3.7-r1

Purpose:
  Preprocess short-read FASTQ and inspect QC results in static HTML/JSON.

Common tasks:
  taf-fastp fastp -i reads.fq -o clean.fq -h report.html -j report.json -w 4
  taf-fastp fastp -i R1.fq.gz -I R2.fq.gz -o clean_R1.fq.gz -O clean_R2.fq.gz -h sample.html -j sample.json -w 4
  cat reads.fq | taf-fastp fastp --stdin --stdout -h stream.html -j stream.json -w 1 > clean.fq

Inputs and outputs:
  Inputs: plain/gzip/BGZF FASTQ, optionally a chosen adapter FASTA.
  Paired inputs must have matching reads in matching order.
  Outputs: filtered FASTQ, JSON statistics, and an HTML QC report.
  Work in a writable directory; set -h/-j to avoid default report names.
  Existing fastp outputs may be overwritten: use a new directory or
  --dont_overwrite. Output names ending in .gz enable gzip compression.

Common options:
  -i/-I           Read1/read2 input
  -o/-O           Read1/read2 output
  -h/-j           HTML/JSON output (name fastp explicitly after taf-fastp)
  -w              Worker threads; start with 1-4
  --adapter_fasta  Experiment-specific adapter FASTA
  --detect_adapter_for_pe, --length_required, --trim_poly_g
  --cut_front, --cut_tail, --cut_right, --umi, --dedup, --merge

View reports offline:
  Original HTML uses remote chart libraries. Create a self-contained copy:
  Docker:
    TAFFISH_CONTAINER_BACKEND=docker taf-fastp fastp-report-offline report.html offline.html
  Podman:
    TAFFISH_CONTAINER_BACKEND=podman taf-fastp fastp-report-offline report.html offline.html
  Apptainer (native Linux):
    TAFFISH_CONTAINER_BACKEND=apptainer taf-fastp fastp-report-offline report.html offline.html
  Open offline.html directly in your local browser; no server or GPU needed.
  The output must be new; input HTML remains unchanged. The same command
  converts parallel.py's overall.html. Review sample/path details before sharing.
  Keep a converted aggregate beside its original reports for View links;
  for offline per-sample viewing, convert that sample's HTML separately.
  On macOS use Docker/Podman, or copy the Linux-generated HTML to your Mac.

Use read-only inputs outside the working directory:
  Docker:
    TAFFISH_CONTAINER_BACKEND=docker TAFFISH_DOCKER_RUN_ARGS="-v /srv/reads:/inputs:ro" taf-fastp fastp -i /inputs/reads.fq -o clean.fq -h report.html -j report.json
  Podman:
    TAFFISH_CONTAINER_BACKEND=podman TAFFISH_PODMAN_RUN_ARGS="-v /srv/reads:/inputs:ro" taf-fastp fastp -i /inputs/reads.fq -o clean.fq -h report.html -j report.json
  Apptainer:
    TAFFISH_CONTAINER_BACKEND=apptainer TAFFISH_APPTAINER_RUN_ARGS="--bind /srv/reads:/inputs:ro" taf-fastp fastp -i /inputs/reads.fq -o clean.fq -h report.html -j report.json

Batch:
  taf-fastp parallel.py -i raw_fastq -o clean_fastq -r fastp_reports -p 1 -a "'-w 2 --detect_adapter_for_pe'"
  Use separate input/output/report directories and simple names without spaces
  or shell metacharacters. Check every expected FASTQ/JSON; parallel.py can
  return success even when a child command fails. Use fastp directly otherwise.

Paths or titles with spaces (retain the inner literal quotes):
  taf-fastp fastp -i "'reads with spaces.fq'" -o "'clean with spaces.fq'" -h report.html -j report.json --report_title "'Tiny sample QC'" -w 1
  taf-fastp fastp-report-offline report.html "'offline report.html'"

More help:
  taf-fastp fastp --help
  taf-fastp parallel.py -h
  taf-fastp fastp-report-offline --help
  https://github.com/taffish/fastp

Wrapper options:
  taf-fastp --help       Show this usage help.
  taf-fastp --version    Show wrapper version.
  taf-fastp --compile    Print generated shell.
  taf-fastp -- --version Show upstream fastp version.
