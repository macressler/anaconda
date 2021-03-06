from chowdren.writers import BaseWriter
from mmfparser.bytereader import ByteReader
from chowdren.idpool import get_id

class ObjectWriter(BaseWriter):
    common = None
    class_name = 'Undefined'
    static = False
    filename = None
    defines = []
    event_callbacks = None
    use_alterables = False
    has_color = False
    update = False
    movement_count = 0
    default_instance = None

    def __init__(self, *arg, **kw):
        self.event_callbacks = {}
        BaseWriter.__init__(self, *arg, **kw)
        self.common = self.data.properties.loader
        self.initialize()

    def initialize(self):
        pass

    def write_pre(self, writer):
        pass

    def write_constants(self, writer):
        pass

    def get_parameters(self):
        return []

    def get_init_list(self):
        return {}

    def write_class(self, writer):
        pass

    def write_start(self, writer):
        pass

    def write_frame(self, writer):
        pass

    def write_init(self, writer):
        pass

    def write_post(self, writer):
        pass

    def get_qualifiers(self):
        try:
            return self.common.qualifiers
        except AttributeError:
            return []

    def get_data(self):
        return ByteReader(self.common.extensionData)

    def has_movements(self):
        return self.movement_count > 0

    def has_updates(self):
        return self.update

    def get_conditions(self, *values):
        groups = []
        for value in values:
            if self.data is None:
                key = value
            else:
                key = (self.data.properties.objectType, value)
            groups.extend(self.converter.generated_groups.pop(key, []))
        groups.sort(key = lambda x: x.global_id)
        return groups

    def get_object_conditions(self, *values):
        object_info = self.data.handle
        groups = []
        for value in values:
            if self.data is None:
                key = value
            else:
                key = (self.data.properties.objectType, value)
            new_groups = self.converter.generated_groups.get(key, None)
            if not new_groups:
                continue
            for group in new_groups[:]:
                first = group.conditions[0]
                other_info = first.data.objectInfo
                if other_info != object_info:
                    continue
                groups.append(group)
                new_groups.remove(group)
            if not new_groups:
                self.converter.generated_groups.pop(key)
        groups.sort(key = lambda x: x.global_id)
        return groups

    def is_visible(self):
        try:
            return self.common.newFlags['VisibleAtStart']
        except (AttributeError, KeyError):
            return True

    def is_scrolling(self):
        try:
            return not self.common.flags['ScrollingIndependant']
        except AttributeError:
            return True

    def is_background(self):
        return self.common.isBackground()

    def is_static_background(self):
        return self.is_background()

    def is_global(self):
        return False
        return self.data.flags['Global']

    def get_images(self):
        return []

    def add_event_callback(self, name):
        event_id = self.converter.event_callback_ids.next()
        self.event_callbacks[name] = event_id
        return event_id

    def write_event_callback(self, name, writer, groups):
        wrapper_name = '%s_%s_%s' % (name, get_id(self),
                                     self.converter.current_frame_index)
        event_id = self.event_callbacks[name]
        wrapper_name = self.converter.write_generated(wrapper_name, writer,
                                                      groups)
        self.converter.event_callbacks[event_id] = wrapper_name

    def write_internal_class(self, writer):
        if not self.is_global():
            return
        writer.putln('static bool has_saved_alterables = false;')
        writer.putln('static AlterableValues saved_values;')
        writer.putln('static AlterableStrings saved_strings;')

    def has_dtor(self):
        return self.is_global()

    def write_dtor(self, writer):
        if self.is_global():
            writer.putln('has_saved_alterables = true;')
            writer.putln('saved_values.set(*values);')
            writer.putln('saved_strings.set(*strings);')

    def load_alterables(self, writer):
        if not self.use_alterables:
            return

        is_global = self.is_global()
        writer.putln('create_alterables();')

        if is_global:
            writer.putln('if (has_saved_alterables) {')
            writer.indent()
            writer.putln('values->set(saved_values);')
            writer.putln('strings->set(saved_strings);')
            writer.dedent()
            writer.putln('} else {')
            writer.indent()

        common = self.common
        if common.values:
            for index, value in enumerate(common.values.items):
                if value == 0:
                    continue
                writer.putlnc('alterables->values.set(%s, %s);', index, value)
        if common.strings:
            for index, value in enumerate(common.strings.items):
                if value == '':
                    continue
                value = self.converter.intern_string(value)
                writer.putlnc('alterables->strings.set(%s, %s);', index, value)

        if is_global:
            writer.end_brace()

    def get_base_filename(self):
        if '/' in self.filename:
            return self.filename
        return 'objects/%s' % self.filename

    def get_includes(self):
        if self.filename is None:
            return []
        return ['%s.h' % self.get_base_filename()]

    def get_sources(self):
        if self.filename is None:
            return []
        return ['%s.cpp' % self.get_base_filename()]

    @staticmethod
    def write_application(converter):
        pass

class EventCallback(object):
    def __init__(self, base, converter):
        self.base = base
        self.converter = converter

    def __str__(self):
        return '%s_%s' % (self.base, self.converter.current_frame_index)

    def __hash__(self):
        return hash(self.base)