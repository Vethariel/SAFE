from typing import Callable, List, Optional

from django.db import transaction

from .models import Content, Course, Module


def _order_nodes(
    nodes: List,
    prev_attr: str,
    next_attr: str,
    fallback_key: Callable,
) -> List:
    """Return nodes ordered by their double-linked pointers with a safe fallback."""
    if not nodes:
        return []

    node_map = {node.pk: node for node in nodes if node.pk is not None}
    head_candidates = [
        node
        for node in nodes
        if getattr(node, prev_attr) is None
        or getattr(getattr(node, prev_attr), "pk", None) not in node_map
    ]
    head = head_candidates[0] if head_candidates else None

    ordered: List = []
    seen = set()
    current = head

    while current and current.pk not in seen:
        ordered.append(current)
        seen.add(current.pk)
        nxt = getattr(current, next_attr)
        current = nxt if nxt and nxt.pk in node_map else None

    if len(ordered) != len(nodes):
        remaining = [node for node in nodes if node.pk not in seen]
        remaining.sort(key=fallback_key)
        ordered.extend(remaining)

    return ordered


def _rewrite_chain(
    ordered_nodes: List,
    prev_attr: str,
    next_attr: str,
    order_attr: Optional[str] = None,
) -> None:
    """Persist previous/next (and optional order) pointers to match the ordered list."""
    for index, node in enumerate(ordered_nodes):
        prev_node = ordered_nodes[index - 1] if index > 0 else None
        next_node = ordered_nodes[index + 1] if index + 1 < len(ordered_nodes) else None

        fields = []
        if getattr(node, prev_attr) != prev_node:
            setattr(node, prev_attr, prev_node)
            fields.append(prev_attr)

        if getattr(node, next_attr) != next_node:
            setattr(node, next_attr, next_node)
            fields.append(next_attr)

        if order_attr:
            desired_order = index + 1
            if getattr(node, order_attr) != desired_order:
                setattr(node, order_attr, desired_order)
                fields.append(order_attr)

        if fields:
            node.save(update_fields=fields)


def get_ordered_modules(course: Course) -> List[Module]:
    """Return modules of a course ordered using their linked pointers."""
    modules = list(
        course.modules.select_related("previous_module", "next_module").prefetch_related("contents")
    )
    return _order_nodes(modules, "previous_module", "next_module", lambda module: module.pk or 0)


def get_ordered_contents(module: Module) -> List[Content]:
    """Return contents of a module ordered using their linked pointers."""
    contents = list(
        module.contents.select_related(
            "previous_content",
            "next_content",
            "material",
            "exam",
            "assignment",
        )
    )
    return _order_nodes(
        contents,
        "previous_content",
        "next_content",
        lambda content: (content.order or 0, content.pk or 0),
    )


@transaction.atomic
def rebuild_module_chain(course: Course) -> List[Module]:
    """Normalize previous/next pointers for modules inside a course."""
    ordered = get_ordered_modules(course)
    _rewrite_chain(ordered, "previous_module", "next_module")
    return ordered


@transaction.atomic
def rebuild_content_chain(module: Module) -> List[Content]:
    """Normalize previous/next pointers and order values for a module contents."""
    ordered = get_ordered_contents(module)
    _rewrite_chain(ordered, "previous_content", "next_content", order_attr="order")
    return ordered


def _swap_adjacent(left, right, prev_attr: str, next_attr: str) -> None:
    """Swap two adjacent nodes: left <-> right."""
    before_left = getattr(left, prev_attr)
    after_right = getattr(right, next_attr)

    setattr(right, prev_attr, before_left)
    setattr(right, next_attr, left)
    setattr(left, prev_attr, right)
    setattr(left, next_attr, after_right)

    updates = [
        (left, [prev_attr, next_attr]),
        (right, [prev_attr, next_attr]),
    ]

    if before_left:
        setattr(before_left, next_attr, right)
        updates.append((before_left, [next_attr]))

    if after_right:
        setattr(after_right, prev_attr, left)
        updates.append((after_right, [prev_attr]))

    for obj, fields in updates:
        obj.save(update_fields=fields)


@transaction.atomic
def append_module_to_course(course: Course, module: Module) -> Module:
    """Append a module at the end of the course linked list and save it."""
    ordered = rebuild_module_chain(course)
    tail = ordered[-1] if ordered else None

    module.course = course
    module.previous_module = tail
    module.next_module = None
    module.save()

    if tail and tail.next_module_id != module.pk:
        tail.next_module = module
        tail.save(update_fields=["next_module"])

    return module


@transaction.atomic
def append_content_to_module(module: Module, content: Content) -> Content:
    """Append a content block at the end of the module linked list and save it."""
    ordered = rebuild_content_chain(module)
    tail = ordered[-1] if ordered else None

    content.module = module
    content.previous_content = tail
    content.next_content = None
    content.order = len(ordered) + 1
    content.save()

    if tail and tail.next_content_id != content.pk:
        tail.next_content = content
        tail.save(update_fields=["next_content"])

    return content


@transaction.atomic
def move_module(module: Module, direction: str) -> bool:
    """Move a module one position up or down inside its course."""
    module = Module.objects.select_related(
        "previous_module", "next_module", "course"
    ).get(pk=module.pk)
    rebuild_module_chain(module.course)
    module = Module.objects.select_related(
        "previous_module", "next_module", "course"
    ).get(pk=module.pk)

    direction = direction.lower()
    if direction == "up":
        target = module.previous_module
        if not target or target.course_id != module.course_id:
            return False
        _swap_adjacent(target, module, "previous_module", "next_module")
        return True

    if direction == "down":
        target = module.next_module
        if not target or target.course_id != module.course_id:
            return False
        _swap_adjacent(module, target, "previous_module", "next_module")
        return True

    return False


@transaction.atomic
def move_content(content: Content, direction: str) -> bool:
    """Move a content block one position up or down inside its module."""
    content = Content.objects.select_related(
        "previous_content", "next_content", "module"
    ).get(pk=content.pk)
    rebuild_content_chain(content.module)
    content = Content.objects.select_related(
        "previous_content", "next_content", "module"
    ).get(pk=content.pk)

    direction = direction.lower()
    if direction == "up":
        target = content.previous_content
        if not target or target.module_id != content.module_id:
            return False
        _swap_adjacent(target, content, "previous_content", "next_content")
        rebuild_content_chain(content.module)
        return True

    if direction == "down":
        target = content.next_content
        if not target or target.module_id != content.module_id:
            return False
        _swap_adjacent(content, target, "previous_content", "next_content")
        rebuild_content_chain(content.module)
        return True

    return False
