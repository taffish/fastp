ARG FASTP_VERSION=1.4.0
ARG FASTP_SHA256=28c0537e9d1f32f5a5c404562e6a282bf373b034a4c3a3610d9aa31d6429b550
ARG ISAL_VERSION=2.31.0
ARG ISAL_SHA256=e218b7b2e241cfb8e8b68f54a6e5eed80968cc387c4b1af03708b54e9fb236f1
ARG LIBDEFLATE_VERSION=1.25
ARG LIBDEFLATE_SHA256=d11473c1ad4c57d874695e8026865e38b47116bbcb872bfc622ec8f37a86017d
ARG HIGHWAY_VERSION=1.3.0
ARG HIGHWAY_SHA256=07b3c1ba2c1096878a85a31a5b9b3757427af963b1141ca904db2f9f4afe0bc2
# 构建来源维护：下方四个源码归档使用版本 tag + SHA256；tag/URL 不是永久保存承诺，哈希用于拒绝字节变化。
# 404/校验失败先排除网络、错误页和截断，再核对各自官方 tag/commit；旧材料只接受原哈希匹配的可信副本。
# 采用新材料须重验源码、许可与逐平台/后端功能；已发布身份通过后继 release 修复，不盲改哈希或跳过校验。

FROM debian:12-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ARG FASTP_VERSION
ARG FASTP_SHA256
ARG ISAL_VERSION
ARG ISAL_SHA256
ARG LIBDEFLATE_VERSION
ARG LIBDEFLATE_SHA256
ARG HIGHWAY_VERSION
ARG HIGHWAY_SHA256

# 两个 stage 的 Debian digest 固定基础镜像，但各自 apt-get 仍从活动仓库解析构建/运行依赖。
# 重试不能恢复已下架的包；先核对仓库分支和包身份，恢复旧闭包需可信同版本材料或经核验的快照。
# 更新依赖时需同时复核 builder 与 runtime 的动态库 ABI，并重新构建所有声明平台。
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

# Remove only debug sections; retain runtime symbols and original notices.
RUN strip --strip-debug /opt/fastp/bin/fastp /opt/fastp-deps/lib/libisal.so.2.0.31 \
 && mkdir -p /opt/fastp/share/doc/fastp/isa-l /opt/fastp/share/doc/fastp/libdeflate /opt/fastp/share/doc/fastp/highway \
 && install -m 0644 /tmp/build/isa-l/LICENSE /opt/fastp/share/doc/fastp/isa-l/LICENSE \
 && install -m 0644 /tmp/build/libdeflate/COPYING /opt/fastp/share/doc/fastp/libdeflate/COPYING \
 && install -m 0644 /tmp/build/highway/LICENSE /tmp/build/highway/LICENSE-BSD3 /opt/fastp/share/doc/fastp/highway/ \
 && for source in cmdline.h writer.cpp writer.h fastqreader.cpp fastqreader.h singleproducersingleconsumerlist.h; do \
      install -D -m 0644 "/tmp/build/fastp/src/$source" "/opt/fastp/share/doc/fastp/source-notices/src/$source"; \
    done \
 && printf 'fastp %s %s\nisa-l %s %s\nlibdeflate %s %s\nhighway %s %s\n' \
      "$FASTP_VERSION" "$FASTP_SHA256" "$ISAL_VERSION" "$ISAL_SHA256" \
      "$LIBDEFLATE_VERSION" "$LIBDEFLATE_SHA256" "$HIGHWAY_VERSION" "$HIGHWAY_SHA256" \
      > /opt/fastp/share/doc/fastp/source-archives.txt

COPY docker/report-assets.lock /opt/fastp/report-assets/report-assets.lock
# 报告 JS/CSS 及许可原文也依赖远端：report-assets.lock 固定 URL/哈希，不保证 CDN/raw 文件长期可得。
# 下载失败先核对 lock 对应版本、文件类型与完整性；迁移来源仍须匹配原哈希，不能用 latest 资源替代。
# 若更新资源，重新核对许可及离线 HTML/浏览器功能；仅 fastp --version 或主命令 smoke 通过不够。
RUN cd /opt/fastp/report-assets \
 && while read -r digest name url; do \
      curl -fsSL --retry 3 "$url" -o "$name" \
      && echo "$digest  $name" | sha256sum -c - || exit 1; \
    done < report-assets.lock

FROM debian:12-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
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
COPY --from=builder /opt/fastp/report-assets/ /usr/local/share/fastp/report-assets/
COPY docker/fastp-report-offline.py /usr/local/bin/fastp-report-offline
COPY docker/fastp-smoke.py /usr/local/share/fastp/fastp-smoke.py
COPY docker/notices.sha256 /usr/local/share/doc/fastp/notices.sha256

RUN ln -sf libisal.so.2.0.31 /usr/local/lib/libisal.so.2 \
 && ln -sf libisal.so.2.0.31 /usr/local/lib/libisal.so \
 && ldconfig \
 && fastp --version | grep -Fx "fastp ${FASTP_VERSION}" >/dev/null \
 && fastp --help 2>&1 | grep -F "usage:" >/dev/null \
 && parallel.py -h 2>&1 | grep -F "A python script to use fastp" >/dev/null \
 && ldd "$(command -v fastp)" | grep -F "libisal" >/dev/null

RUN chmod 0755 /usr/local/bin/fastp-report-offline \
 && fastp-report-offline --help >/dev/null \
 && python3 /usr/local/share/fastp/fastp-smoke.py licenses \
 && python3 /usr/local/share/fastp/fastp-smoke.py buildtime

WORKDIR /root

ENV TAFFISH_ENV=TAFFISH
ENV TAFFISH_NAME=fastp
