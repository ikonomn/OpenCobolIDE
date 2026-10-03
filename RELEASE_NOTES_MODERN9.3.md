# OpenCobolIDE 4.7.6+modern9.3

This update makes installation friendlier for people who compile GnuCOBOL
from source.

The Debian package now recommends `gnucobol` instead of requiring Ubuntu's
package. A normal installation still installs the recommended compiler. If
`cobc` is already installed from source, install OpenCobolIDE without a second
compiler using:

```sh
sudo apt install --no-install-recommends \
    ./opencobolide_4.7.6+modern9.3_all.deb
```

Check which compiler OpenCobolIDE will find with:

```sh
command -v cobc
cobc --version
```

## Package checksum

```text
SHA-256: 76081d2d577cef0971416c3d53913a6f4b4bbe6a118426715f717d6fac76af3f
```

This is an unofficial maintenance build of OpenCobolIDE 4.7.6.
