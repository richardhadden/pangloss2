# Pangloss

A Python framework for defining and initializing rich domain models.

## Initialization Process

Pangloss models (Documents, Entities, Traits, Relations, etc.) are registered as they are defined. Registration is handled by **`ModelManager`**, which maintains a central registry of all declared model types.

### Why deferred initialization?

Many models refer to each other (e.g., a `Document` has a field typed as an `Entity`). Since Python evaluates class bodies in definition order, some referenced types might not yet exist when a model is first defined. To handle this, Pangloss:

1. Registers every model class as it is defined.
2. Attempts to rebuild each model using Pydantic once new types are available.
3. Only runs field-definition initialization when all dependencies are resolved.

### Key components

- **`ModelManager`**: central registry tracking declared models and trying to initialise them as soon as possible.
- **`initialise_field_definitions`**: builds the field definitions for a model once it is complete.
- **`try_initialise_all_models()`**: called on each new model registration; it attempts to rebuild and initialise any models that are ready.

## Getting Started

... (add more docs here as needed) ...
