import bpy, time
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.device='CPU'
sc.cycles.samples=64; sc.cycles.use_denoising=True
sc.render.resolution_x=1440; sc.render.resolution_y=1080
bpy.ops.mesh.primitive_plane_add(size=4); 
bpy.ops.mesh.primitive_cube_add(size=0.3, location=(0,0,0.02)); bpy.context.object.scale=(1,0.7,0.03)
bpy.ops.mesh.primitive_plane_add(size=6, location=(0,2,1)); g=bpy.context.object; g.rotation_euler=(1.57,0,0)
m=bpy.data.materials.new('g'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']; b.inputs['Transmission Weight'].default_value=1; b.inputs['Roughness'].default_value=0.4; g.data.materials.append(m)
bpy.ops.object.light_add(type='AREA', location=(0,-1,2)); bpy.context.object.data.energy=200
bpy.ops.object.camera_add(location=(0,-1.2,0.6), rotation=(1.2,0,0)); sc.camera=bpy.context.object
sc.render.filepath='out/f.png'; t=time.time(); bpy.ops.render.render(write_still=True); print('SECONDS',time.time()-t)
