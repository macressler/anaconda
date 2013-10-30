from chowdren.writers.events import (ActionWriter, ConditionWriter, 
    ExpressionWriter, ComparisonWriter, ActionMethodWriter, 
    ConditionMethodWriter, ExpressionMethodWriter, make_table,
    make_expression, make_comparison, EmptyAction)
from chowdren.common import get_method_name, to_c, make_color
from chowdren.writers.objects import ObjectWriter
from chowdren import shader
from collections import defaultdict

def get_loop_running_name(name):
    return 'loop_%s_running' % get_method_name(name)

def get_loop_index_name(name):
    return 'loop_%s_index' % get_method_name(name)

PROFILE_LOOPS = set([])

class SystemObject(ObjectWriter):
    def __init__(self, converter):
        self.converter = converter
        self.data = None

    def write_frame(self, writer):
        self.write_group_activated(writer)
        self.write_loops(writer)

    def write_start(self, writer):
        for container, names in self.group_activations.iteritems():
            for name in names:
                writer.putln(to_c('%s = true;', name))
        for name in self.loops.keys():
            running_name = get_loop_running_name(name)
            index_name = get_loop_index_name(name)
            writer.putln('%s = false;' % running_name)
            writer.putln('%s = 0;' % index_name)

    def write_group_activated(self, writer):
        self.group_activations = defaultdict(list)
        for group in self.converter.always_groups_dict['OnGroupActivation']:
            cond = group.conditions[0]
            container = cond.container
            check_name = cond.get_group_check()
            writer.putln('bool %s;' % (check_name))
            self.group_activations[container].append(check_name)

    def write_loops(self, writer):
        self.loop_names = set()
        loops = self.loops = defaultdict(list)
        dynloops = []
        for loop_group in self.get_conditions('OnLoop'):
            exps = loop_group.conditions[0].data.items[0].loader.items
            exp = exps[0]

            if len(exps) > 2 or exp.getName() != 'String':
                dynloops.append((exps, loop_group))
                continue

            name = exp.loader.value
            if name == 'Clear Filter':
                # KU-specific hack
                continue
            self.loop_names.add(name.lower())
            loops[name].append(loop_group)

        if not loops:
            return

        for name in loops.keys():
            running_name = get_loop_running_name(name)
            index_name = get_loop_index_name(name)
            writer.putln('bool %s;' % running_name)
            writer.putln('int %s;' % index_name)

        self.converter.begin_events()
        for name, groups in loops.iteritems():
            profile = name in PROFILE_LOOPS
            loop_name = get_method_name(name)
            writer.putmeth('bool loop_%s' % loop_name)
            self.converter.current_loop_name = name

            if profile:
                writer.putln('double profile_time, profile_dt;')

            for index, group in enumerate(groups):
                if profile:
                    writer.putln('profile_time = platform_get_time();')
                self.converter.write_event(writer, group, True)
                if profile:
                    writer.putln('profile_dt = platform_get_time() '
                                              '- profile_time;')
                    writer.putln('if (profile_dt > 0.0001)')
                    writer.indent()
                    writer.putln(
                        ('std::cout << "Event %s took " << '
                         'profile_dt << std::endl;') % group.global_id)
                    writer.dedent()
            writer.putln('return true;')
            writer.end_brace()

        writer.putmeth('bool call_dynamic_loop', 'const std::string & name')
        for name in loops.keys():
            writer.putln(to_c('if (name == %r) return loop_%s();', 
                name, get_method_name(name)))
        writer.putln('return false;')
        writer.end_brace()

# conditions

class IsOverlapping(ConditionWriter):
    has_object = False

    def write(self, writer):
        data = self.data
        negated = data.otherFlags['Not']
        object_info = data.objectInfo
        other_info = data.items[0].loader.objectInfo
        converter = self.converter
        if negated:
            writer.put(to_c(
                'check_not_overlap(%s, %s)',
                converter.get_object(object_info, True), 
                converter.get_object(other_info, True)))
        else:
            selected_name = converter.get_list_name(converter.get_object_name(
                object_info))
            other_selected = converter.get_list_name(converter.get_object_name(
                other_info))
            writer.put(to_c(
                'check_overlap(%s, %s, %s, %s)',
                converter.get_object(object_info, True), 
                converter.get_object(other_info, True), 
                selected_name, other_selected))
            converter.set_list(object_info, selected_name)
            converter.set_list(other_info, other_selected)

    def is_negated(self):
        return False

class ObjectInvisible(ConditionWriter):
    def write(self, writer):
        writer.put('visible')

    def is_negated(self):
        return True

