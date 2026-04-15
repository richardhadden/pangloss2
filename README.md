# Pangloss

A Python framework mapping stupidly complex Pydantic models from API endpoints to a graph database.

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

## Creation Process

Two models are generated for Document, Entity, etc.: `Create` and `CreateDB`.

- `Create` is the model presented as the API endpoint
- `CreateDB` is the model used to write to the database, potentially containing more fields 
annotated as `DBField` and converted by the optional static method `<Model>.to_db_create` 
