[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/cloudhop.svg)](https://pypi.org/project/cloudhop/)
[![GitHub stars](https://img.shields.io/github/stars/husamsoboh-cyber/cloudhop.svg?style=social)](https://github.com/husamsoboh-cyber/cloudhop)

# CloudHop - Free Cloud File Transfer

**Switching cloud providers? CloudHop copies everything for you. Free, open source, runs on your machine.**

![CloudHop Dashboard](screenshots/dashboard.png)

## Download / Install

**Mac** - Download `CloudHop.dmg` from [Releases](https://github.com/husamsoboh-cyber/cloudhop/releases)

**Windows** - Download `CloudHop-Setup.exe` from [Releases](https://github.com/husamsoboh-cyber/cloudhop/releases)

**pip**
```bash
pip install cloudhop && cloudhop
```

**From source**
```bash
git clone https://github.com/husamsoboh-cyber/cloudhop && cd cloudhop && pip install -e . && cloudhop
```

## Why CloudHop?

- **Free and open source** -- no limits, no account needed
- **Runs on your machine** -- files never touch our servers
- **Works with 70+ cloud providers** -- Google Drive, OneDrive, Dropbox, iCloud, MEGA, S3, Proton Drive...
- **Visual wizard** -- no command line needed
- **Pause and resume** across restarts

## How is this different from...

**rclone?**
CloudHop uses rclone as its engine. If you're comfortable with CLI, you don't need this. CloudHop adds a visual wizard and live dashboard.

**MultCloud / CloudFuze?**
Those are paid SaaS that route files through their servers. CloudHop is free and your files transfer directly between providers.

**Download and re-upload?**
That requires local disk space and 2x transfer time. CloudHop uses server-side copy where supported.

## How it works

1. **Run CloudHop** -- launch the app or run `cloudhop` in a terminal
2. **Pick source** -- choose where your files are (e.g., OneDrive)
3. **Pick destination** -- choose where to copy them (e.g., Google Drive)
4. **Configure options** -- set parallel transfers, exclude folders, limit bandwidth
5. **Connect accounts** -- authorize each cloud provider in your browser
6. **Start transfer** -- watch progress in the live dashboard with speed charts and ETA

## CLI Usage

```bash
cloudhop source: dest: [--transfers=8] [--bwlimit=10M] [--exclude="*.tmp"]
```

## Supported Providers

Google Drive, OneDrive, Dropbox, iCloud Drive, MEGA, Amazon S3, Proton Drive, Local Folder + 70 more via rclone

## Links

[Security](SECURITY.md) | [Contributing](CONTRIBUTING.md) | [Changelog](CHANGELOG.md)

## Built by

Built by an orthodontist who needed to move 500GB between cloud services and found no free, simple tool to do it.

## Donate

If CloudHop saved you time, consider supporting development:

[GitHub Sponsors](https://github.com/sponsors/husamsoboh-cyber) | [Buy Me a Coffee](https://buymeacoffee.com/husamsoboh)

## License

MIT License -- see [LICENSE](LICENSE) for details.
