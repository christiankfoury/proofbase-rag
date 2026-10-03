"""Compare all frozen files to committed blobs in one read-only Git batch."""
import hashlib
import subprocess


def verify_bindings(root,commit,bindings):
    paths=list(bindings)
    refs=''.join(commit+':'+p+'\n' for p in paths).encode()
    output=subprocess.check_output(['git','cat-file','--batch'],input=refs,cwd=root)
    position=0
    for path in paths:
        end=output.index(b'\n',position);header=output[position:end].split()
        if len(header)!=3 or header[1]!=b'blob':raise ValueError('Missing frozen committed blob: '+path)
        size=int(header[2]);blob=output[end+1:end+1+size];position=end+size+2
        normalized=blob.replace(b'\r\n',b'\n');expected=bindings[path]
        hashes={hashlib.sha256(v).hexdigest() for v in (blob,normalized,normalized.replace(b'\n',b'\r\n'))}
        if expected not in hashes:
            current=(root/path).read_bytes()
            if hashlib.sha256(current).hexdigest()!=expected or current.replace(b'\r\n',b'\n')!=normalized:
                raise ValueError('Frozen source differs: '+path)
    if position!=len(output):raise ValueError('Unexpected Git batch data')
