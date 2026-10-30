from pathlib import Path
p=Path('art/buildings/market/build_market.py');s=p.read_text().replace("inner+(.45 if x<0 else -.45)","inner+(.375 if x<0 else -.375)").replace("inner+(.46 if x<0 else -.46)","inner+(.375 if x<0 else -.375)")
needle='        # outward shutters are cut pockets; street goods are kept out of central transit lane.'
patch='''        # Exterior warehouse ventilation is carved into the mass, not floating facade decals.
        for yy in [-1.8,.15,2.1]:
            xx=x+(-.78 if x<0 else .78)
            cutter=box('TEMP_lower_window',(xx,yy,1.43),(.34,.68,.70),'shadow',80)
            target=bpy.data.objects[side+'_warehouse'];bpy.context.view_layer.objects.active=target;mo=target.modifiers.new('warehouse_opening','BOOLEAN');mo.operation='DIFFERENCE';mo.object=cutter;bpy.ops.object.modifier_apply(modifier=mo.name);bpy.data.objects.remove(cutter,do_unlink=True);PARTS.pop()
            box(side+'_lower_cedar_shutter',(xx+(.11 if x<0 else -.11),yy,1.43),(.05,.66,.68),'cedar',80)
            for dy in [-.21,0,.21]:box(side+'_shutter_joinery',(xx+(.08 if x<0 else -.08),yy+dy,1.43),(.035,.028,.60),'straw',100)
            box(side+'_window_sill',(xx,yy,1.03),(.24,.80,.10),'stone',80)
            box(side+'_drain_spout',(xx+(-.10 if x<0 else .10),yy,.19+h+.12),(.38,.10,.10),'cedar',80)
        for yy in [-2.77,3.55]:
            box(side+'_buttress',(x+(-.66 if x<0 else .66),yy,.19+h*.44),(.24,.24,h*.88),wall,40)
'''
s=s.replace(needle,patch+needle)
s=s.replace("CONTACTS.append({'interface':side+' awning post top to canopy underside','measured_signed_gap':-.01,'allowed_overlap':.01,'pass':True})", "post=bpy.data.objects[side+'_shade_post'];bpy.context.view_layer.update();gap=bounds(canopy)[0][2]-bounds(post)[1][2];CONTACTS.append({'interface':side+' canopy to post','measured_signed_gap':gap,'expected':-.02,'pass':abs(gap+.02)<1e-5})")
s=s.replace('scene.render.resolution_x=400;scene.render.resolution_y=400','scene.cycles.samples=4;scene.render.resolution_x=256;scene.render.resolution_y=256')
p.write_text(s)
