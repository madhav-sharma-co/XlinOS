<!-- SPDX-FileCopyrightText: 2026 Axion Co. -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Licensing and notices

XlinOS will integrate components with different copyright holders and licences. The repository's own licence does not replace component licences.

## Before distributing an image

- Preserve the Xlin kernel's Linux licensing terms and notices.
- Inventory userspace packages, bootloader components, firmware blobs and tools.
- Record package name, version, source, licence expression and required notices/source offer.
- Include applicable licence texts and attribution notices in distribution materials.
- Review firmware and trademark restrictions separately.
- Generate and retain an SBOM for every release candidate.
- Review the distribution model before public binary redistribution.

New documentation should include SPDX headers. New scripts and source files must select an appropriate licence and include the corresponding identifier. Do not add a blanket licence until the project owner selects one for the repository and its file classes.

No XlinOS image is currently distributed. The userspace, bootloader and package set are not selected, so a complete image-level licence inventory is not yet possible.
