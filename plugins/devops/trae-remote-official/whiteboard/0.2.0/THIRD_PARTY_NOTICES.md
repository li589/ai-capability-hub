# Third-Party Notices

This internal host-validation package includes a compiled, self-contained
Whiteboard editor derived from the following direct runtime dependencies:

| Component | Version | Declared license |
| --- | --- | --- |
| `@excalidraw/excalidraw` | 0.18.0 | MIT |
| `react` | 18.3.1 | MIT |
| `react-dom` | 18.3.1 | MIT |

The compiled editor also contains transitive JavaScript and embedded font
assets inherited from Excalidraw, including Excalifont, Comic Shanns, Cascadia
Code, Liberation Sans, Lilita, Nunito, Virgil, and Xiaolai subsets.

This file is an engineering inventory, not final legal clearance. Before
external distribution:

1. regenerate the complete dependency and font bill of materials from the
   source repository lockfile and built asset;
2. include every required license text and attribution;
3. verify the exact Excalidraw release and all embedded font redistribution
   terms; and
4. complete legal review for the intended distribution channel.

The first-run CLI dependency is not copied into this Plugin. Its top-level
package is fixed at `mcp-excalidraw-server@1.1.0`, which declares the MIT
license, while npm resolves that package's transitive dependency graph at
install time. Its transitive notices remain the responsibility of that
installed package until a locked offline runtime is produced.
