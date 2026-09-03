## Cryptocurrency Obfuscation Techniques & Project Coverage

| Technique                             | What happens                                                                              | Our Current Project                                                                               |
| ------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Multiple wallets / wallet hopping** | Funds move through many addresses to make tracing harder.                                 | 🟢 **Handles**                                                                                    |
| **Splitting funds**                   | One amount is divided and sent to multiple wallets.                                       | 🟢 **Partially handles**                                                                          |
| **Consolidating funds**               | Multiple wallets send funds into a single wallet.                                         | 🟢 **Handles**                                                                                    |
| **Token transfers**                   | Criminals move funds using ERC-20 tokens instead of native ETH.                           | 🟢 **Handles**                                                                                    |
| **Internal transactions**             | ETH moves through smart-contract calls/internal transactions.                             | 🟢 **Handles**                                                                                    |
| **Known exchange / VASP**             | Funds reach a known exchange or Virtual Asset Service Provider (VASP).                    | 🟢 **Handles**                                                                                    |
| **Known mixer**                       | Funds are sent to an address identified as a known mixer.                                 | 🟢 **Can identify if address is known**                                                           |
| **Bridge**                            | Funds are moved from one blockchain to another through a bridge.                          | 🟡 **Detects conceptually, but current engine does not fully trace cross-chain movement**         |
| **Cross-chain movement**              | Funds move between different blockchains, e.g., Ethereum → TRON/BTC.                      | 🔴 **Not yet fully supported**                                                                    |
| **Unknown / private wallet**          | The destination wallet has no known identity or label.                                    | 🟡 **Traces the wallet, but attribution may remain `Unknown`**                                    |
| **Rapid transfers**                   | Funds quickly hop between multiple addresses within a short period.                       | 🟡 **Transaction timestamps are available; advanced behavioral detection is not yet implemented** |
| **Fan-out / fan-in patterns**         | Funds are split across many wallets and later merged, or many wallets send to one wallet. | 🟡 **Graph can represent it; dedicated pattern detector is not yet implemented**                  |
| **Mixer obfuscation**                 | A mixer breaks the direct relationship between the deposit and withdrawal addresses.      | 🔴 **Cannot reliably reconstruct ownership**                                                      |
| **Privacy-focused chains**            | Blockchain transaction visibility is intentionally limited.                               | 🔴 **Not currently handled**                                                                      |
| **Off-chain movement**                | Funds leave the blockchain ecosystem through non-blockchain mechanisms.                   | 🔴 **Cannot trace from blockchain data alone**                                                    |

### Legend

- 🟢 **Handles** — Currently supported by the attribution engine.
- 🟡 **Partial / Conceptual** — Some relevant information or graph representation exists, but full automated detection/tracing is not implemented.
- 🔴 **Not supported** — Outside the current engine's reliable tracing capabilities.
