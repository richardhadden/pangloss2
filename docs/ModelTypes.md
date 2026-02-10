Model Types
===========

Node Types
----------

### `Document`
(SHOULD documents be nestable?)
Describes a top-level viewable document (maps to node)

Inbound types:
- Create
- Update

Outbound types:
- UpateView
    - ID, Label, created/modified,
- View
    - ID, Label, created/modified
- ReferenceView
    - ID, Label, containing doc ref/type??

### `SubDocument`
Describes a part of a viewable document (maps to node)

Inbound types:
- Create
- Update

Outbound types:
- UpdateView
    - ID, Label, created/modified,
- View
    - ID, Label, created/modified, incoming relations
- ReferenceView
    - ID, Label, containing doc ref/type

### `Entity`
Describes an Entity, referenceable by a document (maps to node)

Inbound types:
- Create
- Update
- ReferenceSet
- ReferenceCreate

Outbound types:
- UpdateView
    - ID, Label, created/modified,
- View
    - ID, Label, created/modified, incoming relations
- ReferenceView
    - ID, Label, containing doc ref/type

### `ReifiedRelation`
Describes a relation to an Entity via an intermediate node

Inbound types:

- Create
- Update

Outbound types:
- View/UpdateView
    - ID, Label incoming relations

### `ReifiedRelationDocument`
Same as ReifiedRelation, but with label and treated as SubDocument

Inbound types:
- Create
- Update

Outbound types:
- View/UpdateView
    - ID, Label, created/modified, incoming relations

### `Embedded`
Same as SubDocument, but treated as intrinsic part of container

Inbound types:
- Create
- Update

Outbound types:
- View/UpdateView

### `SemanticSpace`

Inbound types:
- Create
- Update

Outbound types:
- View/UpdateView

### `Conjunction`

Inbound types:
- Create
- Update

Outbound types:
- View/UpdateView

### `Relation`
APIS-style relation-as-node


PropertyClasses
---------------

### `list[T]`
Literal list of type T

### `AnnotatedLiteral[Value]`
Provides extra literal fields that are bound to the main value

### `typing.TypedDict`
Flattened and stored as keys


Special Classes
---------------

### `ViaEdge[Target, EdgeModel]`
Adds an edge of type EdgeModel to a relation

### `Traits`
Mixin classes adding extra fields and labels

### `Fulfils[T: Trait]`
Optionally include fields of a trait, that are fulfilled by being provided (thus adding label)

### DBField[...]
Labels a field as database-only (not returned by API), createable from existing fields on write

### APIField[...]
Labels a field as API-only (not in DB), createble from existing fields on read