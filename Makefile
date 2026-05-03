EXCLUDE ?=
OUTPUT_PREFIX ?= noncn
DEPENDENCY_DIR ?=
OUTPUTS := $(OUTPUT_PREFIX)4.routes $(OUTPUT_PREFIX)6.routes
CHECKSUM := $(OUTPUT_PREFIX).sha256

GEN_ARGS := --output-prefix "$(OUTPUT_PREFIX)"

ifneq ($(strip $(EXCLUDE)),)
GEN_ARGS += --exclude $(EXCLUDE)
endif

all: generate

.PHONY: download-dependencies
download-dependencies:
	@test -n "$(DEPENDENCY_DIR)" || { echo "DEPENDENCY_DIR is required"; exit 1; }
	@mkdir -p "$(DEPENDENCY_DIR)"
	curl -fsSL --retry 3 --connect-timeout 20 "https://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.csv" -o "$(DEPENDENCY_DIR)/ipv4-address-space.csv"
	curl -fsSL --retry 3 --connect-timeout 20 "https://ftp.apnic.net/stats/apnic/delegated-apnic-latest" -o "$(DEPENDENCY_DIR)/delegated-apnic-latest"
	curl -fsSL --retry 3 --connect-timeout 20 "https://raw.githubusercontent.com/17mon/china_ip_list/refs/heads/master/china_ip_list.txt" -o "$(DEPENDENCY_DIR)/china_ip_list.txt"
	curl -fsSL --retry 3 --connect-timeout 20 "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china.txt" -o "$(DEPENDENCY_DIR)/china.txt"
	curl -fsSL --retry 3 --connect-timeout 20 "https://raw.githubusercontent.com/misakaio/chnroutes2/refs/heads/master/chnroutes.txt" -o "$(DEPENDENCY_DIR)/chnroutes.txt"
	curl -fsSL --retry 3 --connect-timeout 20 "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china6.txt" -o "$(DEPENDENCY_DIR)/china6.txt"
	curl -fsSL --retry 3 --connect-timeout 20 "https://raw.githubusercontent.com/mayaxcn/china-ip-list/refs/heads/master/chnroute_v6.txt" -o "$(DEPENDENCY_DIR)/chnroute_v6.txt"

.PHONY: validate
validate:
	python3 -m py_compile generate.py
	@set -eu; \
	tmp="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp"' EXIT; \
	$(MAKE) --no-print-directory download-dependencies DEPENDENCY_DIR="$$tmp"; \
	python3 generate.py --validate-only --dependency-dir "$$tmp"

.PHONY: generate
generate:
	@set -eu; \
	tmp="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp"' EXIT; \
	$(MAKE) --no-print-directory download-dependencies DEPENDENCY_DIR="$$tmp"; \
	python3 generate.py --dependency-dir "$$tmp" $(GEN_ARGS)

.PHONY: generate-local
generate-local:
	@test -n "$(DEPENDENCY_DIR)" || { echo "DEPENDENCY_DIR is required"; exit 1; }
	python3 generate.py --dependency-dir "$(DEPENDENCY_DIR)" $(GEN_ARGS)

.PHONY: checksum
checksum:
	shasum -a 256 $(OUTPUTS) > "$(CHECKSUM)"
