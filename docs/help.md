taf-fastp 1.3.6-r1

TAFFISH wrapper for fastp, an all-in-one FASTQ preprocessing and QC tool for
short-read sequencing data.

Usage:
  taf-fastp [TAF-APP-OPTION]
  taf-fastp [FASTP-CMD] [FASTP-ARGS...]
  taf-fastp [FASTP-OPTION] [FASTP-ARGS...]

TAF app options:
  -h, --help       Show this help text
  -v, --version    Show package and command version
  --compile        Print generated shell code instead of running it
  --               Stop parsing TAFFISH wrapper options

Help and version:
  taf-fastp -- --version
  taf-fastp -- --help
  taf-fastp fastp --version
  taf-fastp fastp --help
  taf-fastp parallel.py -h

Examples:
  taf-fastp fastp -i reads.fq -o clean.fq -h fastp.html -j fastp.json -w 4
  taf-fastp -i reads.fq -o clean.fq -h fastp.html -j fastp.json
  taf-fastp fastp -i R1.fq.gz -I R2.fq.gz -o clean_R1.fq.gz -O clean_R2.fq.gz -w 8
  taf-fastp fastp -i R1.fq.gz -I R2.fq.gz -o clean_R1.fq.gz -O clean_R2.fq.gz --detect_adapter_for_pe --length_required 30 --trim_poly_g -w 8
  cat reads.fq | taf-fastp fastp --stdin --stdout -w 4 > clean.fq
  taf-fastp parallel.py -i raw_fastq -o clean_fastq -r fastp_reports -p 4 -a "-w 2 --detect_adapter_for_pe"

Common options:
  -i, --in1       Read1 input FASTQ
  -o, --out1      Read1 output FASTQ
  -I, --in2       Read2 input FASTQ
  -O, --out2      Read2 output FASTQ
  -h, --html      HTML report path
  -j, --json      JSON report path
  -w, --thread    Worker thread count
  -m, --merge     Merge overlapped paired-end reads
  --stdin, --stdout, --interleaved_in
  --detect_adapter_for_pe, --adapter_sequence, --adapter_fasta
  --cut_front, --cut_tail, --cut_right, --trim_poly_g, --trim_poly_x
  --length_required, --umi, --dedup, --split, --dont_overwrite

Notes:
  The clearest command-mode form is taf-fastp fastp ...
  If the first argument is a fastp option, TAFFISH forwards it to fastp.
  Run taf-fastp fastp --help for the complete upstream option list.
  fastp writes fastp.html and fastp.json by default unless -h and -j are set.
  Outputs are gzip-compressed when output file names end with .gz.
  This release packages upstream fastp v1.3.6, which limits worker and BGZF
  reader thread counts for improved performance on high-core systems.
  This image does not bundle fastplong, FastQC, MultiQC, aligners, or
  downstream analysis tools. parallel.py is included for upstream batch runs.

Container:
  image: ghcr.io/taffish/fastp:1.3.6-r1
  platforms: linux/amd64, linux/arm64

Upstream:
  source:  https://github.com/OpenGene/fastp
  release: v1.3.6
  license: MIT
  citation: Chen 2025, doi:10.1002/imt2.70078, PMID:41112039
