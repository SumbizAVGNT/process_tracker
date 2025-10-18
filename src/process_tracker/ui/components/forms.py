from __future__ import annotations
"""
Compatibility shim:

Некоторый код обращается к `process_tracker.ui.components.forms`.
Этот модуль-алиас реэкспортирует компоненты из dynamic_form/form_field/password_field.
"""

from .dynamic_form import DynamicForm, build_schema_fields
from .form_field import TextField, EmailField, IntegerField
from .password_field import PasswordField

__all__ = [
    "DynamicForm",
    "build_schema_fields",
    "TextField",
    "EmailField",
    "IntegerField",
    "PasswordField",
]
