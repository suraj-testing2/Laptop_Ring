
import unittest

import binding
import errors
import injecting
import scoping
import wrapping


class BindsToTest(unittest.TestCase):

    def test_adds_binding_attrs(self):
        @binding.binds_to('foo')
        class SomeClass(object):
            pass
        self.assertTrue(getattr(SomeClass, binding._IS_DECORATED_ATTR))
        self.assertEqual(
            [binding.BindingKeyWithoutAnnotation('foo')],
            getattr(SomeClass, binding._BOUND_TO_BINDING_KEYS_ATTR))

    def test_can_decorate_several_times(self):
        @binding.binds_to('foo', annotated_with='an-annotation')
        @binding.binds_to('bar')
        class SomeClass(object):
            pass
        self.assertEqual(
            [binding.BindingKeyWithoutAnnotation('bar'),
             binding.BindingKeyWithAnnotation('foo', 'an-annotation')],
            getattr(SomeClass, binding._BOUND_TO_BINDING_KEYS_ATTR))


class NewBindingKeyTest(unittest.TestCase):

    def test_without_annotation(self):
        binding_key = binding.new_binding_key('an-arg-name')
        self.assertEqual('the arg name an-arg-name', str(binding_key))

    def test_with_annotation(self):
        binding_key = binding.new_binding_key('an-arg-name', 'an-annotation')
        self.assertEqual('the arg name an-arg-name annotated with an-annotation',
                         str(binding_key))


class BindingKeyWithoutAnnotationTest(unittest.TestCase):

    def test_equal_if_same_arg_name(self):
        binding_key_one = binding.BindingKeyWithoutAnnotation('an-arg-name')
        binding_key_two = binding.BindingKeyWithoutAnnotation('an-arg-name')
        self.assertEqual(binding_key_one, binding_key_two)
        self.assertEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertEqual(str(binding_key_one), str(binding_key_two))

    def test_unequal_if_not_same_arg_name(self):
        binding_key_one = binding.BindingKeyWithoutAnnotation('arg-name-one')
        binding_key_two = binding.BindingKeyWithoutAnnotation('arg-name-two')
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))

    def test_str(self):
        binding_key = binding.BindingKeyWithoutAnnotation('an-arg-name')
        self.assertEqual('the arg name an-arg-name', str(binding_key))


class BindingKeyWithAnnotationTest(unittest.TestCase):

    def test_equal_if_same_arg_name_and_annotation(self):
        binding_key_one = binding.BindingKeyWithAnnotation(
            'an-arg-name', 'an-annotation')
        binding_key_two = binding.BindingKeyWithAnnotation(
            'an-arg-name', 'an-annotation')
        self.assertEqual(binding_key_one, binding_key_two)
        self.assertEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertEqual(str(binding_key_one), str(binding_key_two))

    def test_unequal_if_not_same_arg_name(self):
        binding_key_one = binding.BindingKeyWithAnnotation(
            'arg-name-one', 'an-annotation')
        binding_key_two = binding.BindingKeyWithAnnotation(
            'arg-name-two', 'an-annotation')
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))

    def test_unequal_if_not_same_annotation(self):
        binding_key_one = binding.BindingKeyWithAnnotation(
            'arg-name-one', 'an-annotation')
        binding_key_two = binding.BindingKeyWithAnnotation(
            'arg-name-two', 'another-annotation')
        self.assertNotEqual(binding_key_one, binding_key_two)
        self.assertNotEqual(hash(binding_key_one), hash(binding_key_two))
        self.assertNotEqual(str(binding_key_one), str(binding_key_two))

    def test_str(self):
        binding_key = binding.BindingKeyWithAnnotation(
            'an-arg-name', 'an-annotation')
        self.assertEqual('the arg name an-arg-name annotated with an-annotation',
                         str(binding_key))


