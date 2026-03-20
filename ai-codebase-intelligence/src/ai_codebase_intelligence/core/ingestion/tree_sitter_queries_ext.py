from __future__ import annotations

CPP_QUERIES = """
; Classes, Structs, Namespaces
(class_specifier name: (type_identifier) @name) @definition.class
(struct_specifier name: (type_identifier) @name) @definition.struct
(namespace_definition name: (namespace_identifier) @name) @definition.namespace
(enum_specifier name: (type_identifier) @name) @definition.enum

; Functions & Methods
(function_definition declarator: (function_declarator declarator: (identifier) @name)) @definition.function
(function_definition declarator: (function_declarator declarator: (qualified_identifier name: (identifier) @name))) @definition.method

; Templates
(template_declaration (class_specifier name: (type_identifier) @name)) @definition.template
(template_declaration (function_definition declarator: (function_declarator declarator: (identifier) @name))) @definition.template

; Includes
(preproc_include path: (_) @import.source) @import

; Calls
(call_expression function: (identifier) @call.name) @call
(call_expression function: (field_expression field: (field_identifier) @call.name)) @call
(call_expression function: (qualified_identifier name: (identifier) @call.name)) @call
(call_expression function: (template_function name: (identifier) @call.name)) @call

; Heritage
(class_specifier name: (type_identifier) @heritage.class
  (base_class_clause (type_identifier) @heritage.extends)) @heritage
(class_specifier name: (type_identifier) @heritage.class
  (base_class_clause (access_specifier) (type_identifier) @heritage.extends)) @heritage
"""

CSHARP_QUERIES = """
; Types
(class_declaration name: (identifier) @name) @definition.class
(interface_declaration name: (identifier) @name) @definition.interface
(struct_declaration name: (identifier) @name) @definition.struct
(enum_declaration name: (identifier) @name) @definition.enum
(record_declaration name: (identifier) @name) @definition.record
(delegate_declaration name: (identifier) @name) @definition.delegate

; Namespaces
(namespace_declaration name: (identifier) @name) @definition.namespace
(namespace_declaration name: (qualified_name) @name) @definition.namespace

; Methods & Properties
(method_declaration name: (identifier) @name) @definition.method
(local_function_statement name: (identifier) @name) @definition.function
(constructor_declaration name: (identifier) @name) @definition.constructor
(property_declaration name: (identifier) @name) @definition.property

; Using
(using_directive (qualified_name) @import.source) @import
(using_directive (identifier) @import.source) @import

; Calls
(invocation_expression function: (identifier) @call.name) @call
(invocation_expression function: (member_access_expression name: (identifier) @call.name)) @call

; Heritage
(class_declaration name: (identifier) @heritage.class
  (base_list (simple_base_type (identifier) @heritage.extends))) @heritage
(class_declaration name: (identifier) @heritage.class
  (base_list (simple_base_type (generic_name (identifier) @heritage.extends)))) @heritage
"""

RUST_QUERIES = """
; Functions & Items
(function_item name: (identifier) @name) @definition.function
(struct_item name: (type_identifier) @name) @definition.struct
(enum_item name: (type_identifier) @name) @definition.enum
(trait_item name: (type_identifier) @name) @definition.trait
(impl_item type: (type_identifier) @name) @definition.impl
(mod_item name: (identifier) @name) @definition.module

; Type aliases, const, static, macros
(type_item name: (type_identifier) @name) @definition.type
(const_item name: (identifier) @name) @definition.const
(static_item name: (identifier) @name) @definition.static
(macro_definition name: (identifier) @name) @definition.macro

; Use statements
(use_declaration argument: (_) @import.source) @import

; Calls
(call_expression function: (identifier) @call.name) @call
(call_expression function: (field_expression field: (field_identifier) @call.name)) @call
(call_expression function: (scoped_identifier name: (identifier) @call.name)) @call
(call_expression function: (generic_function function: (identifier) @call.name)) @call

; Heritage (trait implementation)
(impl_item trait: (type_identifier) @heritage.trait type: (type_identifier) @heritage.class) @heritage
(impl_item trait: (generic_type type: (type_identifier) @heritage.trait) type: (type_identifier) @heritage.class) @heritage
"""

