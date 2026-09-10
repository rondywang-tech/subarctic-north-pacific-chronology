# Code reuse boundaries

- Status: `PARTIAL_NOT_END_TO_END_VALIDATED`.
- The public package contains code only; it intentionally omits formal inputs and scientific tables while PANGAEA controls access.
- Data-dependent stages require the PANGAEA.996868 data/input package.
- Historical absolute paths and environment assumptions must be adapted by the user.
- This release has not been clean-room tested as a one-command v7 rebuild.
- Publication-sanitized files are identified in `CODE_FILE_MANIFEST.csv`; they must not be described as byte-identical historical copies.
- Posterior draws are not included in v1.0.
