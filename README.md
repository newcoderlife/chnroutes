# chnroutes

为 MikroTik RouterOS v7 生成“非中国大陆 IP 段”的路由脚本。

生成出来的 `noncn.rsc` 会把 IPv4 和 IPv6 的非中国大陆目的地址写入
`noncn` routing table。你可以再配合 RouterOS 的 routing rules，把这些流量
转发到 VPN、WireGuard、旁路网关或另一条 WAN。

## 怎么用

最常见的用法是生成一份路由脚本，然后把非中国大陆流量指向你的 VPN 或
WireGuard 接口：

```sh
make generate NEXT=wg-out
```

这里的 `NEXT` 可以是 RouterOS 接口名，也可以是网关 IP。命令会自动下载最新的
上游 IP 数据并生成 `noncn.rsc`。

## RouterOS

手动导入：

```routeros
/import file-name=noncn.rsc
```

生成的路由会带上 `comment="chnroutes"`。第一次迁移导入时会清理 `noncn`
routing table 里的旧路由；之后再次导入时，只会清理同样带有这个 comment 的路由，
避免误删你手工维护的其它路由。

仓库里的 `cron.rsc` 可以在 RouterOS 上创建一个定时任务，每 12 小时下载并导入
最新 release asset：

```text
https://github.com/newcoderlife/chnroutes/releases/latest/download/noncn.rsc
```

checksum 地址：

```text
https://github.com/newcoderlife/chnroutes/releases/latest/download/noncn.rsc.sha256
```

Release asset 还会发布 GitHub Artifact Attestation。下载 `noncn.rsc` 后可以这样
验证来源：

```sh
gh attestation verify noncn.rsc -R newcoderlife/chnroutes
```

注意：RouterOS 自动下载导入时不会验证 attestation；这个验证适合你在本地或 CI 里
手动确认 release asset 的来源。

## GitHub Actions

`.github/workflows/publish-routes.yml` 会生成并发布最新的 `noncn.rsc` 和
`noncn.rsc.sha256` 到固定的 `latest` release。

触发方式：

- push 到 `master`
- 每天定时运行
- 手动 `workflow_dispatch`

生成产物不会提交回 git 仓库，只发布到 release。

## 维护

校验生成器和最新上游依赖，不写出 `noncn.rsc`：

```sh
make validate
```

`make generate` 和 `make validate` 都会把依赖下载到临时目录，使用后自动删除。
本仓库不再维护上游依赖文件快照。

## 依赖来源

本项目生成路由时会使用以下上游数据：

- IANA IPv4 Address Space Registry:
  https://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.csv
- APNIC delegated stats:
  https://ftp.apnic.net/stats/apnic/delegated-apnic-latest
- 17mon/china_ip_list:
  https://github.com/17mon/china_ip_list
- gaoyifan/china-operator-ip:
  https://github.com/gaoyifan/china-operator-ip
- misakaio/chnroutes2:
  https://github.com/misakaio/chnroutes2
- mayaxcn/china-ip-list:
  https://github.com/mayaxcn/china-ip-list
