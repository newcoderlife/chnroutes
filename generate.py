#!/usr/bin/env python3

import argparse
import csv
from ipaddress import IPv4Network, IPv6Network, collapse_addresses, ip_network
from pathlib import Path


DEFAULT_IPV4_SPACE = "ipv4-address-space.csv"
DEFAULT_APNIC = "delegated-apnic-latest"
DEFAULT_CHN_LISTS = [
    "china_ip_list.txt",
    "china.txt",
    "chnroutes.txt",
    "china6.txt",
    "chnroute_v6.txt",
]


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
    IPv4Network("224.0.0.0/4"),
    IPv4Network("240.0.0.0/4"),
    IPv4Network("255.255.255.255/32"),
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
    IPv6Network("2001:0::/32"),
    IPv6Network("2002::/16"),
    IPv6Network("fc00::/7"),
    IPv6Network("fe80::/10"),
    IPv6Network("ff00::/8"),
]


class Node:
    def __init__(self, cidr, parent=None):
        self.cidr = cidr
        self.child = []
        self.dead = False
        self.parent = parent

    def __repr__(self):
        return f"<Node {self.cidr}>"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate non-China IPv4/IPv6 routes for BIRD 3."
    )
    parser.add_argument(
        "--exclude",
        metavar="CIDR",
        type=str,
        nargs="*",
        default=[],
        help="extra IPv4/IPv6 CIDR prefixes to keep local",
    )
    parser.add_argument(
        "--output-prefix",
        default="noncn",
        help="output file prefix",
    )
    parser.add_argument(
        "--dependency-dir",
        default="dependency",
        help="base directory for dependency files",
    )
    parser.add_argument(
        "--ipv4-space",
        default=DEFAULT_IPV4_SPACE,
        help="IANA IPv4 address space CSV",
    )
    parser.add_argument(
        "--apnic",
        default=DEFAULT_APNIC,
        help="APNIC delegated stats file",
    )
    parser.add_argument(
        "--chn-list",
        default=DEFAULT_CHN_LISTS,
        nargs="*",
        help="China IP lists. Each non-comment line must be a CIDR.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="parse and validate dependency data without writing output",
    )
    return parser.parse_args()


def validate_args(args):
    args.output_prefix = args.output_prefix.strip()

    if not args.output_prefix:
        raise ValueError("--output-prefix must not be empty")


def resolve_dependency(path, dependency_dir):
    path = Path(path)
    if path.is_absolute():
        return path

    base = Path(dependency_dir)
    if base == Path("."):
        return path

    if path.parts and path.parts[0] == "dependency":
        return base.joinpath(*path.parts[1:])
    return base / path


def prefix_from_count(count):
    if count <= 0 or count & (count - 1):
        raise ValueError(f"IPv4 allocation size must be a power of two: {count}")
    return 32 - (count.bit_length() - 1)


def load_ipv4_roots(path):
    roots = []
    with open(path, newline="") as f:
        reader = csv.reader(f, quoting=csv.QUOTE_MINIMAL)
        next(reader, None)
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 6:
                raise ValueError(f"{path}:{row_num}: expected at least 6 columns")

            status = row[5].strip().upper()
            if status not in {"ALLOCATED", "LEGACY"}:
                continue

            prefix = row[0].strip()
            block, prefix_len = prefix.split("/", 1)
            cidr = f"{int(block)}.0.0.0/{int(prefix_len)}"
            roots.append(Node(IPv4Network(cidr)))
    return roots


def load_apnic_cn(path):
    v4 = []
    v6 = []
    with open(path) as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("|")
            if len(parts) < 7:
                continue
            registry, country, resource_type = parts[:3]
            if registry != "apnic" or country != "CN":
                continue

            if resource_type == "ipv4":
                prefix = prefix_from_count(int(parts[4]))
                v4.append(IPv4Network(f"{parts[3]}/{prefix}"))
            elif resource_type == "ipv6":
                v6.append(IPv6Network(f"{parts[3]}/{int(parts[4])}"))
    return v4, v6


