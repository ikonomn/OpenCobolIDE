# modern11.6 local validation — 2026-10-23

The functional fix was transferred from reviewed commit 21214f3 into this
repository as 92ccdcc. This preparation changes the display/package version,
Help references and release documentation to modern11.6.

- Complete test suite on an isolated copy of this modern11.6 tree: 112 passed.
  Qt offscreen/Fusion, isolated settings/cache, local backend sockets enabled.
- Built with `bash scripts/make_deb.sh`, without installation.
- Debian metadata verified: opencobolide, 4.7.6+modern11.6, Architecture all.
- Extracted package: display version, runtime-diagnostics fix, manual title
  and executable launcher permissions verified.
- All 230 packaged Python source files parsed without syntax errors.
- No push or system installation performed.

Package SHA-256:
`f76b5d3b0b56503750d2378a1d6218564316a1114091b611c82131509809798b`

Distribution artifact: `dist/opencobolide_4.7.6+modern11.6_all.deb`.
Logs and XML from the test copy: `/tmp/ocide-modern116-review/` (temporary).
Desktop installation and user acceptance testing remain pending. Scrolling and
tooltip reports remain unconfirmed; no fix for them is claimed.
