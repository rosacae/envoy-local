# envoy-local

> CLI tool to manage and sync local `.env` files across projects with secret redaction support.

---

## Installation

```bash
pip install envoy-local
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envoy-local
```

---

## Usage

```bash
# Initialize envoy in your project
envoy init

# Sync .env file from a shared source
envoy sync --source s3://my-bucket/configs/.env.production

# Push local .env to shared source with secrets redacted
envoy push --redact SECRET_KEY,DATABASE_URL

# List all tracked variables
envoy list

# Diff local .env against remote
envoy diff --source s3://my-bucket/configs/.env.production
```

### Example `.envoy.yml` config

```yaml
source: s3://my-bucket/configs/.env.production
redact:
  - SECRET_KEY
  - API_TOKEN
  - DATABASE_URL
```

---

## Features

- 🔄 Sync `.env` files across multiple projects
- 🔒 Automatic secret redaction before sharing or committing
- 📂 Supports local paths, S3, and remote URLs as sources
- 🧩 Simple YAML-based project configuration

---

## License

This project is licensed under the [MIT License](LICENSE).