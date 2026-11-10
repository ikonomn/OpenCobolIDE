#!/usr/bin/env python3
"""Create source-matched native Fedora/Mageia kits from clean local commits."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--debugger-repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    ide = Path(__file__).resolve().parents[1]
    debugger = args.debugger_repo.resolve()
    revisions = {}
    for label, repo in [('OpenCobolIDE', ide), ('cobgdb-python', debugger)]:
        if git(repo, 'status', '--porcelain'):
            parser.error(f'Commit intended source changes before creating kits: {repo}')
        revisions[label] = git(repo, 'rev-parse', 'HEAD')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='modern12-rpm-kits-') as directory:
        temporary = Path(directory)
        sources = []
        for repo, filename, prefix in [
                (ide, 'opencobolide-4.7.6-modern12.tar.gz', 'OpenCobolIDE-4.7.6-modern12/'),
                (debugger, 'cobgdb-python-0.1.0.tar.gz', 'cobgdb-python-0.1.0/')]:
            archive = temporary/filename
            subprocess.run(['git', '-C', str(repo), 'archive', '--format=tar.gz',
                            '--prefix='+prefix, '-o', str(archive), 'HEAD'], check=True)
            if repo == debugger:
                # Examples are a complete local tree, including ignored runtime data.
                original = archive.read_bytes()
                import io
                with tarfile.open(fileobj=io.BytesIO(original), mode='r:gz') as old, tarfile.open(archive, 'w:gz') as new:
                    for member in old:
                        if member.name == prefix + 'examples' or member.name.startswith(prefix + 'examples/'):
                            continue
                        new.addfile(member, old.extractfile(member) if member.isfile() else None)
                    new.add(repo/'examples', arcname=prefix+'examples')
            sources.append(archive)
            bundle = temporary/(repo.name+'-history.bundle')
            subprocess.run(['git', '-C', str(repo), 'bundle', 'create', str(bundle), 'HEAD'], check=True)
            sources.append(bundle)
        for target, distro in [('fedora44', 'fedora'), ('mageia10', 'mageia')]:
            name = f'modern12-{target}-rpm-kit'
            kit = temporary/name
            kit.mkdir()
            for source in sources:
                shutil.copy2(source, kit/source.name)
            shutil.copy2(ide/f'packaging/{distro}/opencobolide-modern12.spec', kit)
            shutil.copy2(debugger/f'packaging/{distro}/cobgdb-python.spec', kit)
            shutil.copy2(ide/'packaging/build-modern12-rpms.sh', kit/'build-rpms.sh')
            shutil.copy2(ide/'scripts/release_bundle.py', kit/'release_bundle.py')
            shutil.copy2(ide/'packaging/RPM_MODERN12.md', kit/'README.md')
            (kit/'TARGET').write_text(target+'\n')
            (kit/'SOURCE_REVISIONS.json').write_text(json.dumps(revisions, indent=2)+'\n')
            checksums = []
            for file in sorted(kit.iterdir()):
                checksums.append(hashlib.sha256(file.read_bytes()).hexdigest()+'  '+file.name)
            (kit/'SHA256SUMS').write_text('\n'.join(checksums)+'\n')
            artifact = output/(name+'.tar.gz')
            with tarfile.open(artifact, 'w:gz') as archive:
                archive.add(kit, arcname=name)
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            Path(str(artifact)+'.sha256').write_text(digest+'  '+artifact.name+'\n')
            print(artifact)


if __name__ == '__main__':
    main()
