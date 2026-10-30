"""Selectively extract current official UI/identity data into research only."""
import json
import os
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
GAME = Path(r'E:\Games\steamapps\common\Age of Empires IV')
TOOL = Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison/bin/sga-archiver.exe'
selected = [('UI.sga','ui/lobby/semimodalpages/createcustommatchsemimodalpage.xaml'),
            ('UI.sga','ui/loading/pages/loadmultiplayerpage.xaml'),
            ('UI.sga','ui/hud/controls/civflagicons.xaml'),
            ('UI.sga','ui/hud/controls/selectioncard.xaml'),
            ('UI.sga','ui/lobby/lobbyresources.xaml'),
            ('Attrib.sga','attrib/racebps/malian.rgd'),
            ('Attrib.sga','attrib/racebps/english.rgd'),
            ('Attrib.sga','attrib/racebps/campaign/bohemia.rgd')]
for archive,member in selected:
    path = OUT/'official'/member
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        res = subprocess.run([str(TOOL),'extract-member',str(GAME/'cardinal/archives'/archive),member,str(path)],capture_output=True,text=True)
        assert res.returncode==0,res.stderr
    if path.suffix=='.rgd':
        decoded = path.with_suffix('.decoded.xml')
        if not decoded.exists():
            res = subprocess.run([str(TOOL),'decode-rgd',str(path),str(decoded)],capture_output=True,text=True)
            assert res.returncode==0,res.stderr
    print('READ',member)

