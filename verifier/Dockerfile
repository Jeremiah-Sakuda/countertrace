# Countertrace verifier worker image.
#
# Pinned inputs: the Debian base by multi-arch index digest and the OSS CAD Suite
# release tarball by SHA-256 for each supported architecture. Rebuilding with a
# different tarball fails the checksum step instead of silently changing tools.
# Record the resulting local image ID in each evidence bundle; a tag is not a pin.
FROM debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251 AS toolchain

ARG TARGETARCH
ARG OSS_CAD_SUITE_RELEASE=2026-09-30
ARG OSS_CAD_SUITE_DATE=20260930
ARG OSS_CAD_SUITE_SHA256_ARM64=128ea0dd924f1469f6c52f49e570f695f350068ed8604321bea6def82409d257
ARG OSS_CAD_SUITE_SHA256_AMD64=9e50078dd84062bb78b19cc27a2185b9d37f8cd3d80c03242ec6d85044895fc1

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates curl g++ make python3 \
    && rm -rf /var/lib/apt/lists/*

RUN set -eu; \
    case "${TARGETARCH:-arm64}" in \
      arm64) arch=arm64; sum="$OSS_CAD_SUITE_SHA256_ARM64" ;; \
      amd64) arch=x64; sum="$OSS_CAD_SUITE_SHA256_AMD64" ;; \
      *) echo "unsupported architecture: $TARGETARCH" >&2; exit 1 ;; \
    esac; \
    file="oss-cad-suite-linux-${arch}-${OSS_CAD_SUITE_DATE}.tgz"; \
    curl -fsSL -o "/tmp/$file" \
      "https://github.com/YosysHQ/oss-cad-suite-build/releases/download/${OSS_CAD_SUITE_RELEASE}/$file"; \
    echo "$sum  /tmp/$file" | sha256sum -c -; \
    tar -xzf "/tmp/$file" -C /opt; \
    rm "/tmp/$file"; \
    cd /opt/oss-cad-suite; \
    rm -rf share/nextpnr* share/gtkwave* share/trellis share/icebox lib/ivl \
      bin/nextpnr* libexec/nextpnr* bin/gtkwave* libexec/gtkwave* bin/ecp* bin/ice* \
      bin/gowin* bin/apicula* bin/openFPGALoader* bin/iverilog bin/vvp \
      2>/dev/null || true; \
    printf '%s\n' "$OSS_CAD_SUITE_RELEASE" > /opt/oss-cad-suite/COUNTERTRACE_RELEASE

ENV PATH=/opt/oss-cad-suite/bin:$PATH

# Verilator's driver script needs full Perl, not Debian's perl-base.
RUN apt-get update \
    && apt-get install --no-install-recommends -y perl \
    && rm -rf /var/lib/apt/lists/*

FROM toolchain AS worker

# The harness and worker are trusted, read-only code. Job inputs arrive through a
# read-only mount at /job; the only writable paths are /out and a tmpfs /tmp.
COPY harness /opt/countertrace/harness
COPY worker.py /opt/countertrace/worker.py

RUN useradd --system --uid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin verifier
USER 10001
WORKDIR /tmp
ENTRYPOINT ["python3", "/opt/countertrace/worker.py"]
