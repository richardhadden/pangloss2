# How to do `Fufils[PersonInLocation]` with multiple persons/locations

PersonInLocation specifies Person and Location fields

If fulfilling class has only *one* set of overridden fields for Person and Location,
make fulfilling class a subclass of PersonInLocation and add additional edges

If *more than one* field overridden by Person/Location, i.e.

letter send from = PersonA,LocationA

letter sent to = PersonB,LocationB

- Declare these as tuples
- Create multiple PersonInLocation nodes, pointing via a `fulfilled_by` edge, and return
the target of this edge during query


# Can we add `PersonInLocation` to individual persons?