"""Native SGA resource namespaces are part of the runtime loading contract."""
HOUSE='berber_house_022'
ACTOR='attrib/ebps/races/malian/buildings/building_house_mal.rgd'
def validate_house_namespaces(inventory):
    members={m['path']:m for m in inventory['members']}
    required=[ACTOR]+[f'attrib/attachments/attachment_lists/garrison/{HOUSE}/house_age{a}_tier.rgd' for a in range(1,5)]
    required += [f'art/stamps/garrison/{HOUSE}/house_age{a}.bin' for a in range(1,5)]
    for path in required:
        if path not in members:raise ValueError('missing native house resource '+path)
    for path,m in members.items():
        if path.startswith('attrib/'):expected='attrib'
        elif path.startswith((f'art/scenario/garrison/{HOUSE}/',f'art/stamps/garrison/{HOUSE}/')):expected='data'
        else:continue
        if m['toc']!=expected:raise ValueError(f'{path}: native namespace must be {expected}, found {m["toc"]}')
    return True