class MouseOnObject(ConditionWriter):
    def get_object(self):
        data = self.data.items[0].loader
        return data.objectInfo, data.objectType

    def write(self, writer):
        writer.put('mouse_over()')

class Always(ConditionWriter):
    custom = True

    def write(self, writer):
        pass

class MouseClicked(ConditionWriter):
    is_always = True

    def write(self, writer):
        writer.put('is_mouse_pressed_once(%s)' % self.convert_index(0))

class ObjectClicked(ConditionWriter):
    is_always = True

    def get_object(self):
        data = self.data.items[1].loader
        return data.objectInfo, data.objectType

    def write(self, writer):
        writer.put('mouse_over() && '
                   'is_mouse_pressed_once(%s)' % self.convert_index(0))

# class PlayerKeyDown(ConditionWriter):
#     def write(self, writer):
#         writer.put('is_player_key_pressed(%s, %r)' % )

class TimerEquals(ConditionWriter):
    is_always = True

    def write(self, writer):
        seconds = self.parameters[0].loader.timer / 1000.0
        writer.put('frame_time >= %s' % seconds)

class TimerGreater(ConditionWriter):
    is_always = True

    def write(self, writer):
        seconds = self.parameters[0].loader.timer / 1000.0
        writer.put('frame_time >= %s' % seconds)

class TimerLess(ConditionWriter):
    is_always = True

    def write(self, writer):
        seconds = self.parameters[0].loader.timer / 1000.0
        writer.put('frame_time <= %s' % seconds)

class TimerEvery(ConditionWriter):
    is_always = True
    custom = True

    def write(self, writer):
        seconds = self.parameters[0].loader.delay / 1000.0
        name = 'every_%s' % id(self)
        writer.putln('static float %s = 0.0f;' % name)
        event_break = self.converter.event_break
        writer.putln('%s += float(manager->fps_limit.dt);' % name)
        writer.putln('if (%s < %s) %s' % (name, seconds, event_break))
        writer.putln('%s -= %s;' % (name, seconds))

class AnimationFinished(ConditionWriter):
    is_always = True

    def write(self, writer):
        writer.put('is_animation_finished(%s)' % self.convert_index(0))

class OnGroupActivation(ConditionWriter):
    custom = True
    def write(self, writer):
        group_check = self.get_group_check()
        writer.putln('if (!%s) %s' % (group_check, self.converter.event_break))
        writer.putln('%s = false;' % group_check)

    def get_group_check(self):
        return 'group_check_%s' % id(self)

class NotAlways(ConditionWriter):
    custom = True
    def write(self, writer):
        event_break = self.converter.event_break
        name = 'not_always_%s' % id(self)
        name2 = '%s_frame' % name
        writer.putln('static unsigned int %s = loop_count;' % name)
        writer.putln('static unsigned int %s = frame_iteration;' % name2)
        writer.putln('if (%s != frame_iteration) {' % name2)
        writer.indent()
        writer.putln('%s = frame_iteration;' % name2)
        writer.putln('%s = loop_count;' % name)
        writer.end_brace()
        writer.putln('if (%s > loop_count) {' % (name))
        writer.indent()
        writer.putln('%s = loop_count + 2;' % name)
        writer.putln(event_break)
        writer.end_brace()
        writer.putln('%s = loop_count + 2;' % name)

class OnceCondition(ConditionWriter):
    custom = True
    def write(self, writer):
        event_break = self.converter.event_break
        name = 'once_condition_%s' % id(self)
        writer.putln('static unsigned int %s = -1;' % name)
        writer.putln('if (%s == frame_iteration) %s' % (name, event_break))
        writer.putln('%s = frame_iteration;' % (name))

class GroupActivated(ConditionWriter):
    def write(self, writer):
        container = self.converter.containers[
            self.parameters[0].loader.pointer]
        writer.put(self.converter.get_container_check(container))

class PickRandom(ConditionWriter):
    custom = True
    def write(self, writer):
        object_info, object_type = self.get_object()
        converter = self.converter
        selected_name = converter.get_list_name(converter.get_object_name(
            object_info))
        if object_info not in converter.has_selection:
            get_list = converter.get_object(object_info, True)
            writer.putln('%s = %s;' % (selected_name, get_list))
            converter.set_list(object_info, selected_name)
        writer.putln('pick_random(%s);' % selected_name)

class NumberOfObjects(ComparisonWriter):
    iterate_objects = False

    def get_comparison_value(self):
        object_info, object_type = self.get_object()
        return '%s.size()' % self.converter.get_object(object_info, True)

