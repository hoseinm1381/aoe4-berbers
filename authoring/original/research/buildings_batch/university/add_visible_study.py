from pathlib import Path
p=Path('art/buildings/university/build_university.py');s=p.read_text();mark='    # Conservative clear source courtyard and entry route, not a navmesh.'
insert='''    # Two visible courtyard reading stations keep the central passage open.
    for x in [-1.20,1.20]:
        pedestal=box('court_reading_pedestal',(x,-1.65,.46),(.20,.38,.60),'cedar',60);contact(pedestal.name,'scholar_court_foundation')
        desk=box('court_reading_desk',(x,-1.65,.80),(.46,.72,.08),'cedar',80);contact(desk.name,pedestal.name)
        for dx in [-.095,.095]:
            page=box('open_manuscript_pages',(x+dx,-1.65,.862),(.18,.36,.044),'straw',100);contact(page.name,desk.name)
        box('manuscript_binding_spine',(x,-1.65,.858),(.03,.37,.036),'clay',100)
        for yy in [-1.0,-2.30]:
            stool=box('court_reader_stool',(x,yy,.34),(.30,.28,.36),'cedar',80);contact(stool.name,'scholar_court_foundation')
'''
s=s.replace(mark,insert+mark);p.write_text(s)
