# Database

## Schema

The usint.db database takes the following approach for formatting and documenting multiple different data types and multiple stages of parameter changes into a uniform table database. This approach closely mimics the design utilized in the original usint text files.

### Revision

#### Kinds

Every revision of an observation calls into one of four categories, the category in question recorded in the `kind` parameter of the revision entry.
- norm: A normal change to the observation parameters. This means that this revision entry will be linked to a set of original parameter values and a set of requested values.
- clone: a request to clone this observation. This is an atypical operation.
- remove: a request to remove the observation from the approved list. Given an obsid, the application will search for all corresponding revisions entries, and if the final revision is a `remove` request, then the observation is considered not approved.
- asis: a request to approve the observation. Given an obsid, the application will search for all corresponding revision entries, and if the final revision is an `asis` request, then the observation is considered approved. If no `asis` request is present for an obsid, then the default state of the observation is not approved.

### Original

To document the state of an observation in the ocat at the time of a `norm` revision. Every parameter of the ocat is fetched and written to the `originals` table with an individual `id`, a `revision_id` matching the corresponding `norm` revision of the parameter change request, the `parameter_id`, and the `value` of the parameter.

To save space and improve efficiency of the database entries, any parameter value that is `null` in the ocat at the time of a revision is not written to the `originals` table. Thus if we search for a specific parameter entry matching a specific revision in the originals table and do not find it, we know that the value is `null`.

### Request

The `requests` table builds off the `originals` table to define any parameter that is changed from the original state. It is also possible for a requested value to be `null`, which means that whatever `non-null` value for that parameter in the `originals` table should be cleared out from the `ocat`.
