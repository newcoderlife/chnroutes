# chnroutes

Generate MikroTik RouterOS v7 routes for non-China IPv4 and IPv6 destinations.

The generated `noncn.rsc` script writes routes into the `noncn` routing table.
Those routes can then be used by RouterOS routing rules to send non-China
traffic through a tunnel, VPN gateway, or alternate WAN.

Forked from https://github.com/dndx/nchnroutes.

## Usage

Generate with the latest upstream dependency lists:

```sh
make generate NEXT=wg-out
```

Create a checksum for the generated script:

```sh
make checksum
```

Generate from the dependency files already checked into this repository:

```sh
make generate-local NEXT=wg-out
```

Keep additional prefixes local by excluding them from the non-China output:

```sh
make generate-local NEXT=wg-out EXCLUDE="8.8.8.0/24 2001:4860:4860::/48"
```

Use a separate IPv6 next hop when needed:

```sh
make generate-local NEXT=wg-out NEXT6="fe80::1%ether1"
```

## RouterOS

Import the generated script on RouterOS:

```routeros
/import file-name=noncn.rsc
```

The generated routes are tagged with `comment="chnroutes"`. After the first
migration import, future imports remove only routes with that comment instead
of clearing every route in the `noncn` table.

`cron.rsc` installs a RouterOS scheduler that fetches and imports the latest
`noncn.rsc` release asset every 12 hours. The stable download URL is:

```text
https://github.com/newcoderlife/chnroutes/releases/latest/download/noncn.rsc
```

The checksum is published at:

```text
https://github.com/newcoderlife/chnroutes/releases/latest/download/noncn.rsc.sha256
```

Release assets are also published with GitHub Artifact Attestations. After
downloading `noncn.rsc`, verify its provenance with:

```sh
gh attestation verify noncn.rsc -R newcoderlife/chnroutes
```

## Maintenance

Validate the current dependency files without writing `noncn.rsc`:

```sh
make validate
```

`make generate` downloads dependency files to a temporary directory, validates
them, and only then replaces the checked-in files. This avoids replacing a good
dependency file with a failed or malformed download.

GitHub Actions publishes the generated `noncn.rsc` and `noncn.rsc.sha256` files
to a fixed `latest` release with a provenance attestation. The generated route
script is not committed back to the repository.
