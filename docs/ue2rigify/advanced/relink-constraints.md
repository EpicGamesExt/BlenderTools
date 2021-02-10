---
layout: default
---

# Relink Constraints
[UE to Rigify Costumization](https://docs.blender.org/manual/en/latest/addons/rigging/rigify/rig_types/basic.html)

Allows retargeting constraints belonging to the bone to point at bones created in the process of generating the rig, thus allowing custom rigging to integrate with generated bones.

To use this feature, add `@` and the intended target bone name to the constraint name, resulting in the `...@bone_name` syntax. After all bones of the rig are generated, the constraint target bone will be replaced. If the new bone name is just `CTRL`, `MCH` or `DEF`, this will just replace the `ORG` prefix in the existing target bone name. For the Armature constraint you can add a `@` suffix for each target, or just one `@CTRL`, `@MCH` or `@DEF` suffix to update all.

![1]( {{ '/assets/images/ue2rigify/advanced/relink-constraints/1.jpg' | relative_url }} )

### Parent
If the field is not empty, applies the same name substitution logic to the parent of the bone.

![2]( {{ '/assets/images/ue2rigify/advanced/relink-constraints/2.jpg' | relative_url }} )

When this feature is enabled, the bone will not be automatically parented to the root bone even if it has no parent; enter root in the Parent field if that is necessary.


