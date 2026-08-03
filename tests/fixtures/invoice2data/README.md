# Pinned invoice2data fixtures

These files were copied unchanged from `invoice-x/invoice2data` at commit
`c4cb921087a932513b381245e20fbe124cce4c0e` for the fixed LedgerLens benchmark.
They are test evidence, not client data.

| File | SHA-256 | Benchmark use |
| --- | --- | --- |
| `coolblue1.pdf` | `3932539B71338F0C73D6ADE499A2A00CD2F9056C60F5A87B1EF623AF095E1607` | text-layer fields and line items |
| `AmazonWebServices.pdf` | `2E21D50F59A97B8C3778B238D14C9D7D15F74B8D021F819F1D2EDE1F5412F81B` | text-layer counterpart |
| `AmazonWebServices.png` | `FEC56E365019C348986BFE1A6C16DB13B1D16FC5962BE83835BB4AC533466D6C` | deterministic image-only PDF source |

The expected values are intentionally limited to stable invoice identifiers,
amounts, and named items used by the tests. Passing these fixtures does not
establish arbitrary-layout or production OCR accuracy.
