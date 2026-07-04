import bpy, os
from bpy_extras.io_utils import ExportHelper
from . import utils





class SEQUENCER_OT_play_stop_in_audacity(bpy.types.Operator):
    """Stop Audacity"""

    bl_idname = "sequencer.play_stop_in_audacity"
    bl_label = "Play/Stop"
    bl_description = "Play/Stop in Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.window_manager.audacity_tools_pipe_available

    def execute(self, context):
        # check if pipe available
        if not utils.check_pipe():
            self.report({"WARNING"}, "Audacity unavailable.")
            return {"FINISHED"}

        if not bpy.context.scene.sequence_editor:
            context.scene.sequence_editor_create()
        scene = context.scene
        props = scene.audacity_tools_props
        sequence = scene.sequence_editor
        screen = context.screen

        if not screen.is_animation_playing:

            if props.audacity_mode == "RECORD" and props.record_start != -1 and props.record_end !=-1:
                bpy.context.scene.use_audio = True
                range_in = 0
                range_out = frames_to_sec(props.record_end) - frames_to_sec(props.record_start)

                if range_out > range_in:
                    scene.use_preview_range = True
                    scene.frame_preview_start = props.record_start
                    scene.frame_preview_end = props.record_end - 2 #latency
                    scene.frame_current = props.record_start

                    utils.do_command(("SelectTime:End='"+str(range_out)+"' RelativeTo='ProjectStart' Start='"+str(range_in)+"'").replace("'", '"'))
                    utils.do_command("PlayLooped:")

                    bpy.ops.screen.animation_play()

            elif props.audacity_mode == "SEQUENCE" or props.audacity_mode == "SELECTION":
                bpy.context.scene.use_audio = True
                scene.use_preview_range = True
                scene.frame_preview_start = scene.frame_current
                scene.frame_preview_end = scene.frame_end
                current_in = frames_to_sec(scene.frame_current)
                range_in = frames_to_sec(scene.frame_start)
                range_out = frames_to_sec(scene.frame_end)

                utils.do_command(("SelectTime:End='"+str(range_out)+"' RelativeTo='ProjectStart' Start='"+str(current_in)+"'").replace("'", '"'))
                utils.do_command("PlayLooped:")

                bpy.ops.screen.animation_play()


        else:

            utils.do_command("Stop:")
            bpy.ops.screen.animation_cancel(restore_frame=False)
            bpy.ops.anim.previewrange_clear()
            bpy.context.scene.use_audio = False
            if props.record_end == -1:
                props.record_end = scene.frame_current

        return {"FINISHED"}








# get unique name
def get_unique_name_from_dir(directory, base_name):
    base_name_no_ext, ext = os.path.splitext(base_name)

    #check for dupes
    old_names = []
    for name in os.listdir(directory):
        if base_name_no_ext in name:
            old_names.append(name)
    
    count = 0
    new_name = base_name
    while new_name in old_names:
        new_name = base_name_no_ext + "_" + str(count).zfill(3) + ext
        count += 1

    return new_name


def find_completely_empty_channel():
    if not bpy.context.scene.sequence_editor:
        bpy.context.scene.sequence_editor_create()
    sequences = bpy.context.scene.sequence_editor.strips_all
    if not sequences:
        addSceneChannel = 1
    else:
        channels = [s.channel for s in sequences]
        channels = sorted(list(set(channels)))
        empty_channel = channels[-1] + 1
        addSceneChannel = empty_channel
    return addSceneChannel


