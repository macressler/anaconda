from chowdren.key import convert_key

is_knytt = False
is_avgn = False
is_anne = False
is_knytt_japan = False
is_test = False
is_hfa = False
is_fp = False

def init(converter):
    name = converter.info_dict.get('name').lower()
    global is_knytt
    global is_knytt_japan
    global is_avgn
    global is_anne
    global is_test
    global is_hfa
    is_knytt = 'knytt' in name
    is_avgn = 'angry video game' in name
    is_anne = 'ane' in name
    is_knytt_japan = 'japan' in name
    is_test = 'application' in name
    is_hfa = 'alicia' in name
    is_fp = 'freedom' in name

    if is_avgn:
        # hack to set default keyboard keys
        # 72 - 82
        values = converter.game.globalValues.items
        for i in xrange(71, 82):
            values[i] = convert_key(values[i])

    if is_hfa:
        # hack to turn on high-resolution lighting system images
        values = converter.game.globalValues.items
        values[191] = 1 # lights max resolution
        values[194] = 1 # turn off adaptive lights
        values[195] = 1 # lights min resolution
        values[196] = 1 # force small images off


object_checks = {
}

def init_container(converter, container):
    if container.name not in ('BETA TESTER SHIT -- TURN OFF WITH FINAL '
                              'RELEASE',
                              'DEBUG -- turn off!'):
        return
    container.inactive = True

def write_pre(converter, writer, group):
    pass

def use_simple_or(converter):
    return is_knytt

def use_iteration_index(converter):
    return is_avgn or is_test or is_hfa

alterable_int_objects = [
    'MenuMainMapObject_',
    'MiniMapObject_',
    'MenuMainController',
    'FireShark',
    'Cog',
    'MapMainObject',
    'CellFG',
    'CellBG'
]

def use_global_int(expression):
    index = expression.data.loader.value
    if is_avgn:
        return index in (0, 1)
    elif is_hfa:
        return index in (428,)

def use_alterable_int(expression):
    if not is_anne and not is_avgn and not is_hfa:
        return False
    obj = expression.get_object()
    name = expression.converter.get_object_name(obj)
    for check in alterable_int_objects:
        if name.startswith(check):
            return True
    return False

def use_safe_division(converter):
    return is_hfa or is_test

def get_startup_instances(converter, instances):
    if not is_hfa or converter.current_frame_index != 0:
        return instances
    # bug in Text Blitter object, need to move them to front
    new_instances = []
    text_blitters = []
    for item in instances:
        frameitem = item[1]
        obj = (frameitem.handle, frameitem.objectType)
        writer = converter.get_object_writer(obj)
        if writer.class_name == 'TextBlitter':
            text_blitters.append(item)
        else:
            new_instances.append(item)

    new_instances += text_blitters
    return new_instances

def use_safe_create(converter):
    return is_avgn or is_hfa

def use_global_instances(converter):
    return True

def use_update_filtering(converter):
    return is_anne

def write_defines(converter, writer):
    if is_anne:
        writer.putln('#define CHOWDREN_SNES_CONTROLLER')
    if is_avgn or is_anne:
        writer.putln('#define CHOWDREN_FORCE_REMOTE')
    if is_anne or is_avgn or is_hfa:
        writer.putln('#define CHOWDREN_QUICK_SCALE')
    if is_knytt_japan:
        writer.putln('#define CHOWDREN_TEXT_USE_UTF8')
        writer.putln('#define CHOWDREN_TEXT_JAPANESE')
        writer.putln('#define CHOWDREN_BIG_FONT_OFFY 1')
    if is_avgn or is_hfa:
        writer.putln('#define CHOWDREN_STARTUP_WINDOW')
        writer.putln('#define CHOWDREN_POINT_FILTER')
    if is_avgn:
        writer.putln('#define CHOWDREN_PERSISTENT_FIXED_STRING')
    if use_iteration_index(converter):
        writer.putln('#define CHOWDREN_ITER_INDEX')
    if is_avgn or is_test:
        writer.putln('#define CHOWDREN_LAYER_WRAP')
    if is_avgn or is_hfa:
        writer.putln('#define CHOWDREN_RESTORE_ANIMATIONS')
    if is_hfa or is_test:
        writer.putln('#define CHOWDREN_INI_FILTER_QUOTES')
        writer.putln('#define CHOWDREN_INI_KEEP_ORDER')
    if is_hfa:
        writer.putln('#define CHOWDREN_FORCE_TRANSPARENT')
        writer.putln('#define CHOWDREN_VSYNC')
        writer.putln('#define CHOWDREN_IS_HFA')
        writer.putln('#define CHOWDREN_OBSTACLE_IMAGE')
    writer.putln('#define CHOWDREN_USE_DYNTREE')
    if is_avgn:
        writer.putln('#define CHOWDREN_WIIU_USE_COMMON')
    # if is_hfa or is_test:
        # writer.putln('#define CHOWDREN_USE_DYNAMIC_NUMBER')

def get_frames(converter, game, frames):
    if not is_hfa:
        return frames
    new_frames = {}
    if game.index == 0:
        indexes = (0, 1, 3, 4, 15, 16, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31,
                   32, 33, 35, 36, 37, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48,
                   49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63,
                   64, 65, 66, 67, 68, 69, 70, 71, 72)
    else:
        indexes = (0, 1, 2, 3, 4, 5, 6)
    for index in indexes:
        new_frames[index] = frames[index]
    return new_frames