class CompareFixedValue(ConditionWriter):
    custom = True
    def write(self, writer):
        object_info, object_type = self.get_object()
        converter = self.converter

        end_label = 'fixed_%s_end' % id(self)
        value = self.convert_index(0)
        comparison = self.get_comparison()
        is_equal = comparison == '=='
        has_selection = object_info in converter.has_selection
        is_instance = value.endswith('get_fixed()')
        test_all = has_selection or not is_equal or not is_instance
        if is_instance:
            instance_value = value.replace('->get_fixed()', '')
        else:
            instance_value = 'get_object_from_fixed(%s)' % value

        selected_name = converter.get_list_name(converter.get_object_name(
            object_info))
        get_list = converter.get_object(object_info, True)

        fixed_name = 'fixed_test_%s' % id(self)
        writer.putln('FrameObject * %s = %s;' % (fixed_name, instance_value))
        if is_equal:
            event_break = converter.event_break
        else:
            event_break = 'goto %s;' % end_label
        if test_all and not has_selection:
            writer.putln('%s = %s;' % (selected_name, get_list))
        writer.putln('if (%s == NULL) %s' % (fixed_name, event_break))
        if test_all:
            writer.putln('item = %s.begin();' % (selected_name))
            writer.putln('while (item != %s.end()) {' % selected_name)
            writer.indent()
            writer.putln('if (!((*item) %s %s)) item = %s.erase(item);' % (
                comparison, fixed_name, selected_name))
            writer.putln('else ++item;')
            writer.end_brace()
            writer.put_label(end_label)
            writer.putln('if (%s.empty()) %s' % (selected_name,
                                                 converter.event_break))
        else:
            writer.putln('make_single_list(%s, %s);' % (fixed_name,
                                                        selected_name))
            writer.put_label(end_label)

        converter.set_list(object_info, selected_name)

class FacingInDirection(ConditionWriter):
    def write(self, writer):
        parameter = self.parameters[0].loader
        if parameter.isExpression:
            name = 'test_direction'
            value = self.convert_index(0)
        else:
            name = 'test_directions'
            value = parameter.value
        writer.put('%s(%s)' % (name, value))

# actions

class CreateBase(ActionWriter):
    custom = True
    def write(self, writer):
        writer.start_brace()
        end_name = 'create_%s_end' % id(self)
        is_shoot = self.is_shoot
        details = self.convert_index(0)
        x = str(details['x'])
        y = str(details['y'])
        parent = details.get('parent', None)
        if parent is not None and not is_shoot:
            writer.putln('int parent_x, parent_y, layer_index;')
            parent_list = 'parent_instances'
            writer.putln('FrameObject * parent = %s;' % (
                self.converter.get_object(parent)))
            writer.putln('if (parent == NULL) parent_x = parent_y = '
                         'layer_index = 0;')
            writer.putln('else {')
            writer.indent()
            if details.get('use_action_point', False):
                parent_x = 'get_action_x()'
                parent_y = 'get_action_y()'
            else:
                parent_x = 'x'
                parent_y = 'y'
            writer.putln('parent_x = parent->%s;' % parent_x)
            writer.putln('parent_y = parent->%s;' % parent_y)
            writer.putln('layer_index = parent->layer_index;')
            writer.end_brace()
            if details.get('set_direction', False):
                raise NotImplementedError
                # arguments.append('use_direction = True')
            if details.get('transform_position_direction', False):
                print 'transform position direction not implemented'
            if details.get('use_direction', False):
                print 'use_direction not implemented'
            x = 'parent_x + %s' % (x)
            y = 'parent_y + %s' % (y)
            layer = 'layer_index'
        else:
            layer = details['layer']
        if is_shoot:
            create_object = details['shoot_object']
        else:
            create_object = details['create_object']
        arguments = [x, y]
        obj_create_func = 'create_%s' % get_method_name(create_object)
        create_method = 'create_object'
        writer.putln('FrameObject * new_obj = %s(%s(%s), %s); // %s' % (
            create_method, obj_create_func, ', '.join(arguments), layer,
            details))
        object_info = self.parameters[0].loader.objectInfo
        try:
            list_name = self.converter.has_selection[object_info]
            writer.putln('%s.push_back(new_obj);' % (list_name))
        except KeyError:
            list_name = self.converter.get_list_name(create_object)
            writer.putln('make_single_list(new_obj, %s);' % (list_name))
            self.converter.has_selection[object_info] = list_name
        if is_shoot:
            writer.putln('%s->shoot(new_obj, %s);' % (
                self.converter.get_object(object_info),
                details['shoot_speed']))
        writer.end_brace()
        if False: # action_name == 'DisplayText':
            paragraph = parameters[1].loader.value
            if paragraph != 0:
                raise NotImplementedError