class SEQUENCER_OT_receive_from_audacity(bpy.types.Operator, ExportHelper):

    bl_idname = "sequencer.receive_from_audacity"
    bl_label = "Receive"

    filename_ext = ".wav"

    filter_glob: bpy.props.StringProperty(
        default="*.wav",
        options={"HIDDEN"},
        maxlen=255,
    )

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        # if file saved, get proper unique name
        if bpy.data.filepath:
            directory = os.path.dirname(bpy.data.filepath)
            blend_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
            base_name = "%s_from_audacity.wav" % blend_name
            base_path = os.path.join(directory, base_name)
            if os.path.isfile(base_path):
                self.filepath = get_unique_name_from_dir(directory, base_name)
            else:
                self.filepath = base_path
        
        return super().invoke(context, event)

    def execute(self, context):
        # check if pipe available
        if not utils.check_pipe():
            self.report({"WARNING"}, "Audacity unavailable.")
            return {"FINISHED"}

        scene = context.scene
        props = scene.audacity_tools_props
        mode = props.audacity_mode

        # Because Audacity 4 has no IPC, the user must manually export the file from Audacity
        # to this path before clicking 'Receive'. We no longer send macro commands.
        
        if not os.path.exists(self.filepath):
            self.report({"WARNING"}, f"File {self.filepath} not found. Please export it from Audacity first.")
            return {"CANCELLED"}

        sequence = scene.sequence_editor
        seq_ops = bpy.ops.sequencer
        if props.record_start != -1 and mode  == "RECORD":
            seq_ops.sound_strip_add(
                filepath=self.filepath,
                relative_path=False,
                frame_start=props.record_start,
                channel=find_completely_empty_channel(),
            )
            props.record_start = -1
            props.record_end = -1
        elif mode != "SEQUENCE" and mode != "SELECTION":  # No Strip name, insert at current frame
            seq_ops.sound_strip_add(
                filepath=self.filepath,
                relative_path=False,
                frame_start=scene.frame_current,
                channel=find_completely_empty_channel(),
            )
        else:  # Sequence
            seq_ops.sound_strip_add(
                filepath=self.filepath,
                relative_path=False,
                frame_start=0,
                channel=find_completely_empty_channel(),
            )
        return {"FINISHED"}








class SEQUENCER_OT_record_in_audacity(bpy.types.Operator):
    """Record Audacity"""

    bl_idname = "sequencer.record_in_audacity"
    bl_label = "Record in Audacity"
    bl_description = "Record in Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.window_manager.audacity_tools_pipe_available

    def execute(self, context):
        # check if pipe available
        if not utils.check_pipe():
            self.report({"WARNING"}, "Audacity unavailable.")
            return {"FINISHED"}

        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()
        scene = bpy.context.scene
        props = scene.audacity_tools_props
        sequence = scene.sequence_editor

        props.record_start = scene.frame_current
        props.record_end = -1
        bpy.context.scene.use_audio = True

        utils.do_command("SelectAll")
        utils.do_command("RemoveTracks")

        utils.do_command("Record1stChoice:")
        bpy.ops.screen.animation_play()

        return {"FINISHED"}







class SEQUENCER_OT_refresh_audacity_pipe(bpy.types.Operator):
    """Record Audacity"""

    bl_idname = "sequencer.refresh_audacity_pipe"
    bl_label = "Refresh Pipe"
    bl_description = "Refresh the Audacity pipe"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # check if pipe available
        if utils.check_set_pipe():
            self.report({"INFO"}, "Pipe set")
        else:
            self.report({"WARNING"}, "Audacity unavailable.")

        return {"FINISHED"}







# return active strip
def act_strip(context):
    try:
        return context.scene.sequence_editor.active_strip
    except AttributeError:
        return False


def frames_to_sec(frames):
    render = bpy.context.scene.render
    fps = render.fps / render.fps_base
    sec = frames / fps
    return sec