class GetBindingKeyToBindingMapsTest(unittest.TestCase):

    def setUp(self):
        class SomeClass(object):
            pass
        self.some_binding_key = binding.BindingKeyWithoutAnnotation(
            'some_class')
        self.some_binding = binding.Binding(
            self.some_binding_key, 'a-proviser-fn')
        self.another_some_binding = binding.Binding(
            self.some_binding_key, 'another-proviser-fn')

    def assertBindingsReturnMaps(
            self, explicit_bindings, implicit_bindings,
            binding_key_to_binding, collided_binding_key_to_bindings):
        self.assertEqual((binding_key_to_binding,
                          collided_binding_key_to_bindings),
                         binding.get_binding_key_to_binding_maps(
                             explicit_bindings, implicit_bindings))

    def assertBindingsRaise(
            self, explicit_bindings, implicit_bindings, error_type):
        self.assertRaises(error_type,
                          binding.get_binding_key_to_binding_maps,
                          explicit_bindings, implicit_bindings)

    def test_no_input_bindings_returns_empty_maps(self):
        self.assertBindingsReturnMaps(
            explicit_bindings=[], implicit_bindings=[],
            binding_key_to_binding={}, collided_binding_key_to_bindings={})

    def test_explicit_class_gets_returned(self):
        self.assertBindingsReturnMaps(
            explicit_bindings=[self.some_binding],
            implicit_bindings=[],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_implicit_class_gets_returned(self):
        self.assertBindingsReturnMaps(
            explicit_bindings=[],
            implicit_bindings=[self.some_binding],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_explicit_class_overrides_implicit(self):
        self.assertBindingsReturnMaps(
            explicit_bindings=[self.some_binding],
            implicit_bindings=[self.another_some_binding],
            binding_key_to_binding={self.some_binding_key: self.some_binding},
            collided_binding_key_to_bindings={})

    def test_colliding_explicit_classes_raises_error(self):
        self.assertBindingsRaise(
            explicit_bindings=[self.some_binding, self.another_some_binding],
            implicit_bindings=[],
            error_type=errors.ConflictingBindingsError)

    def test_colliding_implicit_classes_returned_as_colliding(self):
        self.assertBindingsReturnMaps(
            explicit_bindings=[],
            implicit_bindings=[self.some_binding, self.another_some_binding],
            binding_key_to_binding={},
            collided_binding_key_to_bindings={
                self.some_binding_key: set([self.some_binding,
                                            self.another_some_binding])})


class BindingMappingTest(unittest.TestCase):

    def setUp(self):
        class SomeClass(object):
            pass
        self.some_binding_key = binding.BindingKeyWithoutAnnotation(
            'some_class')
        self.some_binding = binding.Binding(
            self.some_binding_key, binding.ProviderToProviser(lambda: 'a-some-class'))
        self.another_some_binding = binding.Binding(
            self.some_binding_key, binding.ProviderToProviser(lambda: 'another-some-class'))

    def test_success(self):
        binding_mapping = binding.BindingMapping(
            {self.some_binding_key: self.some_binding}, {},
            {scoping.PROTOTYPE: scoping.PrototypeScope()}, lambda _1, _2: True)
        self.assertEqual('a-some-class',
                         binding_mapping.get_instance(
                             self.some_binding_key, binding.new_binding_context(), injector=None))

    def test_unknown_binding_raises_error(self):
        binding_mapping = binding.BindingMapping(
            {self.some_binding_key: self.some_binding}, {},
            {scoping.PROTOTYPE: scoping.PrototypeScope()}, lambda _1, _2: True)
        unknown_binding_key = binding.BindingKeyWithoutAnnotation(
            'unknown_class')
        self.assertRaises(errors.NothingInjectableForArgError,
                          binding_mapping.get_instance, unknown_binding_key,
                          binding.new_binding_context(), injector=None)

    def test_colliding_bindings_raises_error(self):
        binding_mapping = binding.BindingMapping(
            {}, {self.some_binding_key: self.some_binding,
                 self.some_binding_key: self.another_some_binding},
            {scoping.PROTOTYPE: scoping.PrototypeScope()}, lambda _1, _2: True)
        self.assertRaises(
            errors.AmbiguousArgNameError, binding_mapping.get_instance,
            self.some_binding_key, binding.new_binding_context(), injector=None)

    def test_scope_not_usable_from_scope_raises_error(self):
        binding_mapping = binding.BindingMapping(
            {self.some_binding_key: self.some_binding}, {},
            {scoping.PROTOTYPE: scoping.PrototypeScope()}, lambda _1, _2: False)
        self.assertRaises(errors.BadDependencyScopeError,
                          binding_mapping.get_instance, self.some_binding_key,
                          binding.new_binding_context(), injector=None)


class DefaultGetArgNamesFromClassNameTest(unittest.TestCase):

    def test_single_word_lowercased(self):
        self.assertEqual(['foo'], binding.default_get_arg_names_from_class_name('Foo'))

    def test_leading_underscore_stripped(self):
        self.assertEqual(['foo'], binding.default_get_arg_names_from_class_name('_Foo'))

    def test_multiple_words_lowercased_with_underscores(self):
        self.assertEqual(['foo_bar_baz'], binding.default_get_arg_names_from_class_name('FooBarBaz'))

    def test_malformed_class_name_raises_error(self):
        self.assertEqual([], binding.default_get_arg_names_from_class_name('notAllCamelCase'))


class FakeInjector(object):

    def provide(self, cls):
        return self._provide_class(cls, _UNUSED_BINDING_CONTEXT)

    def _provide_class(self, cls, binding_context):
        return 'a-provided-{0}'.format(cls.__name__)

    def _call_with_injection(self, provider_fn, binding_context):
        return provider_fn()


_UNUSED_BINDING_CONTEXT = binding.BindingContext('unused', 'unused')
def call_provisor_fn(a_binding):
    return a_binding.proviser_fn(_UNUSED_BINDING_CONTEXT, FakeInjector())


class GetExplicitBindingsTest(unittest.TestCase):

    def test_returns_no_bindings_for_no_input(self):
        self.assertEqual([], binding.get_explicit_bindings([], [], []))

    def test_returns_binding_for_input_explicitly_bound_class(self):
        @binding.binds_to('foo')
        class SomeClass(object):
            pass
        [explicit_binding] = binding.get_explicit_bindings(
            [SomeClass], [], scope_ids=[scoping.PROTOTYPE])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         explicit_binding.binding_key)
        self.assertEqual('a-provided-SomeClass', call_provisor_fn(explicit_binding))

    def test_returns_binding_for_input_provider_fn(self):
        @wrapping.provides('foo')
        def some_function():
            return 'a-foo'
        [explicit_binding] = binding.get_explicit_bindings(
            [], [some_function], scope_ids=[scoping.PROTOTYPE])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         explicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(explicit_binding))

    def test_returns_binding_for_provider_fn_on_input_class(self):
        class SomeClass(object):
            @staticmethod
            @wrapping.provides('foo')
            # TODO(kurts): figure out why the decorator order cannot be reversed.
            def some_function():
                return 'a-foo'
        [explicit_binding] = binding.get_explicit_bindings(
            [SomeClass], [], scope_ids=[scoping.PROTOTYPE])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         explicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(explicit_binding))

    def test_returns_binding_in_known_scope(self):
        @wrapping.provides('foo', in_scope='a-scope')
        def some_function():
            return 'a-foo'
        [explicit_binding] = binding.get_explicit_bindings(
            [], [some_function], scope_ids=['a-scope'])
        self.assertEqual('a-scope', explicit_binding.scope_id)

    def test_raises_error_for_binding_in_unknown_scope(self):
        @wrapping.provides('foo', in_scope='unknown-scope')
        def some_function():
            return 'a-foo'
        self.assertRaises(errors.UnknownScopeError,
                          binding.get_explicit_bindings,
                          [], [some_function], scope_ids=['known-scope'])