class CreateObject(CreateBase):
    is_shoot = False

class ShootObject(CreateBase):
    is_shoot = True

class SetPosition(ActionWriter):
    def write(self, writer):
        details = self.convert_index(0)
        x = str(details['x'])
        y = str(details['y'])
        parent = details.get('parent', None)
        if parent is not None:
            parent = self.converter.get_object(parent)
            if details.get('use_action_point', False):
                parent_x = 'get_action_x()'
                parent_y = 'get_action_y()'
            else:
                parent_x = 'x'
                parent_y = 'y'
            x = '%s->%s + %s' % (parent, parent_x, x)
            y = '%s->%s + %s' % (parent, parent_y, y)
            if details.get('set_direction', False):
                raise NotImplementedError
            if details.get('transform_position_direction', False):
                print 'transform position direction 2 not implemented'
            if details.get('use_direction', False):
                print 'use direction 2 not implemented'
        arguments = [x, y]
        writer.put('set_position(%s); // %s' % (
            ', '.join(arguments), details))

class LookAt(ActionWriter):
    def write(self, writer):
        object_info, object_type = self.get_object()
        instance = self.converter.get_object(object_info)
        details = self.convert_index(0)
        x = str(details['x'])
        y = str(details['y'])
        parent = details.get('parent', None)
        if not parent:
            raise NotImplementedError()
        parent = self.converter.get_object(parent)
        x = '%s->x + %s' % (parent, x)
        y = '%s->y + %s' % (parent, y)
        writer.put('set_direction(get_direction_int(%s->x, %s->y, %s, %s));' 
            % (instance, instance, x, y))

class MoveInFront(ActionWriter):
    def write(self, writer):
        object_info = self.parameters[0].loader.objectInfo
        writer.put('move_front(%s);' % (self.converter.get_object(object_info)))

class MoveBehind(ActionWriter):
    def write(self, writer):
        object_info = self.parameters[0].loader.objectInfo
        # if object_info in self.converter.multiple_instances:
        #     raise NotImplementedError
        writer.put('move_back(%s);' % (self.converter.get_object(object_info)))

class StartLoop(ActionWriter):
    def write(self, writer):
        real_name = None
        try:
            exp, = self.parameters[0].loader.items[:-1]
            real_name = exp.loader.value
            loop_names = self.converter.system_object.loop_names
            if real_name.lower() not in loop_names:
                if real_name == 'Clear Filter':
                    self.converter.clear_selection()
                return
            name = get_method_name(real_name)
            func_call = 'loop_%s()' % name
        except ValueError:
            func_call = 'call_dynamic_loop(name)'
        comparison = None
        times = None
        try:
            exp, = self.parameters[1].loader.items[:-1]
            if exp.getName() == 'Long':
                times = exp.loader.value
                if times == -1:
                    comparison = 'true'
        except ValueError:
            pass
        if times is None:
            times = self.convert_index(1)
        is_infinite = comparison is not None
        is_dynamic = real_name is None
        if is_dynamic:
            raise NotImplementedError
        running_name = get_loop_running_name(real_name)
        index_name = get_loop_index_name(real_name)
        if not is_infinite:
            comparison = '%s < times' % index_name
        writer.start_brace()
        # writer.putln('static const std::string name = %s;' %
        #              self.convert_index(0))
        writer.putln('%s = true;' % running_name)
        # writer.putln('RunningLoops::iterator running_it '
        #     '= set_map_value(running_loops, name, false);')
        # writer.putln('running_it->second = true;')
        if not is_infinite:
            writer.putln('int times = int(%s);' % times)
        writer.putln('%s = 0;' % index_name)
        # writer.putln('LoopIndexes::iterator index_it '
        #     '= set_map_value(loop_indexes, name, 0);')
        # writer.putln('index_it->second = 0;')
        writer.putln('while (%s) {' % comparison)
        writer.indent()
        writer.putln('%s;' % func_call)
        # writer.putln('if (!running_it->second) break;')
        writer.putln('if (!%s) break;' % running_name)
        # writer.putln('index_it->second++;')
        writer.putln('%s++;' % index_name)
        writer.end_brace()
        writer.end_brace()
        # self.converter.write_container_check(self.group, writer)
        self.converter.clear_selection()

class DeactivateGroup(ActionWriter):
    deactivated_container = None
    def write(self, writer):
        container = self.get_deactivated_container()
        writer.putln('%s = false;' % container.code_name)

    def get_deactivated_container(self):
        if self.deactivated_container is None:
            self.deactivated_container = self.converter.containers[
                self.parameters[0].loader.pointer]
        return self.deactivated_container

    def write_post(self, writer):
        pass
        # container = self.get_deactivated_container()
        # if container in self.converter.container_tree:
        #     writer.putln('goto %s;' % container.end_label)
        # elif self.container and container in self.container.tree:
        #     pass

