#!/usr/bin/env python3

import argparse
import csv
import math
from ipaddress import IPv4Network, IPv6Network, ip_network

parser = argparse.ArgumentParser(
    description="Generate non-China IPv4/IPv6 routes for RouterOS."
)
parser.add_argument(
    "--exclude",
    metavar="CIDR",
    type=str,
    nargs="*",
    help="Extra IPv4/IPv6 CIDR prefixes to keep local (excluded from output)",
)
parser.add_argument(
    "--next",
    default="%ether1",
    metavar="INTERFACE OR IP",
    help="next hop for non-China IPv4/IPv6; typically your tunnel interface or gateway",
)
parser.add_argument(
    "--next6",
    default=None,
    metavar="INTERFACE OR IP",
    help="next hop for non-China IPv6; overrides --next when set",
)
parser.add_argument(
    "--chn_list",
    default=[
        "dependency/china_ip_list.txt",
        "dependency/china.txt",
        "dependency/chnroutes.txt",
        "dependency/china6.txt",
        "dependency/chnroute_v6.txt",
    ],
    nargs="*",
    help="China IP lists (IPv4/IPv6). Each line is a CIDR. Blank lines are ignored. Multiple files supported.",
)
args = parser.parse_args()


class Node:
    def __init__(self, cidr, parent=None):
        self.cidr = cidr
        self.child = []
        self.dead = False
        self.parent = parent

    def __repr__(self):
        return "<Node %s>" % self.cidr


def dump_tree(lst, ident=0):
    for n in lst:
        print("+" * ident + str(n))
        dump_tree(n.child, ident + 1)


def dump_rsc(lst, f):
    f.write(
        ':foreach routeId in=[/ip/route/find where routing-table="noncn"] do={\n/ip/route/remove ($routeId)\n}\n'
    )

    dump_rds_inner(lst, f)


def dump_rds_inner(lst, f):
    for n in lst:
        if n.dead:
            continue

        if len(n.child) > 0:
            dump_rds_inner(n.child, f)
        elif not n.dead:
            f.write(
                "/ip/route/add distance=10 dst-address=%s gateway=%s routing-table=noncn\n"
                % (n.cidr, args.next)
            )


def dump_rsc6(lst, f):
    f.write(
        ':foreach routeId in=[/ipv6/route/find where routing-table="noncn"] do={\n/ipv6/route/remove ($routeId)\n}\n'
    )

    dump_rds6_inner(lst, f)


def dump_rds6_inner(lst, f):
    for n in lst:
        if n.dead:
            continue

        if len(n.child) > 0:
            dump_rds6_inner(n.child, f)
        elif not n.dead:
            nh = args.next6 if args.next6 is not None else args.next
            f.write(
                "/ipv6/route/add distance=10 dst-address=%s gateway=%s routing-table=noncn\n"
                % (n.cidr, nh)
            )


RESERVED = [
    IPv4Network("0.0.0.0/8"),
    IPv4Network("10.0.0.0/8"),
    IPv4Network("127.0.0.0/8"),
    IPv4Network("169.254.0.0/16"),
    IPv4Network("172.16.0.0/12"),
    IPv4Network("192.0.0.0/29"),
    IPv4Network("192.0.0.170/31"),
    IPv4Network("192.0.2.0/24"),
    IPv4Network("192.168.0.0/16"),
    IPv4Network("198.18.0.0/15"),
    IPv4Network("198.51.100.0/24"),
    IPv4Network("203.0.113.0/24"),
    IPv4Network("240.0.0.0/4"),
    IPv4Network("255.255.255.255/32"),
    IPv4Network("169.254.0.0/16"),
    IPv4Network("127.0.0.0/8"),
    IPv4Network("224.0.0.0/4"),
    IPv4Network("100.64.0.0/10"),
]

RESERVED6 = [
    IPv6Network("::/128"),
    IPv6Network("::1/128"),
    IPv6Network("::ffff:0:0/96"),
    IPv6Network("64:ff9b::/96"),
    IPv6Network("100::/64"),
    IPv6Network("2001:db8::/32"),
    IPv6Network("2001:2::/48"),
    IPv6Network("2001:10::/28"),
    IPv6Network("2001:20::/28"),
    IPv6Network("2001:0::/32"),  # Teredo
    IPv6Network("2002::/16"),  # 6to4
    IPv6Network("fc00::/7"),
    IPv6Network("fe80::/10"),
    IPv6Network("ff00::/8"),
]


def subtract_cidr(sub_from, sub_by):
    for cidr_to_sub in sub_by:
        for n in sub_from:
            if n.cidr == cidr_to_sub:
                n.dead = True
                break

            if n.cidr.supernet_of(cidr_to_sub):
                if len(n.child) > 0:
                    subtract_cidr(n.child, sub_by)

                else:
                    n.child = [Node(b, n) for b in n.cidr.address_exclude(cidr_to_sub)]

                break


root = []

# IPv6 universe root (define before use)
root6 = [Node(IPv6Network("2000::/3"))]

with open("dependency/ipv4-address-space.csv", newline="") as f:
    f.readline()  # skip the title

    reader = csv.reader(f, quoting=csv.QUOTE_MINIMAL)
    for cidr in reader:
        if cidr[5] == "ALLOCATED" or cidr[5] == "LEGACY":
            block = cidr[0]
            cidr = "%s.0.0.0%s" % (
                block[:3].lstrip("0"),
                block[-2:],
            )
            root.append(Node(IPv4Network(cidr)))

with open("dependency/delegated-apnic-latest") as f:
    for line in f:
        if "apnic|CN|ipv4|" in line:
            line = line.split("|")
            a = "%s/%d" % (
                line[3],
                32 - math.log(int(line[4]), 2),
            )
            a = IPv4Network(a)
            subtract_cidr(root, (a,))
        elif "apnic|CN|ipv6|" in line:
            line = line.split("|")
            # For IPv6 in delegated files, value is prefix length
            a6 = f"{line[3]}/{int(line[4])}"
            a6 = IPv6Network(a6)
            subtract_cidr(root6, (a6,))


all_lists = []
if args.chn_list:
    all_lists.extend(args.chn_list)

# de-duplicate while preserving order
seen = set()
dedup_lists = []
for p in all_lists:
    if p not in seen:
        dedup_lists.append(p)
        seen.add(p)

for path in dedup_lists:
    with open(path, "r") as f:
        for line in f:
            s = line.strip()
            if s == "" or s.startswith("#"):
                continue

            net = ip_network(s, strict=True)
            if isinstance(net, IPv4Network):
                subtract_cidr(root, (net,))
            else:
                subtract_cidr(root6, (net,))

extra_excludes = []
if args.exclude:
    extra_excludes.extend(args.exclude)

for e in extra_excludes:
    net = ip_network(e, strict=True)
    if isinstance(net, IPv4Network):
        RESERVED.append(net)
    else:
        RESERVED6.append(net)

subtract_cidr(root, RESERVED)

subtract_cidr(root6, RESERVED6)

with open("noncn.rsc", "w") as f:
    dump_rsc(root, f)
    dump_rsc6(root6, f)
