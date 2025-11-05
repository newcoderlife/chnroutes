EXCLUDE :=
NEXT :=

all: generate

.PHONY: update-dependency
update-dependency:
	curl https://ftp.apnic.net/stats/apnic/delegated-apnic-latest -o dependency/delegated-apnic-latest
	curl https://raw.githubusercontent.com/17mon/china_ip_list/refs/heads/master/china_ip_list.txt -o dependency/china_ip_list.txt
	curl https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china.txt -o dependency/china.txt
	curl https://raw.githubusercontent.com/misakaio/chnroutes2/refs/heads/master/chnroutes.txt -o dependency/chnroutes.txt
	# IPv6 lists
	curl https://raw.githubusercontent.com/gaoyifan/china-operator-ip/refs/heads/ip-lists/china6.txt -o dependency/china6.txt
	curl https://raw.githubusercontent.com/mayaxcn/china-ip-list/refs/heads/master/chnroute_v6.txt -o dependency/chnroute_v6.txt

.PHONY: generate
generate: update-dependency
	python3 generate.py --exclude $(EXCLUDE) --next $(NEXT)

.PHONY: force-push
force-push:
	git add . && git commit --amend --no-edit && git push -f
