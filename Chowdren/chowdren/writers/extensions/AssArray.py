from chowdren.writers.objects import ObjectWriter
from chowdren.common import (get_image_name, get_animation_name, to_c,
    make_color)
from chowdren.writers.events import (ComparisonWriter, ActionMethodWriter,
    ConditionMethodWriter, ExpressionMethodWriter, make_table, EmptyAction)

class AssociateArray(ObjectWriter):
    class_name = 'AssociateArray'
    includes = ['objects/assarray.h']

    def write_init(self, writer):
        data = self.get_data()
        data.skipBytes(4)
        data.skipBytes(4) # width, height
        is_global = data.readByte() != 0
        if is_global:
            writer.putln('map = &global_map;')
        else:
            writer.putln('map = new ArrayMap();')


actions = make_table(ActionMethodWriter, {
    0 : 'set_value',
    1 : 'set_string',
    3 : 'clear',
    43 : 'load_encrypted',
    44 : 'set_key',
    25 : EmptyAction, # set_file_saving_interval
    24 : EmptyAction # set_file_loading_interval
})

conditions = make_table(ConditionMethodWriter, {
})

expressions = make_table(ExpressionMethodWriter, {
    0 : 'get_value',
    1 : 'get_string'
})

def get_object():
    return AssociateArray