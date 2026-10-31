# Contributing

Corrections to the docs and examples are welcome as issues or pull requests. Changes to the contract (`specs/`) and to the service contract (`website/docs/service/`) are made by Patternode; propose them in an issue.

1. Fork, branch, and change. If you change an example, its test must still pass: `python -m unittest discover -s examples/python/tests`.
2. Build the site if you changed a page: `cd website && npm ci && npm run build`.
3. Open a pull request into `main` and fill in its template.

Never include an API key, real data, or your customer's name. This repository is public.

By contributing you agree that your contribution is licensed as the file it changes is: Apache 2.0 for code, specs and configuration, CC BY 4.0 for `website/docs/`.
