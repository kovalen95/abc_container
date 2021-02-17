import abc
from typing import List, Set, Any


class ABContainer(abc.ABCMeta):
    """Extends ABCMeta metaclass to also check for class specific fields. Allows to create Container abstract classes,
    that forces theirs subclasses to implement attributes listed in annotations.
    Usage:
    class ContainerClassInterface(metaclass=ABContainer):
        field_that_must_be_inherited: Any
        _also_inherit_private_single_dash: Any
        __omit_this_field: Any
    class ContainerSubclassA(ContainerClassInterface):
        field_that_must_be_inherited = 'OK'
        _also_inherit_private_single_dash = 'OK'
    class ContainerSubclassAA(ContainerSubclassA):
        pass
    class ContainerSubclassB(ContainerClassInterface):
        pass
    Classes ContainerSubclassA and ContainerSubclassAA will be perceived as correctly specified. ContainerSubclassB does
    not implement necessary attributes of ContainerClassInterface and the script results in the following error:
    NameError: Container ContainerSubclassB does not handle following attributes
    field_that_must_be_inherited, _also_inherit_private_single_dash.
    """

    def __new__(mcs, what, bases, _dict, **kwargs):
        """Return new class if it implements all fields specified in annotations of it's parents that has ABContainer
        type, or the class directly inherits from ABContainer, hence being a Container class Protocol."""
        cls = super().__new__(mcs, what, bases, _dict, **kwargs)
        is_first_level_child = True
        parent_required_attributes = []
        for parent_class in bases:
            if type(parent_class) == ABContainer:
                is_first_level_child = False
                parent_required_attributes.extend(ABContainer._get_class_needed_attributes(parent_class))
        if is_first_level_child:
            if not ABContainer._get_class_needed_attributes(cls):
                raise NameError(f'Container {cls.__name__} does not contain any required fields.')
        else:
            missing_requirements = []
            for requirement in parent_required_attributes:
                if not hasattr(cls, requirement):
                    missing_requirements.append(requirement)
            if missing_requirements:
                raise NameError(
                    f"Container {cls.__name__} does not handle following attributes {', '.join(missing_requirements)}."
                )
        return cls

    @staticmethod
    def _get_class_needed_attributes(cls) -> List[str]:
        """Return a list of annotations of a class. All private fields of the class and it's parents are skipped."""
        omit_names = ABContainer._get_class_bases(cls)
        omit_names.add(cls.__name__)
        omit_starting_sequences = {f'_{name}__' for name in omit_names}
        all_inherit_attributes = [attribute for attribute in cls.__annotations__.keys()]
        necessary_attributes = []
        for attribute in all_inherit_attributes:
            must_inherit = True
            for starting_seq in omit_starting_sequences:
                if attribute.startswith(starting_seq):
                    must_inherit = False
                    break
            if must_inherit:
                necessary_attributes.append(attribute)
        return necessary_attributes

    @staticmethod
    def _get_class_bases(cls) -> Set[str]:
        """Return unique collection of names of classes that cls inherits from."""
        bases = ABContainer.__get_class_bases(cls)
        ret = {base.__name__ for base in bases}
        return ret

    @staticmethod
    def __get_class_bases(cls) -> List[type]:
        """Return list of types of all bases given class inherits from."""
        bases = list(cls.__bases__)
        for base in bases:
            bases.extend(ABContainer.__get_class_bases(base))
        return bases