def read_cidr_file(path):
    networks = []
    with open(path) as f:
        for line_num, line in enumerate(f, start=1):
            cidr = line.split("#", 1)[0].strip()
            if not cidr:
                continue
            try:
                networks.append(ip_network(cidr, strict=True))
            except ValueError as exc:
                raise ValueError(f"{path}:{line_num}: invalid CIDR {cidr}: {exc}")
    return networks


def dedupe_paths(paths):
    seen = set()
    result = []
    for path in paths:
        if path not in seen:
            result.append(path)
            seen.add(path)
    return result


def subtract_network(nodes, cidr_to_sub):
    changed = False
    for node in nodes:
        if node.dead or node.cidr.version != cidr_to_sub.version:
            continue

        if node.cidr == cidr_to_sub or cidr_to_sub.supernet_of(node.cidr):
            node.dead = True
            changed = True
            continue

        if node.cidr.supernet_of(cidr_to_sub):
            if node.child:
                return subtract_network(node.child, cidr_to_sub)

            node.child = [Node(cidr, node) for cidr in node.cidr.address_exclude(cidr_to_sub)]
            return True
    return changed


def collect_live_networks(nodes):
    for node in nodes:
        if node.dead:
            continue
        if node.child:
            yield from collect_live_networks(node.child)
        else:
            yield node.cidr


def build_routes(args):
    dependency_dir = args.dependency_dir
    ipv4_space = resolve_dependency(args.ipv4_space, dependency_dir)
    apnic = resolve_dependency(args.apnic, dependency_dir)
    chn_lists = [resolve_dependency(path, dependency_dir) for path in args.chn_list]

    roots_v4 = load_ipv4_roots(ipv4_space)
    roots_v6 = [Node(IPv6Network("2000::/3"))]

    exclude_v4, exclude_v6 = load_apnic_cn(apnic)

    for path in dedupe_paths(chn_lists):
        for network in read_cidr_file(path):
            if isinstance(network, IPv4Network):
                exclude_v4.append(network)
            else:
                exclude_v6.append(network)

    for raw in args.exclude:
        network = ip_network(raw, strict=True)
        if isinstance(network, IPv4Network):
            exclude_v4.append(network)
        else:
            exclude_v6.append(network)

    exclude_v4.extend(RESERVED)
    exclude_v6.extend(RESERVED6)

    for network in collapse_addresses(exclude_v4):
        subtract_network(roots_v4, network)
    for network in collapse_addresses(exclude_v6):
        subtract_network(roots_v6, network)

    routes_v4 = list(collapse_addresses(collect_live_networks(roots_v4)))
    routes_v6 = list(collapse_addresses(collect_live_networks(roots_v6)))
    return routes_v4, routes_v6


def output_paths(prefix):
    return {
        "routes4": Path(f"{prefix}4.routes"),
        "routes6": Path(f"{prefix}6.routes"),
    }


def write_bird_routes(path, routes, family):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write("# Generated by chnroutes. Do not edit manually.\n")
        f.write(f"# Include inside a BIRD static {family} protocol block.\n")
        for route in routes:
            f.write(f"route {route} unreachable;\n")


def write_outputs(routes_v4, routes_v6, args):
    paths = output_paths(args.output_prefix)
    write_bird_routes(paths["routes4"], routes_v4, "IPv4")
    write_bird_routes(paths["routes6"], routes_v6, "IPv6")


def main():
    args = parse_args()
    try:
        validate_args(args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    routes_v4, routes_v6 = build_routes(args)

    if args.validate_only:
        print(
            f"Validated dependencies: {len(routes_v4)} IPv4 routes, "
            f"{len(routes_v6)} IPv6 routes."
        )
        return

    write_outputs(routes_v4, routes_v6, args)
    print(
        f"Generated {len(routes_v4)} IPv4 routes and {len(routes_v6)} IPv6 routes "
        f"with prefix {args.output_prefix}."
    )


if __name__ == "__main__":
    main()
