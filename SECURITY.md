# Security and safe use

## Reporting

Do not put credentials, real response bodies, exploit details affecting live
systems, or personal data in a public issue. Use the repository's **Security →
Report a vulnerability** private reporting feature when enabled. If unavailable,
ask a maintainer for a private channel without posting the sensitive details.
Maintainers should enable private reporting before making the repository public.
No response-time SLA or security-support commitment is implied.

## Boundaries

- Respondo parses data; it does not sanitize HTML or establish that a URL is safe
  to fetch. Use output-context escaping, URL allowlists and an SSRF policy in the
  application that consumes extracted values.
- HTML selectors and JSONPath queries support documented subsets. They do not
  execute JavaScript or expressions. HTMLParser does not reproduce browser DOM
  recovery or CSS visibility rules.
- XML parsing rejects DTDs, limits input bytes, nesting and resolved-base growth.
  Keep Python and its Expat library patched; library limits do not replace
  process memory/time limits. Python 3.9 compatibility is not a recommendation
  to run an unsupported runtime against hostile documents.
- CSV export prefixes formula-like strings by default, including column names.
  That changes values and is not a universal guarantee for all spreadsheet
  programs. `escape_formulas=False` / `--raw-csv` is only for trusted consumers.
- `decode_jwt` does **not** authenticate a token or check signatures, issuer,
  audience, expiry or authorization. Never trust its decoded claims by themselves.
- Encoding, hashing and random helpers have different purposes. Base64 is not
  encryption; MD5/SHA-1 are not suitable for security-sensitive integrity or
  password storage. Use established authentication/password libraries.
- Optional AI functions transmit prompts and source text to the chosen provider.
  Send only approved data. Supply credentials via a secret manager/runtime
  environment, never source code or committed `.env` files. Provider availability,
  models and schema enforcement vary; validate outputs and handle empty failures.
  The legacy AI API returns empty results on many failures for compatibility;
  opt into `strict=True` for fixed `AIError` categories and optional HTTP status.
  There is no built-in model: set the provider's `*_MODEL` variable or `model=`.
  Schemas are forwarded but are not validated locally against generated output.
  Authenticated requests refuse redirects to avoid forwarding credentials to a
  different destination; redirects surface as sanitized HTTP failures.
- The CLI never fetches URLs or calls AI. It buffers its input/results, so use
  suitable file/process limits for large jobs. Diagnostics omit source contents.
- Batch mode limits selected files, input and staged output bytes, rejects links
  and non-regular selected files, and never overwrites an output destination.
  It materializes one extraction at a time; input/output limits do not bound
  parser memory/CPU amplification. Temporary output contains extracted data and
  is closed on completion/failure. Protect the OS temp directory. Filesystem
  identity checks are not a sandbox against concurrent hostile path mutation.
- Legacy `Response.save*` methods can overwrite the explicit destination and
  report failures as `False`. Validate paths and check their return values.

Use captcha/bot-protection identification helpers only where authorized. They
identify challenge metadata; they do not grant access or solve challenges.
