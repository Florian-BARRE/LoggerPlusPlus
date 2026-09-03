# Changelog

## [1.1.0](https://github.com/Florian-BARRE/LoggerPlusPlus/compare/loggerplusplus-v1.0.5...loggerplusplus-v1.1.0) (2026-09-03)


### Features

* add_json() — structured (NDJSON) logging (A4) ([471693e](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/471693e0e1fe5bc812b7f4fbc31e7339890ac468))
* async-aware log_timing / log_io decorators (A3) ([e11edd4](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/e11edd4d0b7c0161e1cd96d19a71751f402dabb1))
* correlation context — bind_context / new_id / otel_context (A5) ([83353cc](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/83353cc14f8ca80d0e6c5236afdc6cae9398c1a2))
* cross-process auto-width alignment via export/import (B10) ([2afe014](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/2afe01460349a2dc25e22ced064dc7c5ba0c492c))
* enriched decorators and color themes (bug-hunt hardened) ([0296c2b](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/0296c2b09e0b935e7a069f5ba189867ad4d8e1b7))
* intercept_std_logging() — bridge standard-library logging into loguru (A1) ([a4113c8](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/a4113c8fc53796ce7078cf2ddabe6f901af9dbfe))
* setup() and configure_from_env() — one-call logging bootstrap (A2) ([8bfebb5](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/8bfebb59e94ccb8a304e09b4da00ea22eb6fa6c5))
* ship a PEP 561 py.typed marker ([33ccab9](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/33ccab9a484bd8b0e798336d4e3bb49f6890f933))
* uncolored file formats (PlainFormat, FileFormat) and a testing capture helper (A6, A7) ([402c9ab](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/402c9ab106964f70dcf6d26ed382730759b60703))
* visual-width auto-alignment, bounded/resettable registry, control-char safety ([6160e55](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/6160e552d89f831eb06d3f35d0e479c914121204))


### Bug Fixes

* address A1-A3 integration bug-hunt findings ([c961258](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/c9612585f1f39ba3ee54ac27976699a2886864ed))
* correct auto-width pipeline bugs and harden the test suite ([46cfafd](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/46cfafdc7c71963ffcea37cc3d8d2056282d50de))
* correct packaging metadata and modernize the build/release pipeline ([8780b2e](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/8780b2ea0c85e659df86437a892ed71877c5ec4c))
* harden add_json and otel_context against bug-hunt findings ([e7e25a6](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/e7e25a6909606bd16509bf3f681c6ee0eb189638))


### Documentation

* professional README overhaul and a dedicated docs/ folder ([5c5b34f](https://github.com/Florian-BARRE/LoggerPlusPlus/commit/5c5b34f43b47b1685f82720553a208f9f9c07271))

## Changelog

All notable changes to this project are documented here. This file is maintained automatically
by [release-please](https://github.com/googleapis/release-please) from
[Conventional Commits](https://www.conventionalcommits.org/); do not edit released sections by hand.
