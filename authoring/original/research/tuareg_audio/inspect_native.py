"""Read selected current-game speech/attribute metadata; never change game files."""
from pathlib import Path
import os
import subprocess
import re
import sqlite3

root = Path(__file__).resolve().parent
game = Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal')
tool = Path(os.environ['APPDATA']) / r'Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com\garrison\bin\sga-archiver.exe'
selected = [('Data.sga','statetrees/speech/statetree.bin','speech-statetree.bin'),
            ('Data.sga','audio/soundbanks.lua','soundbanks.lua'),
            ('Data.sga','audio/wwiseconfig.lua','wwiseconfig.lua'),
            ('Attrib.sga','attrib/ebps/races/malian/units/unit_spearman_1_mal.rgd','stock-donso-ebps.rgd'),
            ('Attrib.sga','attrib/sbps/races/malian/unit_spearman_1_mal.rgd','stock-donso-sbps.rgd'),
            ('Attrib.sga','attrib/ebps/races/core/units/unit_spearman_1.rgd','core-spearman-ebps.rgd'),
            ('Attrib.sga','attrib/sbps/races/core/unit_spearman_1.rgd','core-spearman-sbps.rgd')]
for archive,member,name in selected:
    output=root/name
    if not output.exists():
        result=subprocess.run([str(tool),'extract-member',str(game/'archives'/archive),member,str(output)],capture_output=True,text=True)
        if result.returncode:
            print('FAIL',member,result.stderr[:200]); continue
    print('READ',name,output.stat().st_size)
    if name.endswith('.rgd'):
        xml=output.with_suffix('.decoded.xml')
        if not xml.exists():
            result=subprocess.run([str(tool),'decode-rgd',str(output),str(xml)],capture_output=True,text=True)
            if result.returncode: print('DECODE FAIL',name,result.stderr[:200])
speech=root/'speech-statetree.bin'
strings=[s.decode('ascii') for s in re.findall(rb'[\x20-\x7e]{4,}',speech.read_bytes())]
(root/'speech-statetree-strings.txt').write_text('\n'.join(strings),encoding='utf-8')
print('speech strings',len(strings))
db=Path(os.environ['LOCALAPPDATA'])/'Garrison'/'Kit'/'game-assets.sqlite3'
with sqlite3.connect('file:'+db.as_posix()+'?mode=ro',uri=True) as conn:
    tables=conn.execute("select name from sqlite_master where type='table'").fetchall()
    print('Game index tables:',tables)
