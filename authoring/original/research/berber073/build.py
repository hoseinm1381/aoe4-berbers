"""Progress-only update of the retained working native installation route."""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'research'))
from berber070_package import sha,verify,put
SOURCE=ROOT/'output/berber_update_0_7_2'
OUT=ROOT/'output/berber_update_0_7_3'
PROGRESS=r'''
$ProgressPreference = 'Continue'
$script:VoiceStage = ''
$script:VoiceLastUpdate = [datetime]::MinValue
function Voice-Progress([string]$Stage,[int]$Done,[int]$Total) {
    $now = [datetime]::UtcNow
    if ($Stage -eq $script:VoiceStage -and $Done -ne $Total -and
        ($now - $script:VoiceLastUpdate).TotalSeconds -lt 1) { return }
    $script:VoiceStage = $Stage
    $script:VoiceLastUpdate = $now
    $percent = if ($Total -gt 0) { [int][math]::Floor(100.0*$Done/$Total) } else { 0 }
    $filled = [int][math]::Floor($percent/5)
    $status = ('[' + ('#' * $filled) + ('-' * (20-$filled)) + '] ' + $percent + '%  ' + $Done + '/' + $Total)
    Write-Progress -Id 73 -Activity ('Berber voices: '+$Stage) -Status $status -PercentComplete $percent
    # Persistent text also works in hosts that do not render Write-Progress.
    [Console]::Error.WriteLine(($Stage+' '+$status))
    if ($Done -eq $Total) { Write-Progress -Id 73 -Activity 'Berber voices' -Completed }
}
'''
def enhance(text):
 if 'Voice-Progress' in text:raise ValueError('Already patched')
 text=text.replace("$NewOwned =",PROGRESS+"\n$NewOwned =",1)
 text=text.replace('    foreach ($file in @($Files)) {',"    $progressIndex=0; $progressTotal=@($Files).Count\n    $progressStage=if($Sources){'Validating package'}else{'Reading installed inventory'}\n    Voice-Progress $progressStage 0 $progressTotal\n    foreach ($file in @($Files)) {\n        Voice-Progress $progressStage $progressIndex $progressTotal\n        $progressIndex++",1)
 text=text.replace("    if ($rows.Count -eq 0)","    Voice-Progress $progressStage $progressTotal $progressTotal\n    if ($rows.Count -eq 0)",1)
 marker='        foreach ($row in $rows) {'
 text=text.replace(marker,"        $progressIndex=0; Voice-Progress $Action 0 $rows.Count\n"+marker+"\n            Voice-Progress $Action $progressIndex $rows.Count; $progressIndex++",1)
 text=text.replace('        if ($issues.Count -gt 0)',"        Voice-Progress $Action $rows.Count $rows.Count\n        if ($issues.Count -gt 0)",1)
 marker='    # No destination is changed until every package payload and conflict passes.'
 text=text.replace(marker,marker+"\n    $progressIndex=0; Voice-Progress 'Checking destination conflicts' 0 $rows.Count",1)
 marker='    foreach ($row in $rows) {'
 # Match only the two loops at exactly four spaces, not Verify's nested loop.
 text=text.replace('\n'+marker,'\n'+marker+"\n        Voice-Progress 'Checking destination conflicts' $progressIndex $rows.Count; $progressIndex++",1)
 text=text.replace('    $firstNewByHash =',"    Voice-Progress 'Checking destination conflicts' $rows.Count $rows.Count\n    $progressIndex=0; Voice-Progress 'Installing files' 0 $rows.Count\n    $firstNewByHash =",1)
 marker='    foreach ($row in $rows) {\n        Assert-NoReparse'
 text=text.replace(marker,"    foreach ($row in $rows) {\n        Voice-Progress 'Installing files' $progressIndex $rows.Count; $progressIndex++\n        Assert-NoReparse",1)
 text=text.replace('    $savedFiles =',"    Voice-Progress 'Installing files' $rows.Count $rows.Count\n    [Console]::Error.WriteLine('Saving installation ownership state...')\n    $savedFiles =",1)
 text=text.replace('    $failure = $_.Exception.Message',"    Write-Progress -Id 73 -Activity 'Berber voices' -Completed\n    $failure = $_.Exception.Message\n    [Console]::Error.WriteLine('Operation failed; checking rollback and temporary files...')",1)
 for stage in ('Validating package','Reading installed inventory','Checking destination conflicts','Installing files'):
  if stage not in text:raise ValueError('Missing stage')
 return text
def build():
 if not (SOURCE/'Berber-0.7.2-MAIN-GARRISON.zip').exists():
  raise RuntimeError('Historical ZIP chain retired. For a new release use research/next_release.py --version X.Y.Z --summary "Changes" --sga <validated.sga>; see REBUILD_NEXT.md.')
 OUT.mkdir(exist_ok=True)
 reports={}
 for kind in ('MAIN-GARRISON','VOICES-INSTALLER'):
  target=OUT/('Berber-0.7.3-'+kind+'.zip')
  if target.exists():raise FileExistsError('Existing delivery retained')
  expected={}
  with zipfile.ZipFile(SOURCE/('Berber-0.7.2-'+kind+'.zip')) as old,zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   for item in old.infolist():
    data=old.read(item)
    if item.filename=='garrison.json':
     m=json.loads(data);m['details']['version']='0.7.3';m['details']['summary']='Native voices with visible installer progress';m['details']['description']=m['details']['description'].replace('0.7.2','0.7.3');m['details']['changelog']='Installer progress bars, stage labels and processed-file counts; working 0.7.0 game content retained.';data=(json.dumps(m,indent=2)+'\n').encode()
    elif item.filename.endswith('/Install-BerberNativeAudio.ps1'):
     data=enhance(data.decode('utf-8-sig')).encode('utf-8-sig')
     source=ROOT/'research/berber073'/item.filename.split('/')[0]/'Install-BerberNativeAudio.ps1';source.parent.mkdir(exist_ok=True);source.write_bytes(data)
    elif item.filename=='Setup-BerberVoices.ps1':
     s=data.decode('utf-8-sig').replace('0.7.2','0.7.3')
     s=s.replace('    foreach($part in $parts) {',"    $componentIndex=0\n    foreach($part in $parts) {\n        $componentIndex++\n        Write-Host ('=== Component '+$componentIndex+'/'+$parts.Count+': '+$part+' / '+$Action+' ===')")
     s=s.replace("    Write-Host 'Completed.","    Write-Host 'Completed.")
     data=s.encode('utf-8-sig')
    elif item.filename=='START-HERE.txt':
     data=data.replace(b'0.7.2',b'0.7.3')+b'\nProgress: each stage displays a bar, percentage, and processed/total files.\nStages restart at 0% for each component and operation; this is normal.\n'
    put(z,item.filename,data,expected)
  reports[kind]=verify(target,expected)
 result=dict(status='ZIP_member_hashes_and_CRC_passed',version='0.7.3',packages=reports,game_content='Unchanged working 0.7.0 archive',recordings='Unchanged',installed_game_modified=False,cleanup='No staging, cook or readback copies created; retained deliverables, scripts and compact evidence')
 (OUT/'release-validation.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:{f:r[f] for f in ('zip','bytes','sha256')} for k,r in reports.items()}),flush=True)
if __name__=='__main__':build()
