"""Open the saved asset with a task-owned Blender MCP session for final inspection."""
import bpy,addon_utils
addon_utils.enable('bl_ext.raw_githubusercontent_com.garrison',default_set=False)
addon_utils.enable('bl_ext.user_default.blender_mcp',default_set=False)
bpy.ops.blendermcp.start_server()
print('BERBER_HOUSE_PREVIEW_BRIDGE_READY',flush=True)