class StopLoop(ActionWriter):
    def write(self, writer):
        exp, = self.parameters[0].loader.items[:-1]
        name = exp.loader.value
        running_name = get_loop_running_name(name)
        writer.putln('%s = false;' % running_name)

class SetLoopIndex(ActionWriter):
    def write(self, writer):
        exp, = self.parameters[0].loader.items[:-1]
        name = exp.loader.value
        index_name = get_loop_index_name(name)
        value = self.convert_index(1)
        # writer.putln(to_c('loop_indexes[%r] = %s;', name, value))
        writer.putln('%s = %s;' % index_name, value)

class ActivateGroup(ActionWriter):
    def write(self, writer):
        container = self.converter.containers[
            self.parameters[0].loader.pointer]
        writer.put('%s = true;' % container.code_name)
        check_names = set()
        group_activations = self.converter.system_object.group_activations
        for child in ([container] + container.get_all_children()):
            check_names.update(group_activations[child])
        for name in check_names:
            writer.putln('%s = true;' % name)

class CenterDisplayX(ActionWriter):
    def write(self, writer):
        writer.put('set_display_center(%s, -1);' % self.convert_index(0))

class CenterDisplayY(ActionWriter):
    def write(self, writer):
        writer.put('set_display_center(-1, %s);' % self.convert_index(0))

class EndApplication(ActionWriter):
    def write(self, writer):
        writer.put('has_quit = true;')

class SetFrameAction(ActionWriter):
    def set_frame(self, writer, value):
        writer.put('next_frame = %s;' % value)
        writer.putln('')
        fade = self.converter.current_frame.fadeOut
        if not fade:
            return
        color = fade.color
        writer.putln(to_c('manager->set_fade(%s, %s);', make_color(
            color), 1.0 / (fade.duration / 1000.0)))

class JumpToFrame(SetFrameAction):
    def write(self, writer):
        frame = self.parameters[0].loader
        if frame.isExpression:
            value = '%s-1' % self.convert_index(0)
        else:
            value = str(self.converter.game.frameHandles[frame.value])
        self.set_frame(writer, value)

class RestartFrame(SetFrameAction):
    def write(self, writer):
        self.set_frame(writer, 'index')

class NextFrame(SetFrameAction):
    def write(self, writer):
        self.set_frame(writer, 'index + 1')

class PreviousFrame(SetFrameAction):
    def write(self, writer):
        self.set_frame(writer, 'index - 1')

class SetEffect(ActionWriter):
    def write(self, writer):
        name = self.parameters[0].loader.value
        if name == '':
            shader_name = 'NULL'
        else:
            shader_name = shader.get_name(name)
        writer.put('set_shader(%s);' % shader_name)

class SpreadValue(ActionWriter):
    custom = True
    def write(self, writer):
        alt = self.convert_index(0)
        start = self.convert_index(1)
        object_list = self.converter.get_object(self.data.objectInfo, True)
        writer.putln('spread_value(%s, %s, %s);' % (object_list, alt, start))

# expressions

class ValueExpression(ExpressionWriter):
    def get_string(self):
        return to_c('%r', self.data.loader.value)

class ConstantExpression(ExpressionWriter):
    def get_string(self):
        return self.value

class StringExpression(ExpressionWriter):
    def get_string(self):
        self.converter.start_clauses -= self.data.loader.value.count('(')
        self.converter.end_clauses -= self.data.loader.value.count(')')
        return to_c('std::string(%r)', self.data.loader.value)

class EndParenthesis(ConstantExpression):
    value = ')'

class PlusExpression(ConstantExpression):
    value = '+'

class MinusExpression(ConstantExpression):
    value = '-'

class MultiplyExpression(ConstantExpression):
    value = '*'

class DivideExpression(ConstantExpression):
    value = '/'

class ModulusExpression(ConstantExpression):
    value = '%'

class ParenthesisExpression(ConstantExpression):
    value = '('

class VirguleExpression(ExpressionWriter):
    def get_string(self):
        out = ''
        if self.converter.last_out[-1] == '(':
            out += ')'
        out += ', '
        return out

class AlterableValueExpression(ExpressionWriter):
    def get_string(self):
        return 'values->get(%s)' % self.data.loader.value

class AlterableStringExpression(ExpressionWriter):
    def get_string(self):
        return 'strings->get(%s)' % self.data.loader.value

