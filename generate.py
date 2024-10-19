#!/usr/bin/env python3

import argparse
import csv
import math
from ipaddress import IPv4Network

parser = argparse.ArgumentParser(description="Generate non-China routes for RouterOS.")
parser.add_argument(
    "--exclude",
    metavar="CIDR",
    type=str,
    nargs="*",
    help="IPv4 ranges to exclude in CIDR format",
)
parser.add_argument(
    "--next",
    default="%ether1",
    metavar="INTERFACE OR IP",
    help="next hop for where non-China IP address, this is usually the tunnel interface",
)
parser.add_argument(
    "--chn_list",
    default=[
        "dependency/china_ip_list.txt",
        "dependency/china.txt",
        "dependency/chnroutes.txt",
    ],
    nargs="*",
    help="IPv4 lists to use when subtracting China based IP, multiple lists can be used at the same time",
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
if args.exclude:
    for e in args.exclude:
        RESERVED.append(IPv4Network(e))


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

for path in args.chn_list:
    with open(path, "r") as f:
        for line in f:
            if line.strip() == "" or line.startswith("#"):
                continue

            line = line.strip("\n")
            a = IPv4Network(line)
            subtract_cidr(root, (a,))

subtract_cidr(root, RESERVED)

with open("noncn.rsc", "w") as f:
    dump_rsc(root, f)
