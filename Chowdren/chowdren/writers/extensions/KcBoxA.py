from chowdren.writers.objects import ObjectWriter
from chowdren.common import (get_image_name, get_animation_name, to_c,
    make_color)
from chowdren.writers.events import (ComparisonWriter, ActionMethodWriter,
    ConditionMethodWriter, ExpressionMethodWriter, make_table)
from mmfparser.data.font import LogFont
from mmfparser.bitdict import BitDict

def get_system_color(index):
    return None
    # if index == 0xFFFF:
    #     return None
    # if index & (1 << 31) != 0:
    #     return get_color_number(index)
    # try:
    #     return COLORS[index]
    # except KeyError:
    #     return (0, 0, 0)

def read_system_color(reader):
    return get_system_color(reader.readInt(True))

FLAGS = BitDict(
    'AlignTop',
    'AlignVerticalCenter',
    'AlignBottom',
    None,
    'AlignLeft',
    'AlignHorizontalCenter',
    'AlignRight',
    None,
    'Multiline',
    'NoPrefix',
    'EndEllipsis',
    'PathEllipsis',
    'Container',
    'Contained',
    'Hyperlink',
    None,
    'AlignImageTopLeft',
    'AlignImageCenter',
    'AlignImagePattern',
    None,
    'Button',
    'Checkbox',
    'ShowButtonBorder',
    'ImageCheckbox',
    'HideImage',
    'ForceClipping',
    None,
    None,
    'ButtonPressed',
    'ButtonHighlighted',
    'Disabled'
)

NONE, HYPERLINK, BUTTON, CHECKBOX = xrange(4)

class SystemBox(ObjectWriter):
    class_name = 'SystemBox'
    includes = ['objects/systembox.h']

    def write_init(self, writer):
        data = self.get_data()
        # data.skipBytes(4)

        width = data.readShort(True)
        height = data.readShort(True)
        writer.putlnc('width = %s;', width)
        writer.putlnc('height = %s;', height)

        flags = FLAGS.copy()
        flags.setFlags(data.readInt())
        self.show_border = flags['ShowButtonBorder']
        self.image_checkbox = flags['ImageCheckbox']
        if flags['Hyperlink']:
            display_type = HYPERLINK
        elif flags['Button']:
            if flags['Checkbox']:
                display_type = CHECKBOX
            else:
                display_type = BUTTON
        else:
            display_type = NONE
        align_top_left = flags['AlignImageTopLeft']
        align_center = flags['AlignImageCenter']
        pattern = flags['AlignImagePattern']
        fill = read_system_color(data)
        border1 = read_system_color(data)
        border2 = read_system_color(data)
        self.image = data.readShort()

        if pattern:
            writer.putln('type = PATTERN_IMAGE;')
        elif align_center:
            writer.putln('type = CENTER_IMAGE;')
        elif align_top_left:
            writer.putln('type = TOPLEFT_IMAGE;')
        else:
            raise NotImplementedError()

        if self.image == -1:
            raise NotImplementedError()

        writer.putln('image = %s;' % get_image_name(self.image))
        data.skipBytes(2) # rData_wFree
        text_color = read_system_color(data)
        margin_left = data.readShort()
        margin_top = data.readShort()
        margin_right = data.readShort()
        margin_bottom = data.readShort()

        font = LogFont(data, old=True)
        data.skipBytes(40) # file.readStringSize(40)
        data.adjust(8)
        text = data.readReader(data.readInt(True)).readString().rsplit('\\n',
                                                                       1)
        if len(text) == 1:
            text, = text
            tooltip = None
        else:
            text, tooltip = text
        new_width = width - margin_left - margin_right
        new_height = height - margin_top - margin_bottom

        if flags['AlignTop']:
            y_align = 'top'
        elif flags['AlignVerticalCenter']:
            y_align = 'center'
        elif flags['AlignBottom']:
            y_align = 'bottom'

        if flags['AlignLeft']:
            x_align = 'left'
        elif flags['AlignHorizontalCenter']:
            x_align = 'center'
        elif flags['AlignRight']:
            x_align = 'right'

        version = data.readInt()
        hyperlink_color = read_system_color(data)

actions = make_table(ActionMethodWriter, {
    1 : 'set_position'
})

conditions = make_table(ConditionMethodWriter, {
})

expressions = make_table(ExpressionMethodWriter, {
})

def get_object():
    return SystemBox