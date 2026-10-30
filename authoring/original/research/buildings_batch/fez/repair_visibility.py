from pathlib import Path
p=Path('art/buildings/fez/build_fez.py');s=p.read_text();needle="    rear=box('teaching_hall_rear'"
addition='''    # Exterior zellij-like dado and plaster courses prevent blank institutional side walls.
    for side,x in [('west',-2.15),('east',2.15)]:
        box(side+'_exterior_geometric_dado',(x,0,.66),(.026,3.82,.34),'stone',100)
        for yy in [-1.7+i*.34 for i in range(11)]:
            for z in [.61,.74]:
                o=box(side+'_exterior_ceramic_diamond',(x+(-.018 if x<0 else .018),yy,z),(.018,.095,.095),'clay',100);o.rotation_euler.x=math.pi/4
        box(side+'_exterior_carved_plaster_course',(x,0,1.89),(.030,3.82,.18),'lime',100)
        for yy in [-1.7+i*.34 for i in range(11)]:
            o=box(side+'_exterior_plaster_relief',(x+(-.022 if x<0 else .022),yy,1.89),(.025,.075,.075),'stone',100);o.rotation_euler.x=math.pi/4
'''
s=s.replace(needle,addition+needle).replace('location=(7,-9,8)','location=(6,-8,12)').replace('cam.location=(3,-4,5);cam.data.ortho_scale=4.5','cam.location=(0,-2,7);cam.data.ortho_scale=4.5')
p.write_text(s)
