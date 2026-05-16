taf-fastp 1.3.3-r1

TAFFISH wrapper for fastp, the ultrafast all-in-one FASTQ preprocessing and
quality-control tool for short-read sequencing data.

Usage:
  taf-fastp [TAF-APP-OPTION]
  taf-fastp [FASTP-CMD] [FASTP-ARGS...]
  taf-fastp [FASTP-OPTION] [FASTP-ARGS...]

TAF app options:
  -h, --help       Show this help text
  -v, --version    Show package and command version
  --compile        Print generated shell code instead of running it
  --               Stop parsing TAFFISH wrapper options

Upstream option calls:
  taf-fastp -- --version
  taf-fastp -- --help
  taf-fastp -i reads.fq -o clean.fq -h fastp.html -j fastp.json

Upstream commands:
  taf-fastp fastp --version
  taf-fastp fastp --help
  taf-fastp fastp -i reads.fq -o clean.fq -h fastp.html -j fastp.json
  taf-fastp parallel.py -h

Recommended examples:
  taf-fastp --version
  taf-fastp fastp --version
  taf-fastp fastp -i reads.fq -o clean.fq -h fastp.html -j fastp.json -w 4
  taf-fastp fastp -i sample_R1.fq.gz -I sample_R2.fq.gz -o clean_R1.fq.gz -O clean_R2.fq.gz -h sample.fastp.html -j sample.fastp.json -w 8
  taf-fastp fastp -i sample_R1.fq.gz -I sample_R2.fq.gz -o clean_R1.fq.gz -O clean_R2.fq.gz --detect_adapter_for_pe --length_required 30 --trim_poly_g -w 8
  cat reads.fq | taf-fastp fastp --stdin --stdout -w 4 > clean.fq
  taf-fastp parallel.py -i raw_fastq -o clean_fastq -r fastp_reports -p 4 -a '-w 2 --detect_adapter_for_pe'

Common fastp options:
  -i, --in1                 Read1 input FASTQ
  -o, --out1                Read1 output FASTQ
  -I, --in2                 Read2 input FASTQ for paired-end data
  -O, --out2                Read2 output FASTQ for paired-end data
  --unpaired1               Write read1 reads whose mate failed QC
  --unpaired2               Write read2 reads whose mate failed QC
  --failed_out              Write reads that failed filtering
  -h, --html                HTML report path, default fastp.html
  -j, --json                JSON report path, default fastp.json
  -w, --thread              Worker thread count
  -m, --merge               Merge overlapped paired-end reads
  --merged_out              Output path for merged reads
  -A, --disable_adapter_trimming
  -2, --detect_adapter_for_pe
  -a, --adapter_sequence
  --adapter_sequence_r2
  --adapter_fasta
  -q, --qualified_quality_phred
  -u, --unqualified_percent_limit
  -n, --n_base_limit
  -l, --length_required
  -L, --disable_length_filtering
  -5, --cut_front
  -3, --cut_tail
  -r, --cut_right
  -c, --correction
  -g, --trim_poly_g
  -x, --trim_poly_x
  -U, --umi
  -D, --dedup
  -p, --overrepresentation_analysis
  -y, --low_complexity_filter
  -s, --split
  -S, --split_by_lines
  --stdin
  --stdout
  --interleaved_in
  --dont_overwrite

Notes:
  - This command runs fastp inside the TAFFISH container image.
  - The clearest command-mode form is taf-fastp fastp ...
  - taf-fastp --help and taf-fastp --version are handled by the TAFFISH
    command wrapper. Use taf-fastp fastp --version or taf-fastp -- --version
    for the upstream fastp version.
  - If the first argument is a fastp option, taf-fastp forwards it to fastp,
    so taf-fastp -i reads.fq -o clean.fq also works.
  - The common option list above is not exhaustive. The wrapper calls the
    upstream fastp binary directly, so official fastp options can be used
    as-is. Run taf-fastp fastp --help for the complete upstream option list.
  - By default, fastp writes fastp.html and fastp.json in the current working
    directory unless -h and -j are provided.
  - Output is gzip-compressed when the output file name ends with .gz.
  - fastp is designed for short-read FASTQ data such as Illumina and MGI. This
    image does not bundle fastplong for Nanopore or PacBio long-read data.
  - parallel.py is the upstream batch helper. It calls fastp from PATH, writes
    per-sample HTML/JSON reports, and creates an aggregate overall.html.
  - The aggregate overall.html is created offline, but upstream parallel.py
    references CDN JavaScript libraries for some interactive browser charts.
  - This image does not bundle FastQC, MultiQC, aligners, or downstream
    analysis tools.
  - Input and output paths should be accessible from the current working
    directory or from mounted user paths.

Container:
  image: ghcr.io/taffish/fastp:1.3.3-r1
  supported backends: apptainer, podman, docker
  supported platforms: linux/amd64, linux/arm64

Upstream:
  project: fastp
  source:  https://github.com/OpenGene/fastp
  release: https://github.com/OpenGene/fastp/releases/tag/v1.3.3
  license: MIT
  citation: Chen 2025, doi:10.1002/imt2.70078, PMID:41112039
