EXCLUDE ?=
NEXT ?= ether1
NEXT6 ?=
ROUTE_TABLE ?= noncn
ROUTE_COMMENT ?= chnroutes
OUTPUT ?= noncn.rsc

NEXT_ARG := $(if $(strip $(NEXT)),$(NEXT),ether1)
GEN_ARGS := --next "$(NEXT_ARG)" --table "$(ROUTE_TABLE)" --comment "$(ROUTE_COMMENT)" --output "$(OUTPUT)"

ifneq ($(strip $(NEXT6)),)
GEN_ARGS += --next6 "$(NEXT6)"
endif

ifneq ($(strip $(EXCLUDE)),)
GEN_ARGS += --exclude $(EXCLUDE)
endif

all: generate

.PHONY: update-dependency
update-dependency:
	@set -eu; \
	tmp="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp"' EXIT; \
	curl -fsSL --retry 3 --connect-timeout 20 "https://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.csv" -o "$$tmp/ipv4-address-space.csv"; \
	curl -fsSL --retry 3 --connect-timeout 20 "https://ftp.apnic.net/stats/apnic/delegated-apnic-latest" -o "$$tmp/delegated-apnic-latest"; \
	curl -fsSL --retry 3 --connect-timeout 20 "https://raw.githubusercontent.com/17mon/china_ip_list/refs/heads/master/china_ip_list.txt" -o "$$tmp/china_ip_list.txt"; \
	curl -fsSL --retry 3 --connect-timeout 20 "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china.txt" -o "$$tmp/china.txt"; \
	curl -fsSL --retry 3 --connect-timeout 20 "https://raw.githubusercontent.com/misakaio/chnroutes2/refs/heads/master/chnroutes.txt" -o "$$tmp/chnroutes.txt"; \
	curl -fsSL --retry 3 --connect-timeout 20 "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china6.txt" -o "$$tmp/china6.txt"; \
	curl -fsSL --retry 3 --connect-timeout 20 "https://raw.githubusercontent.com/mayaxcn/china-ip-list/refs/heads/master/chnroute_v6.txt" -o "$$tmp/chnroute_v6.txt"; \
	python3 generate.py --validate-only --dependency-dir "$$tmp"; \
	cp "$$tmp/ipv4-address-space.csv" dependency/ipv4-address-space.csv; \
	cp "$$tmp/delegated-apnic-latest" dependency/delegated-apnic-latest; \
	cp "$$tmp/china_ip_list.txt" dependency/china_ip_list.txt; \
	cp "$$tmp/china.txt" dependency/china.txt; \
	cp "$$tmp/chnroutes.txt" dependency/chnroutes.txt; \
	cp "$$tmp/china6.txt" dependency/china6.txt; \
	cp "$$tmp/chnroute_v6.txt" dependency/chnroute_v6.txt

.PHONY: validate
validate:
	python3 -m py_compile generate.py
	python3 generate.py --validate-only

.PHONY: generate
generate: update-dependency
	python3 generate.py $(GEN_ARGS)

.PHONY: generate-local
generate-local:
	python3 generate.py $(GEN_ARGS)

.PHONY: checksum
checksum:
	shasum -a 256 "$(OUTPUT)" > "$(OUTPUT).sha256"
