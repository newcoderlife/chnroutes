EXCLUDE :=

all: generate

.PHONY: update-dependency
update-dependency:
	curl https://ftp.apnic.net/stats/apnic/delegated-apnic-latest -o dependency/delegated-apnic-latest
	curl https://gh.newco.workers.dev/https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt -o dependency/china_ip_list.txt
	curl https://gh.newco.workers.dev/https://raw.githubusercontent.com/gaoyifan/china-operator-ip/ip-lists/china.txt -o dependency/china.txt
	curl https://gh.newco.workers.dev/https://raw.githubusercontent.com/misakaio/chnroutes2/master/chnroutes.txt -o dependency/chnroutes.txt

.PHONY: generate
generate: update-dependency
	python3 generate.py --exclude $(EXCLUDE)

.PHONY: force-push
force-push:
	git add . && git commit --amend --no-edit && git push -f