class GetImplicitBindingsTest(unittest.TestCase):

    def test_returns_no_bindings_for_no_input(self):
        self.assertEqual([], binding.get_implicit_bindings([], []))

    def test_returns_binding_for_input_class(self):
        class SomeClass(object):
            pass
        [implicit_binding] = binding.get_implicit_bindings([SomeClass], functions=[])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('some_class'),
                         implicit_binding.binding_key)
        self.assertEqual('a-provided-SomeClass', call_provisor_fn(implicit_binding))

    def test_returns_no_binding_for_explicitly_bound_class(self):
        @binding.binds_to('foo')
        class SomeClass(object):
            pass
        self.assertEqual([], binding.get_implicit_bindings([SomeClass], functions=[]))

    def test_returns_binding_for_correct_input_class(self):
        class ClassOne(object):
            pass
        class ClassTwo(object):
            pass
        implicit_bindings = binding.get_implicit_bindings(
            [ClassOne, ClassTwo], functions=[])
        for implicit_binding in implicit_bindings:
            if (implicit_binding.binding_key ==
                binding.BindingKeyWithoutAnnotation('class_one')):
                self.assertEqual(
                    'a-provided-ClassOne', call_provisor_fn(implicit_binding))
            else:
                self.assertEqual(
                    implicit_binding.binding_key,
                    binding.BindingKeyWithoutAnnotation('class_two'))
                self.assertEqual(
                    'a-provided-ClassTwo', call_provisor_fn(implicit_binding))

    def test_uses_provided_fn_to_map_class_names_to_arg_names(self):
        class SomeClass(object):
            pass
        [implicit_binding] = binding.get_implicit_bindings(
            [SomeClass], functions=[],
            get_arg_names_from_class_name=lambda _: ['foo'])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         implicit_binding.binding_key)

    def test_returns_binding_for_input_provider_fn(self):
        def new_foo():
            return 'a-foo'
        [implicit_binding] = binding.get_implicit_bindings(
            classes=[], functions=[new_foo])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         implicit_binding.binding_key)
        self.assertEqual('a-foo', call_provisor_fn(implicit_binding))

    def test_returns_no_binding_for_explicit_provider_fn(self):
        @wrapping.provides('bar')
        def new_foo():
            return 'a-foo'
        self.assertEqual(
            [], binding.get_implicit_bindings(classes=[], functions=[new_foo]))

    def test_returns_binding_for_staticmethod_provider_fn(self):
        class SomeClass(object):
            @staticmethod
            def new_foo():
                return 'a-foo'
        implicit_bindings = binding.get_implicit_bindings(
            classes=[SomeClass], functions=[])
        self.assertEqual([binding.BindingKeyWithoutAnnotation('some_class'),
                          binding.BindingKeyWithoutAnnotation('foo')],
                         [b.binding_key for b in implicit_bindings])
        self.assertEqual('a-foo', call_provisor_fn(implicit_bindings[1]))

    def test_returns_no_binding_for_input_non_provider_fn(self):
        def some_fn():
            pass
        self.assertEqual([], binding.get_implicit_bindings(
            classes=[], functions=[some_fn]))

    def test_uses_provided_fn_to_map_provider_fn_names_to_arg_names(self):
        def some_foo():
            return 'a-foo'
        [implicit_binding] = binding.get_implicit_bindings(
            classes=[], functions=[some_foo],
            get_arg_names_from_provider_fn_name=lambda _: ['foo'])
        self.assertEqual(binding.BindingKeyWithoutAnnotation('foo'),
                         implicit_binding.binding_key)


