# Lesson 11 protected-mathematics audit

The frozen semantic main contains 264 mathematics nodes: 209 inline and 55
display. Their ordered source-text aggregate SHA-256 is
`cadc74feeb0269a091b90cdd8f6e1cfc13065dfd4dbec72dab008a03e681a0a7`.
Authority bytes are unchanged.

Five target mathematics nodes receive registered repairs:

| Stable math ID | Frozen expression | Target expression | Finding |
|---|---|---|---|
| `O006-PSU-012-M0057` | `∫_{-∞}^{∞} … dθ` | `∫_Θ … dθ` | L11-D004: arbitrary parameter support |
| `O006-PSU-012-M0118` | `k_1(p)` | `k_1(y)` | L11-D006: wrong argument |
| `O006-PSU-012-M0134` | `Γ(4+y)/(Γ(4)Γ(y+1))` | `Γ(5+y)/(Γ(4)Γ(y+1))` | L11-D007: Beta normalizer |
| `O006-PSU-012-M0253` | second coefficient `35/4` | second coefficient `140` | L11-D015: Beta(4,4) density |
| `O006-PSU-012-M0263` | `g(y|θ)/k_1(y)` | `g(y|θ)h(θ)/k_1(y)` | L11-D016: omitted prior |

Every other mathematics node must remain text-identical to the normalized
authority. The corrected target aggregate must therefore differ only at these
five stable IDs. The R results are not mathematics-node edits: their frozen
code/output text remains unchanged and receives only an additive runtime
contract.
