from chowdren.writers.objects import ObjectWriter

from chowdren.common import get_animation_name, to_c, make_color

from chowdren.writers.events import (StaticConditionWriter,
    StaticActionWriter, StaticExpressionWriter, make_table,
    ConditionMethodWriter, ExpressionMethodWriter, EmptyAction,
    StaticConditionWriter, TrueCondition, FalseCondition)

class Joystick2(ObjectWriter):
    class_name = 'Joystick'
    static = True

    def write_init(self, writer):
        pass

actions = make_table(StaticActionWriter, {
    0 : EmptyAction, # ignore control
    1 : EmptyAction, # restore control,
    35 : EmptyAction, # poll for devices, not necessary on GLFW
})

conditions = make_table(ConditionMethodWriter, {
    0 : 'is_joystick_pressed', # repeat while
    1 : 'any_joystick_pressed',
    2 : 'is_joystick_attached',
    3 : FalseCondition, # how does this work exactly
    4 : 'is_joystick_pressed',
    5 : 'is_joystick_pressed', # once
    6 : 'is_joystick_released',
    7 : 'any_joystick_pressed',
    17 : 'compare_joystick_direction',
    27 : 'is_joystick_direction_changed',
    33 : TrueCondition, # is xbox controller
    26 : TrueCondition, # has point of view
    8 : 'is_joystick_pressed(%s, CHOWDREN_BUTTON_DPAD_UP)'
})

expressions = make_table(ExpressionMethodWriter, {
    0 : 'get_joystick_x',
    1 : 'get_joystick_y',
    6 : 'get_joystick_dpad_degrees',
    22 : 'get_joystick_last_press',
    26 : 'get_joystick_degrees'
})

def get_object():
    return Joystick2