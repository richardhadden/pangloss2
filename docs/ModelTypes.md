Model Types
===========

Node Types
----------

### `Document`
Describes a top-level viewable document (maps to node)

Action types:
- [] Create
- [] EditSet

- [] View
- [] EditView
- [] ReferenceView

### `SubDocument`
Describes a part of a viewable document (maps to node)

Action types:
- [] Create
- [] EditSet

- [] EditView
- [] View
- [] ReferenceView

### `Entity`
Describes an Entity, referenceable by a document (maps to node)

### `ReifiedRelation`
Describes a relation to an Entity via an intermediate node

### `ReifiedRelationDocument`
Same as ReifiedRelation, but with label and treated as SubDocument

### `Embedded`
Same as SubDocument, but treated as intrinsic part of 

### `SemanticSpace`

### `Conjunction`

### `Relation`
APIS-style relation-as-node


PropertyClasses
---------------

### list[T]
Literal list of type T

### AnnotatedLiteral[Value]
Provides extra literal fields that are bound to the main value

### typing.TypedDict
Flattened and stored as keys


Special Classes
---------------

### ViaEdge[Target, EdgeModel]
Adds an edge of type EdgeModel to a relation

### Traits
Mixin classes adding extra fields and labels

### Fulfils[T: Trait]
Optionally include fields of a trait, that are fulfilled by being provided (thus adding label)