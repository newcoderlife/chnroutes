# chnroutes

生成“非中国大陆 IP 段”的 BIRD 3 static route 片段，用来通过 iBGP 分发给
RouterOS client。

生成文件只包含 route 语句，放在 `protocol static` 块内 `include`。它不会生成完整
BIRD 配置，也不会同步 Linux kernel table。

## 用法

下载 route 片段：

```sh
curl -L -o /etc/bird/noncn4.routes \
  https://github.com/newcoderlife/chnroutes/releases/latest/download/noncn4.routes
curl -L -o /etc/bird/noncn6.routes \
  https://github.com/newcoderlife/chnroutes/releases/latest/download/noncn6.routes
```

在 `bird.conf` 里 include：

```bird
ipv4 table noncn4;
ipv6 table noncn6;

protocol static noncn_static4 {
    ipv4 { table noncn4; import all; };
    include "/etc/bird/noncn4.routes";
}

protocol static noncn_static6 {
    ipv6 { table noncn6; import all; };
    include "/etc/bird/noncn6.routes";
}
```

完整示例见 `bird.example.conf`。加载前检查：

```sh
birdc configure check
birdc configure
```

## 本地生成

```sh
make generate
```

会生成：

- `noncn4.routes`
- `noncn6.routes`
- `noncn.sha256`

## 数据来源

- [IANA IPv4 Address Space Registry](https://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.csv)
- [APNIC delegated stats](https://ftp.apnic.net/stats/apnic/delegated-apnic-latest)
- [17mon/china_ip_list](https://github.com/17mon/china_ip_list)
- [gaoyifan/china-operator-ip](https://github.com/gaoyifan/china-operator-ip)
- [misakaio/chnroutes2](https://github.com/misakaio/chnroutes2)
- [mayaxcn/china-ip-list](https://github.com/mayaxcn/china-ip-list)
