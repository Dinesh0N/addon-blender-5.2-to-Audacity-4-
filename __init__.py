bl_info = {
    "name": "VSE to Audacity",
    "author": "Ai",
    "version": (0, 1),
    "blender": (5, 2, 0),
    "location": "Sequencer Sidebar",
    "description": "Open Sound Strip, Sequence or Record in Audacity",
    "category": "Sequencer",
}

import bpy, os
from bpy.app.handlers import persistent
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty

from . import utils
from . import operators

addon_name = os.path.basename(os.path.dirname(__file__))



class AUDACITYTOOLS_PF_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = addon_name

    audacity_executable : bpy.props.StringProperty(
        name = "Audacity executable",
        subtype = "FILE_PATH",
        )

    audacity_waiting_time : bpy.props.FloatProperty(
        name = "Audacity waiting time",
        description = "Waiting time in seconds for Audacity opening",
        default = 1,
        precision = 1,
        min = 0.5,
        max = 10.0,
    )


    def draw(self, context):
        layout = self.layout

        layout.prop(self, "audacity_executable")
        layout.prop(self, "audacity_waiting_time")
        
        pipe = context.window_manager.audacity_tools_pipe_available
        box = layout.box()
        row = box.row(align=True)
        if pipe:
            row.label(text="Pipe available", icon="CHECKMARK")
        else:
            row.label(text="Pipe unavailable", icon="ERROR")
        
        row.operator("sequencer.refresh_audacity_pipe", text="", icon="FILE_REFRESH")
 

# get addon preferences
def get_addon_preferences():
    addon = bpy.context.preferences.addons.get(addon_name)
    return getattr(addon, "preferences", None)







class AUDACITYTOOLS_PR_properties(bpy.types.PropertyGroup) :
    '''name : StringProperty() '''

    send_to_new_file : BoolProperty(
        name = "Open in new Audacity file",
        description = "Uncheck to send to the existing open Audacity session instead",
        default = True,
        )

    record_start : IntProperty(
        name = "Record start",
        default = -1,
        )

    record_end : IntProperty(
        name = "Record end",
        default = -1,
        )

    audacity_mode : bpy.props.EnumProperty(
        name="Mode",
        description="",
        items=(
            ("SELECTION", "Selection", ""),
            ("SEQUENCE", "Sequence", ""),
            ("RECORD", "Record", ""),
            ),
        )






@persistent
def audacity_tools_startup(scene):
    # check pipe
    utils.check_set_pipe()

    # reset properties
    for s in bpy.data.scenes:
        props = s.audacity_tools_props
        props.record_start = -1
        props.record_end = -1
    print("Audacity Tools --- Properties reset")




class SEQUENCER_PT_audacity_tools(bpy.types.Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_idname = "SEQUENCER_PT_audacity_tools"
    bl_label = "Audacity Tools"
    bl_category = "Audacity Tools"

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.view_type == "SEQUENCER"
            or context.space_data.view_type == "SEQUENCER_PREVIEW"
        )

    def draw_header(self, context):
        layout = self.layout
        pipe = context.window_manager.audacity_tools_pipe_available
        if pipe:
            layout.label(text="", icon="RADIOBUT_ON")
        else:
            layout.label(text="", icon="RADIOBUT_OFF")

    def draw(self, context):
        scene = context.scene
        props = scene.audacity_tools_props
        screen = context.screen
        layout = self.layout

        layout.row().prop(props, "audacity_mode", expand=True)
        col = layout.column(align=(False))

        if props.audacity_mode in {"SEQUENCE", "SELECTION"}:
            col.prop(props, "send_to_new_file")
            col.separator()

        # SEQUENCE or SELECTION MODE
        if props.audacity_mode == "SEQUENCE" or props.audacity_mode == "SELECTION":
            col.separator()
            col.operator(
                "sequencer.send_project_to_audacity",
                text="Send "+(props.audacity_mode).title(),
                icon="EXPORT",
            )
            col.operator(
                "sequencer.receive_from_audacity", text="Receive Mixdown", icon="IMPORT"
            )
            col.separator()
            row = col.row(align=False)
            if not screen.is_animation_playing:
                row.operator(
                    "sequencer.play_stop_in_audacity", text="Play", icon="PLAY"
                )
            else:
                row.operator(
                    "sequencer.play_stop_in_audacity", text="Stop", icon="SNAP_FACE"
                )
            if scene.use_audio:
                row.prop(scene, "use_audio", text="",icon="PLAY_SOUND", emboss = False)
            else:
                row.prop(scene, "use_audio", text="",icon="OUTLINER_OB_SPEAKER", emboss = False)    

        # RECORD MODE
        elif props.audacity_mode == "RECORD":
            sub = col.column() 
            if not screen.is_animation_playing or (props.record_end !=-1 and props.record_start !=-1):
                col.operator(
                    "sequencer.record_in_audacity", text="Record", icon="RADIOBUT_ON"
                )
            elif props.record_start != -1:
                col.operator(
                    "sequencer.play_stop_in_audacity", text="Stop", icon="SNAP_FACE"
                )

            sub = col.column()
            sub.active = not props.record_start == -1
            sub.operator(
                "sequencer.receive_from_audacity", text="Receive", icon="IMPORT"
            )
            if props.record_start != -1 and props.record_end != -1:
                col.separator()
                row = col.row(align=False)
                if not screen.is_animation_playing:
                    row.operator(
                        "sequencer.play_stop_in_audacity", text="Play", icon="PLAY"
                    )
                else:
                    row.operator(
                        "sequencer.play_stop_in_audacity", text="Stop", icon="SNAP_FACE"
                    )
                if scene.use_audio:
                    row.prop(scene, "use_audio", text="",icon="PLAY_SOUND", emboss = False)
                else:
                    row.prop(scene, "use_audio", text="",icon="OUTLINER_OB_SPEAKER", emboss = False) 





classes = (
    AUDACITYTOOLS_PF_Addon_Prefs,
    AUDACITYTOOLS_PR_properties,
    SEQUENCER_PT_audacity_tools,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.audacity_tools_props = bpy.props.PointerProperty(type=AUDACITYTOOLS_PR_properties, name="Audacity tools properties")
    bpy.types.WindowManager.audacity_tools_pipe_available = bpy.props.BoolProperty(default=False)
    bpy.app.handlers.load_post.append(audacity_tools_startup)
    operators.register()

def unregister():
    operators.unregister()
    bpy.app.handlers.load_post.remove(audacity_tools_startup)
    del bpy.types.WindowManager.audacity_tools_pipe_available
    del bpy.types.Scene.audacity_tools_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
