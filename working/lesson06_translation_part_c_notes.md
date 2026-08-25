# Lesson 06 translation part C — decisions and corrections

- Scope: exactly `O006-PSU-007-S0121` through `O006-PSU-007-S0176` (56 text segments), in source order.
- Terminology follows the controlling glossary and lesson QA: **selang kepercayaan**, **besaran pivot**, **galat baku**, **rataan**, **nilai harapan**, **varians**, **khi-kuadrat**, **kuantil**, **fungsi pembangkit momen (MGF)**, and **Teorema Limit Pusat**. The Gamma shape/scale roles are explicit.
- `S0132` makes the intended Example 6.1 convention explicit: the chi-square subscript is a lower-tail probability. The displayed numerical endpoints remain unchanged.
- `S0144`–`S0155` apply L06-D005: exact unbiasedness is not required; asymptotically negligible bias is sufficient, and an estimated standard error must be consistent or supported by an equivalent studentization result. The studentized statistic is stated to converge in distribution to the standard Normal law.
- `S0161` and `S0166` label Example 6.2 as approximate. `S0165` states the corrected estimated standard error as 2. The frozen source math surface `M0098` is outside this text-segment map and contains the proved typo; its derivative rendering must be corrected to `estimated SE(xbar) = s/sqrt(64) = 16/8 = 2`, without the squared-SE symbol or 256.
- `S0175` qualifies the exact unknown-variance t interval: it requires an iid Normal sample and uses `df = n − 1`.
- Source typos and malformed prose encountered in this range were corrected in translation without altering source topology. Decimal constants, course identifier `STAT 414`, and capitalization distinctions such as Gamma/Normal were retained.
