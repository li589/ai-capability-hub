#!/usr/bin/env python3
import base64,pathlib,zlib
_p=pathlib.Path(__file__)
_s=zlib.decompress(base64.b85decode(_p.with_suffix(_p.suffix+'.b85').read_bytes()))
exec(compile(_s,str(_p),'exec'),globals(),globals())