# Get f-curves and set then as envelopes.
def set_volume(strip, strip_mode):
    scene = bpy.context.scene
    props = scene.audacity_tools_props
    mode = props.audacity_mode
    sequence = scene.sequence_editor
    volume = strip.volume
    name = sequence.strips_all[strip.name]
    fade_curve = None  # curve for the fades

    if strip.mute == True:
        utils.do_command(
            "SetEnvelope: Time="
            + str(frames_to_sec(name.frame_offset_start)+0.01)
            + " Value=0"
        )
    elif scene.animation_data is not None:
        if scene.animation_data.action is not None:
            action = scene.animation_data.action
            all_curves = []
            if hasattr(action, "fcurves"):
                all_curves.extend(action.fcurves)
            elif hasattr(action, "layers"):
                for layer in action.layers:
                    for strp in layer.strips:
                        if hasattr(strp, "channelbags"):
                            for cb in strp.channelbags:
                                all_curves.extend(cb.fcurves)
                        elif hasattr(strp, "fcurves"):
                            all_curves.extend(strp.fcurves)

            # attempts to find the keyframes by iterating through all curves in scene

            for curve in all_curves:
                if (
                    curve.data_path
                    == 'sequence_editor.strips_all["' + strip.name + '"].volume'
                ):
                    fade_curve = curve
                    if fade_curve:
                        fade_keyframes = fade_curve.keyframe_points

                        for f in fade_keyframes:
                            # f.co[0] is the frame number
                            # f.co[1] is the keyed value
                            if f.co[1] == 0:
                                volume = 0.001
                            else:
                                volume = f.co[1]
                            sound_start = sequence.strips_all[
                                strip.name
                            ].frame_final_start
                            sound_end = (
                                name.frame_final_start
                                + sequence.strips_all[
                                    strip.name
                                ].frame_final_duration
                            )
                            # Fade out will not work on last frame. Audacity cuts it so add/subtract value
                            if f.co[0] >= sound_end:
                                frame = sound_end - 1
                            elif f.co[0] <= sound_start:
                                frame = sound_start + 0.01
                            else:
                                frame = f.co[0]
                            if strip_mode:
                                utils.do_command(
                                    "SetEnvelope: Time="
                                    + str(frames_to_sec(frame - sequence.strips_all[strip.name].frame_start))
                                    + " Value="
                                    + str(volume)
                                )
                            else:
                                utils.do_command(
                                    "SetEnvelope: Time="
                                    + str(frames_to_sec(frame))
                                    + " Value="
                                    + str(volume)
                                )
    if fade_curve is None:
        if mode == "SEQUENCE" or mode == "SELECTION":
            utils.do_command(
                "SetEnvelope: Time="
                + str(frames_to_sec(name.frame_final_start)+0.01)
                + " Value="
                + str(volume)
            )
        







# return sound sequences of timeline
def collect_sound_strips():
    scene = bpy.context.scene
    props = scene.audacity_tools_props
    sequencer = scene.sequence_editor

    if props.audacity_mode == "SEQUENCE":    
        sequences = sequencer.strips_all
    elif props.audacity_mode == "SELECTION":
        sequences = bpy.context.selected_strips
    export_sequences = []
    for sequence in sequences:
        if sequence.type == "SOUND":
            export_sequences.append(sequence)
    return export_sequences


class SEQUENCER_OT_send_project_to_audacity(bpy.types.Operator):
    """Send to Audacity"""

    bl_idname = "sequencer.send_project_to_audacity"
    bl_label = "Send Sequence to Audacity"
    bl_description = "Send Sequence to Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        # check if pipe available
        if not utils.check_pipe():
            self.report({"WARNING"}, "Audacity unavailable.")
            return {"FINISHED"}

        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()
        strip = act_strip(context)
        scene = bpy.context.scene
        props = scene.audacity_tools_props
        sequence = scene.sequence_editor
        render = bpy.context.scene.render
        fps = round((render.fps / render.fps_base), 3)
        props.record_start = -1
        props.record_end = -1

        mixdown_path = "/tmp/blender_audacity_mixdown.wav"
        try:
            bpy.ops.sound.mixdown(filepath=mixdown_path, container='WAV', codec='PCM')
            
            if props.send_to_new_file:
                utils.forward_file(mixdown_path)
            else:
                utils.do_command(f'Import2: Filename="{mixdown_path}"')
            
            # Mute the original clips in Blender so they don't double-play, mimicking the old behavior
            sequences = collect_sound_strips()
            for sequence in sequences:
                set_volume(sequence, False)

        except Exception as e:
            self.report({"ERROR"}, f"Failed to mixdown: {str(e)}")

        return {"FINISHED"}






classes = (
    SEQUENCER_OT_play_stop_in_audacity,
    SEQUENCER_OT_receive_from_audacity,
    SEQUENCER_OT_record_in_audacity,
    SEQUENCER_OT_refresh_audacity_pipe,
    SEQUENCER_OT_send_project_to_audacity,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