PHP_QUERIES = """
(namespace_definition name: (namespace_name) @name) @definition.namespace
(class_declaration name: (name) @name) @definition.class
(interface_declaration name: (name) @name) @definition.interface
(trait_declaration name: (name) @name) @definition.trait
(enum_declaration name: (name) @name) @definition.enum
(function_definition name: (name) @name) @definition.function
(method_declaration name: (name) @name) @definition.method
(property_declaration (property_element (variable_name (name) @name))) @definition.property
(namespace_use_declaration (namespace_use_clause (qualified_name) @import.source)) @import
(function_call_expression function: (name) @call.name) @call
(member_call_expression name: (name) @call.name) @call
(nullsafe_member_call_expression name: (name) @call.name) @call
(scoped_call_expression name: (name) @call.name) @call
(class_declaration name: (name) @heritage.class (base_clause [(name) (qualified_name)] @heritage.extends)) @heritage
(class_declaration name: (name) @heritage.class (class_interface_clause [(name) (qualified_name)] @heritage.implements)) @heritage.impl
(class_declaration name: (name) @heritage.class body: (declaration_list (use_declaration [(name) (qualified_name)] @heritage.trait))) @heritage
"""

KOTLIN_QUERIES = """
(class_declaration "interface" (type_identifier) @name) @definition.interface
(class_declaration "class" (type_identifier) @name) @definition.class
(object_declaration (type_identifier) @name) @definition.class
(companion_object (type_identifier) @name) @definition.class
(function_declaration (simple_identifier) @name) @definition.function
(property_declaration (variable_declaration (simple_identifier) @name)) @definition.property
(enum_entry (simple_identifier) @name) @definition.enum
(type_alias (type_identifier) @name) @definition.type
(import_header (identifier) @import.source) @import
(call_expression (simple_identifier) @call.name) @call
(call_expression (navigation_expression (navigation_suffix (simple_identifier) @call.name))) @call
(constructor_invocation (user_type (type_identifier) @call.name)) @call
(infix_expression (simple_identifier) @call.name) @call
(class_declaration (type_identifier) @heritage.class (delegation_specifier (user_type (type_identifier) @heritage.extends))) @heritage
(class_declaration (type_identifier) @heritage.class (delegation_specifier (constructor_invocation (user_type (type_identifier) @heritage.extends)))) @heritage
"""

SWIFT_QUERIES = """
(class_declaration "class" name: (type_identifier) @name) @definition.class
(class_declaration "struct" name: (type_identifier) @name) @definition.struct
(class_declaration "enum" name: (type_identifier) @name) @definition.enum
(class_declaration "extension" name: (user_type (type_identifier) @name)) @definition.class
(class_declaration "actor" name: (type_identifier) @name) @definition.class
(protocol_declaration name: (type_identifier) @name) @definition.interface
(typealias_declaration name: (type_identifier) @name) @definition.type
(function_declaration name: (simple_identifier) @name) @definition.function
(protocol_function_declaration name: (simple_identifier) @name) @definition.method
(init_declaration) @definition.constructor
(property_declaration (pattern (simple_identifier) @name)) @definition.property
(import_declaration (identifier (simple_identifier) @import.source)) @import
(call_expression (simple_identifier) @call.name) @call
(call_expression (navigation_expression (navigation_suffix (simple_identifier) @call.name))) @call
(class_declaration name: (type_identifier) @heritage.class (inheritance_specifier inherits_from: (user_type (type_identifier) @heritage.extends))) @heritage
(protocol_declaration name: (type_identifier) @heritage.class (inheritance_specifier inherits_from: (user_type (type_identifier) @heritage.extends))) @heritage
"""
