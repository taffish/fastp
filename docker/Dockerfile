ARG FASTP_VERSION=1.3.4
ARG FASTP_SHA256=105c948dc11e567ca6d7532f76ef53b456505256b5ba16012a0182810c28b591
ARG ISAL_VERSION=2.31.0
ARG ISAL_SHA256=e218b7b2e241cfb8e8b68f54a6e5eed80968cc387c4b1af03708b54e9fb236f1
ARG LIBDEFLATE_VERSION=1.25
ARG LIBDEFLATE_SHA256=d11473c1ad4c57d874695e8026865e38b47116bbcb872bfc622ec8f37a86017d
ARG HIGHWAY_VERSION=1.3.0
ARG HIGHWAY_SHA256=07b3c1ba2c1096878a85a31a5b9b3757427af963b1141ca904db2f9f4afe0bc2

FROM debian:12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive
ARG FASTP_VERSION
ARG FASTP_SHA256
ARG ISAL_VERSION
ARG ISAL_SHA256
ARG LIBDEFLATE_VERSION
ARG LIBDEFLATE_SHA256
ARG HIGHWAY_VERSION
ARG HIGHWAY_SHA256

RUN set -eux; \
    for attempt in 1 2 3; do \
      if apt-get -o Acquire::Retries=3 update \
       && apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
            autoconf \
            automake \
            build-essential \
            ca-certificates \
            cmake \
            curl \
            libtool \
            nasm \
            pkg-config; then \
        break; \
      fi; \
      if [ "$attempt" = "3" ]; then exit 1; fi; \
      apt-get clean; \
      rm -rf /var/lib/apt/lists/*; \
      sleep 5; \
    done; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/build/isa-l

RUN curl -fsSL "https://github.com/intel/isa-l/archive/refs/tags/v${ISAL_VERSION}.tar.gz" \
      -o isa-l.tar.gz \
 && echo "${ISAL_SHA256}  isa-l.tar.gz" | sha256sum -c - \
 && tar -xzf isa-l.tar.gz --strip-components=1 \
 && ./autogen.sh \
 && ./configure \
      --prefix=/opt/fastp-deps \
      --libdir=/opt/fastp-deps/lib \
      --enable-shared=yes \
      --enable-static=no \
 && make -j"$(nproc)" \
 && make install

WORKDIR /tmp/build/libdeflate

RUN curl -fsSL "https://github.com/ebiggers/libdeflate/archive/refs/tags/v${LIBDEFLATE_VERSION}.tar.gz" \
      -o libdeflate.tar.gz \
 && echo "${LIBDEFLATE_SHA256}  libdeflate.tar.gz" | sha256sum -c - \
 && tar -xzf libdeflate.tar.gz --strip-components=1 \
 && cmake -S . -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/fastp-deps \
      -DLIBDEFLATE_BUILD_STATIC_LIB=ON \
      -DLIBDEFLATE_BUILD_SHARED_LIB=OFF \
      -DLIBDEFLATE_BUILD_GZIP=OFF \
      -DLIBDEFLATE_BUILD_TESTS=OFF \
 && cmake --build build --parallel "$(nproc)" \
 && cmake --install build

WORKDIR /tmp/build/highway

RUN curl -fsSL "https://github.com/google/highway/archive/refs/tags/${HIGHWAY_VERSION}.tar.gz" \
      -o highway.tar.gz \
 && echo "${HIGHWAY_SHA256}  highway.tar.gz" | sha256sum -c - \
 && tar -xzf highway.tar.gz --strip-components=1 \
 && cmake -S . -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/fastp-deps \
      -DBUILD_SHARED_LIBS=OFF \
      -DHWY_ENABLE_CONTRIB=OFF \
      -DHWY_ENABLE_TESTS=OFF \
      -DHWY_ENABLE_EXAMPLES=OFF \
 && cmake --build build --parallel "$(nproc)" \
 && cmake --install build

WORKDIR /tmp/build/fastp

RUN curl -fsSL "https://github.com/OpenGene/fastp/archive/refs/tags/v${FASTP_VERSION}.tar.gz" \
      -o fastp.tar.gz \
 && echo "${FASTP_SHA256}  fastp.tar.gz" | sha256sum -c - \
 && tar -xzf fastp.tar.gz --strip-components=1 \
 && PKG_CONFIG_PATH=/opt/fastp-deps/lib/pkgconfig \
      make -j"$(nproc)" \
        INCLUDE_DIRS=/opt/fastp-deps/include \
        LIBRARY_DIRS=/opt/fastp-deps/lib \
 && mkdir -p /opt/fastp/bin /opt/fastp/share/doc/fastp \
 && install -m 0755 fastp /opt/fastp/bin/fastp \
 && install -m 0755 parallel.py /opt/fastp/bin/parallel.py \
 && install -m 0644 README.md /opt/fastp/share/doc/fastp/README.md \
 && install -m 0644 LICENSE /opt/fastp/share/doc/fastp/LICENSE \
 && LD_LIBRARY_PATH=/opt/fastp-deps/lib /opt/fastp/bin/fastp --version | grep -Fx "fastp ${FASTP_VERSION}" >/dev/null \
 && LD_LIBRARY_PATH=/opt/fastp-deps/lib /opt/fastp/bin/fastp --help 2>&1 | grep -F "usage:" >/dev/null \
 && test -x /opt/fastp/bin/parallel.py

FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive
ARG FASTP_VERSION

RUN set -eux; \
    for attempt in 1 2 3; do \
      if apt-get -o Acquire::Retries=3 update \
       && apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
            libgcc-s1 \
            libstdc++6 \
            python-is-python3 \
            python3; then \
        break; \
      fi; \
      if [ "$attempt" = "3" ]; then exit 1; fi; \
      apt-get clean; \
      rm -rf /var/lib/apt/lists/*; \
      sleep 5; \
    done; \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/fastp/bin/fastp /usr/local/bin/fastp
COPY --from=builder /opt/fastp/bin/parallel.py /usr/local/bin/parallel.py
COPY --from=builder /opt/fastp/share/doc/fastp/ /usr/local/share/doc/fastp/
COPY --from=builder /opt/fastp-deps/lib/libisal.so.2.0.31 /usr/local/lib/libisal.so.2.0.31

RUN ln -sf libisal.so.2.0.31 /usr/local/lib/libisal.so.2 \
 && ln -sf libisal.so.2.0.31 /usr/local/lib/libisal.so \
 && ldconfig \
 && fastp --version | grep -Fx "fastp ${FASTP_VERSION}" >/dev/null \
 && fastp --help 2>&1 | grep -F "usage:" >/dev/null \
 && parallel.py -h 2>&1 | grep -F "A python script to use fastp" >/dev/null \
 && ldd "$(command -v fastp)" | grep -F "libisal" >/dev/null

RUN set -eux; \
    mkdir -p /tmp/fastp-test; \
    cd /tmp/fastp-test; \
    printf "@r1\nACGTACGTACGTACGTACGT\n+\nFFFFFFFFFFFFFFFFFFFF\n@r2\nACGTACGTNNNNACGTACGT\n+\nFFFFFFFF!!!!FFFFFFFF\n" > reads.fq; \
    fastp -i reads.fq -o clean.fq -h report.html -j report.json -w 1 >/tmp/fastp-se.log 2>&1; \
    test -s clean.fq; \
    test -s report.html; \
    test -s report.json; \
    grep -F '"fastp_version": "' report.json >/dev/null; \
    grep -F "@r1" clean.fq >/dev/null; \
    fastp --stdin --stdout -w 1 < reads.fq > stdout.fq 2>/tmp/fastp-stdin.log; \
    grep -F "@r1" stdout.fq >/dev/null; \
    printf "@p1/1\nACGTACGTACGTACGTACGT\n+\nFFFFFFFFFFFFFFFFFFFF\n" > r1.fq; \
    printf "@p1/2\nTGCATGCATGCATGCATGCA\n+\nFFFFFFFFFFFFFFFFFFFF\n" > r2.fq; \
    fastp -i r1.fq -I r2.fq -o out1.fq.gz -O out2.fq.gz -h pe.html -j pe.json -w 1 >/tmp/fastp-pe.log 2>&1; \
    test -s out1.fq.gz; \
    test -s out2.fq.gz; \
    test -s pe.html; \
    test -s pe.json; \
    mkdir -p batch-in batch-out batch-report; \
    cp r1.fq batch-in/sample_R1.fq; \
    cp r2.fq batch-in/sample_R2.fq; \
    parallel.py -i batch-in -o batch-out -r batch-report -p 1 -a "-w 1" >/tmp/fastp-parallel.log; \
    test -s batch-out/sample_R1.clean.fastq.gz; \
    test -s batch-out/sample_R2.clean.fastq.gz; \
    test -s batch-report/sample_pe.fq.html; \
    test -s batch-report/sample_pe.fq.json; \
    test -s batch-report/overall.html; \
    cd /; \
    rm -rf /tmp/fastp-test /tmp/fastp-se.log /tmp/fastp-stdin.log /tmp/fastp-pe.log /tmp/fastp-parallel.log

WORKDIR /root

ENV TAFFISH_ENV=TAFFISH
ENV TAFFISH_NAME=fastp