class BinderTest(unittest.TestCase):

    def setUp(self):
        self.collected_bindings = []
        self.binder = binding.Binder(
            self.collected_bindings,
            scope_ids=[scoping.PROTOTYPE, 'known-scope'])

    def test_can_bind_to_class(self):
        class SomeClass(object):
            pass
        self.binder.bind('an-arg-name', to_class=SomeClass)
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.BindingKeyWithoutAnnotation('an-arg-name'),
                         only_binding.binding_key)
        self.assertEqual('a-provided-SomeClass', call_provisor_fn(only_binding))

    def test_can_bind_to_instance(self):
        an_instance = object()
        self.binder.bind('an-arg-name', to_instance=an_instance)
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.BindingKeyWithoutAnnotation('an-arg-name'),
                         only_binding.binding_key)
        self.assertIs(an_instance, call_provisor_fn(only_binding))

    def test_can_bind_to_provider(self):
        self.binder.bind('an-arg-name', to_provider=lambda: 'a-provided-thing')
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.BindingKeyWithoutAnnotation('an-arg-name'),
                         only_binding.binding_key)
        self.assertEqual('a-provided-thing', call_provisor_fn(only_binding))

    def test_can_bind_with_annotation(self):
        self.binder.bind('an-arg-name', annotated_with='an-annotation',
                         to_provider=lambda: 'a-provided-thing')
        [only_binding] = self.collected_bindings
        self.assertEqual(binding.BindingKeyWithAnnotation('an-arg-name',
                                                          'an-annotation'),
                         only_binding.binding_key)
        self.assertEqual('a-provided-thing', call_provisor_fn(only_binding))

    def test_can_bind_with_scope(self):
        self.binder.bind('an-arg-name', to_provider=lambda: 'a-provided-thing',
                         in_scope='known-scope')
        [only_binding] = self.collected_bindings
        self.assertEqual('known-scope', only_binding.scope_id)

    def test_binding_to_unknown_scope_raises_error(self):
        self.assertRaises(
            errors.UnknownScopeError, self.binder.bind, 'unused-arg-name',
            to_instance='unused-instance', in_scope='unknown-scope')

    def test_binding_to_nothing_raises_error(self):
        self.assertRaises(errors.NoBindingTargetError,
                          self.binder.bind, 'unused-arg-name')

    def test_binding_to_multiple_things_raises_error(self):
        self.assertRaises(errors.MultipleBindingTargetsError,
                          self.binder.bind, 'unused-arg-name',
                          to_instance=object(), to_provider=lambda: None)

    def test_binding_to_non_class_raises_error(self):
        self.assertRaises(errors.InvalidBindingTargetError,
                          self.binder.bind, 'unused-arg-name',
                          to_class='not-a-class')

    def test_binding_to_non_provider_raises_error(self):
        self.assertRaises(errors.InvalidBindingTargetError,
                          self.binder.bind, 'unused-arg-name',
                          to_provider='not-a-provider')