class GlobalValueExpression(ExpressionWriter):
    def get_string(self):
        return 'global_values->get(%s)' % self.data.loader.value

class GlobalStringExpression(ExpressionWriter):
    def get_string(self):
        return 'global_strings->get(%s)' % self.data.loader.value

class ObjectCount(ExpressionWriter):
    has_object = False
    def get_string(self):
        return '%s.size()' % self.converter.get_object(
            self.data.objectInfo, True)

class ToString(ExpressionWriter):
    def get_string(self):
        converter = self.converter
        next = converter.expression_items[converter.item_index + 1].getName()
        if next == 'FixedValue':
            return 'std::string('
        return 'number_to_string('

class GetLoopIndex(ExpressionWriter):
    def get_string(self):
        converter = self.converter
        next_exp = converter.expression_items[converter.item_index + 1]
        converter.item_index += 2
        name = next_exp.loader.value
        index_name = get_loop_index_name(name)
        return index_name

actions = make_table(ActionMethodWriter, {
    'CreateObject' : CreateObject,
    'Shoot' : ShootObject,
    'StartLoop' : StartLoop,
    'StopLoop' : StopLoop,
    'SetX' : 'set_x',
    'SetY' : 'set_y',
    'SetAlterableValue' : 'values->set',
    'AddToAlterable' : 'values->add',
    'SpreadValue' : SpreadValue,
    'SubtractFromAlterable' : 'values->sub',
    'SetAlterableString' : 'strings->set',
    'AddCounterValue' : 'add',
    'SubtractCounterValue' : 'subtract',
    'SetCounterValue' : 'set',
    'SetMaximumValue' : 'set_max',
    'SetMinimumValue' : 'set_min',
    'SetGlobalString' : 'global_strings->set',
    'SetGlobalValue' : 'global_values->set',
    'AddGlobalValue' : 'global_values->add',
    'SubtractGlobalValue' : 'global_values->sub',
    'SetString' : 'set_string',
    'SetBold' : 'set_bold',
    'Hide' : 'set_visible(false)',
    'Show' : 'set_visible(true)',
    'SetParagraph' : 'set_paragraph(%s-1)',
    'LockChannel' : 'media->lock(%s-1)',
    'StopChannel' : 'media->stop_channel(%s-1)',
    'ResumeChannel' : 'media->resume_channel(%s-1)',
    'PauseChannel' : 'media->pause_channel(%s-1)',
    'SetChannelPosition' : 'media->set_channel_position(%s-1, %s)',
    'SetChannelPan' : 'media->set_channel_pan(%s-1, %s)',
    'SetChannelVolume' : 'media->set_channel_volume(%s-1, %s)',
    'PlayLoopingChannelFileSample' : 'media->play(%s, %s-1, %s)',
    'PlayChannelFileSample' : 'media->play(%s, %s-1)',
    'PlayChannelSample' : 'media->play_name("%s", %s-1)',
    'PlayLoopingChannelSample' : 'media->play_name("%s", %s-1, %s)',
    'PlayLoopingSample' : 'media->play_name("%s", -1, %s-1)',
    'PlaySample' : 'media->play_name("%s", -1, 1)',
    'SetChannelFrequency' : 'media->set_channel_frequency(%s-1, %s) ',
    'SetDirection' : 'set_direction',
    'SetRGBCoefficient' : 'set_blend_color',
    'SetAngle' : 'set_angle',
    'DeactivateGroup' : DeactivateGroup,
    'ActivateGroup' : ActivateGroup,
    'CenterDisplayX' : CenterDisplayX,
    'CenterDisplayY' : CenterDisplayY,
    'EndApplication' : EndApplication,
    'RestartApplication' : 'restart',
    'LookAt' : LookAt,
    'SetPosition' : SetPosition,
    'ExecuteEvaluatedProgram' : 'open_process',
    'HideCursor' : 'set_cursor_visible(false)',
    'ShowCursor' : 'set_cursor_visible(true)',
    'FullscreenMode' : 'set_fullscreen(true)',
    'NextFrame' : NextFrame,
    'PreviousFrame' : PreviousFrame,
    'MoveToLayer' : 'set_layer(%s-1)',
    'JumpToFrame' : JumpToFrame,
    'RestartFrame' : RestartFrame,
    'SetAlphaCoefficient' : 'blend_color.set_alpha_coefficient(%s)',
    'SetSemiTransparency' : 'blend_color.set_semi_transparency(%s)',
    'SetXScale' : 'set_x_scale({0})',
    'SetYScale' : 'set_y_scale({0})',
    'SetScale' : 'set_scale({0})',
    'ForceAnimation' : 'force_animation',
    'RestoreAnimation' : 'restore_animation',
    'ForceFrame' : 'force_frame',
    'ForceSpeed' : 'force_speed',
    'RestoreFrame' : 'restore_frame',
    'SetEffect' : SetEffect,
    'AddToDebugger' : EmptyAction,
    'SetFrameRate' : 'manager->set_framerate(%s)',
    'Destroy' : 'destroy',
    'BringToBack' : 'move_back',
    'BringToFront' : 'move_front',
    'DeleteAllCreatedBackdrops' : 'layers[%s-1]->destroy_backgrounds()',
    'DeleteCreatedBackdrops' : 'layers[%s-1]->destroy_backgrounds(%s, %s, %s)',
    'SetEffectParameter' : 'set_shader_parameter',
    'SetFrameBackgroundColor' : 'set_background_color',
    'AddBackdrop' : 'paste',
    'PasteActive' : 'paste',
    'MoveInFront' : MoveInFront,
    'MoveBehind' : MoveBehind,
    'ForceDirection' : 'force_direction',
    'StopAnimation' : 'stop_animation',
    'StartAnimation' : 'start_animation',
    'RestoreSpeed' : 'restore_speed',
    'SetMainVolume' : 'media->set_main_volume',
    'StopAllSamples' : 'media->stop_samples',
    'StopSample' : 'media->stop_sample("%s")',
    'SetSampleVolume' : 'media->set_sample_volume("%s", %s)',
    'NextParagraph' : 'next_paragraph',
    'PauseApplication' : 'pause',
    'SetRandomSeed' : 'set_random_seed',
    'SetTimer' : 'set_timer',
    'SetLoopIndex' : SetLoopIndex,
    'IgnoreControls' : EmptyAction, # XXX fix
    'RestoreControls' : EmptyAction, # XXX fix,
    'ChangeControlType' : EmptyAction, # XXX fix,
    'FlashDuring' : 'flash',
    'SetMaximumSpeed' : 'get_movement()->set_max_speed',
    'SetSpeed' : 'get_movement()->set_speed',
    'Bounce' : 'get_movement()->bounce()',
    'Start' : 'get_movement()->start()',
    'Stop' : 'get_movement()->stop()',
    'SetDirections' : 'get_movement()->set_directions',
    'GoToNode' : 'get_movement()->set_node',
    'SelectMovement' : 'set_movement',
    'EnableFlag' : 'enable_flag',
    'DisableFlag' : 'disable_flag',
    'ReplaceColor' : EmptyAction # XXX fix,
})

