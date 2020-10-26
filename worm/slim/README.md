The SLIM interpreter is broken into multiple phases.

1. Parser: Converting raw input into a list of semantic lines.
2. Namer: Associating labels with lines and register names with their indices.
3. Resolver: Verifying opcodes are real, and mapping labels and registers to integers.