conditions = make_table(ConditionMethodWriter, {
    'CompareAlterableValue' : make_comparison('values->get(%s)'),
    'CompareAlterableString' : make_comparison('strings->get(%s)'),
    'CompareGlobalValue' : make_comparison('global_values->get(%s)'),
    'CompareGlobalString' : make_comparison('global_strings->get(%s)'),
    'CompareCounter' : make_comparison('value'),
    'CompareX' : make_comparison('x'),
    'CompareY' : make_comparison('y'),
    'Compare' : make_comparison('%s'),
    'IsOverlapping' : IsOverlapping,
    'OnCollision' : IsOverlapping,
    'ObjectVisible' : '.visible',
    'ObjectInvisible' : ObjectInvisible,
    'WhileMousePressed' : 'is_mouse_pressed',
    'MouseOnObject' : MouseOnObject,
    'Always' : Always,
    'MouseClicked' : MouseClicked,
    'ObjectClicked' : ObjectClicked,
    # 'PlayerKeyDown' : PlayerKeyDown,
    'KeyDown' : 'is_key_pressed',
    'KeyPressed' : 'is_key_pressed_once(%s)',
    'OnGroupActivation' : OnGroupActivation,
    'FacingInDirection' : FacingInDirection,
    'AnimationPlaying' : 'test_animation',
    'Chance' : 'random_chance',
    'CompareFixedValue' : CompareFixedValue,
    'OutsidePlayfield' : 'outside_playfield',
    'IsObstacle' : 'test_background_collision',
    'IsOverlappingBackground' : 'overlaps_background',
    'OnBackgroundCollision' : 'overlaps_background',
    'PickRandom' : PickRandom,
    'NumberOfObjects' : NumberOfObjects,
    'GroupActivated' : GroupActivated,
    'NotAlways' : NotAlways,
    'AnimationFrame' : make_comparison('get_frame()'),
    'ChannelNotPlaying' : '!media->is_channel_playing(%s-1)',
    'SampleNotPlaying' : '!media->is_sample_playing("%s")',
    'Once' : OnceCondition,
    'Every' : TimerEvery,
    'TimerEquals' : TimerEquals,
    'TimerGreater' : TimerGreater,
    'TimerLess' : TimerLess,
    'IsBold' : 'get_bold',
    'IsItalic' : 'get_italic',
    'MovementStopped' : 'get_movement()->is_stopped()',
    'PathFinished' : 'get_movement()->is_path_finished',
    'NodeReached' : 'get_movement()->is_node_reached',
    'CompareSpeed' : make_comparison('get_movement()->get_speed()'),
    'FlagOn' : 'is_flag_on',
    'FlagOff' : 'is_flag_off',
    'NearWindowBorder' : 'is_near_border',
    'AnimationFinished' : AnimationFinished,
    'StartOfFrame' : '.loop_count <= 1'
})

expressions = make_table(ExpressionMethodWriter, {
    'Speed' : 'get_movement()->get_speed()',
    'String' : StringExpression,
    'ToNumber' : 'string_to_double',
    'ToInt' : 'int',
    'Abs' : 'get_abs',
    'ToString' : ToString,
    'GetRGB' : 'make_color_int',
    'Long' : ValueExpression,
    'Double' : ValueExpression,
    'EndParenthesis' : EndParenthesis,
    'Plus' : PlusExpression,
    'Multiply' : MultiplyExpression,
    'Divide' : DivideExpression,
    'Minus' : MinusExpression,
    'Virgule' : VirguleExpression,
    'Parenthesis' : ParenthesisExpression,
    'Modulus' : '.%math_helper%',
    'Random' : 'randrange',
    'ApplicationPath' : 'get_app_path()',
    'AlterableValue' : AlterableValueExpression,
    'AlterableValueIndex' : 'values->get',
    'AlterableStringIndex' : 'strings->get',
    'AlterableString' : AlterableStringExpression,
    'GlobalString' : GlobalStringExpression,
    'GlobalValue' : GlobalValueExpression,
    'YPosition' : 'get_y()',
    'XPosition' : 'get_x()',
    'ActionX' : 'get_action_x()',
    'ActionY' : 'get_action_y()',
    'GetParagraph' : 'get_paragraph',
    'ParagraphCount' : 'get_count()',
    'CurrentParagraphIndex' : 'get_index()+1',
    'LoopIndex' : GetLoopIndex,
    'CurrentText' : '.text',
    'XMouse' : 'get_mouse_x()',
    'YMouse' : 'get_mouse_y()',
    'Min' : 'std::min<double>',
    'Max' : 'std::max<double>',
    'Sin' : 'sin_deg',
    'Cos' : 'cos_deg',
    'GetAngle' : 'get_angle()',
    'FrameHeight' : '.height',
    'FrameWidth' : '.width',
    'StringLength' : 'string_size',
    'Find' : 'string_find',
    'ReverseFind' : 'string_rfind',
    'LowerString' : 'lowercase_string',
    'UpperString' : 'uppercase_string',
    'MidString' : 'mid_string',
    'LeftString' : 'left_string',
    'FixedValue' : 'get_fixed()',
    'AnimationFrame' : 'get_frame()',
    'ObjectLeft' : 'get_box_index(0)',
    'ObjectRight' : 'get_box_index(2)',
    'ObjectTop' : 'get_box_index(1)',
    'ObjectBottom' : 'get_box_index(3)',
    'GetDirection' : 'get_direction()',
    'GetXScale' : '.x_scale',
    'GetYScale' : '.y_scale',
    'Power' : '.*math_helper*',
    'SquareRoot' : 'sqrt',
    'Atan2' : 'atan2d',
    'AlphaCoefficient' : 'blend_color.get_alpha_coefficient()',
    'EffectParameter' : 'get_shader_parameter',
    'Floor' : 'floor',
    'Round' : 'int_round',
    'AnimationNumber' : 'get_animation',
    'Ceil' : 'ceil',
    'GetMainVolume' : 'media->get_main_volume()',
    'GetChannelPosition' : '.media->get_channel_position(-1 +',
    'GetChannelVolume' : '.media->get_channel_volume(-1 +',
    'NewLine' : '.newline_character',
    'XLeftFrame' : 'frame_left()',
    'XRightFrame' : 'frame_right()',
    'YBottomFrame' : 'frame_bottom()',
    'ObjectCount' : ObjectCount,
    'CounterMaximumValue' : '.maximum',
    'ApplicationDirectory' : 'get_app_dir()',
    'ApplicationDrive' : 'get_app_drive()',
    'TimerValue' : '.frame_time * 1000.0',
    'CounterValue': '.value'
})
