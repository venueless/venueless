set shell := ["bash", "-euo", "pipefail", "-c"]
set quiet
set fallback
set default-list

uv_dev := "uv run --extra=dev"
py_src := "venueless tests"

# Sort imports with isort
[group('linting')]
[working-directory("server")]
isort *args=py_src:
    {{ uv_dev }} isort {{ args }}

# Format Python code with black
[group('linting')]
[working-directory("server")]
black *args=py_src:
    {{ uv_dev }} black {{ args }}

# Run flake8 linter
[group('linting')]
[working-directory("server")]
flake8 *args=py_src:
    {{ uv_dev }} flake8 {{ args }}

# Run eslint on the webapp, pass --fix to apply fixes
[group('linting')]
[working-directory("webapp")]
eslint *args:
    npx eslint . --ext .js,.ts,.vue {{ args }}

# Format and lint the server (isort runs before black, both rewrite the same files)
[group('linting')]
fmt-server: isort black flake8

# Format and lint everything
[group('linting')]
[parallel]
fmt: fmt-server (eslint "--fix") && fmt-done

[private]
fmt-done:
    echo '{{ GREEN }}Formatting complete{{ NORMAL }}'

# Run all code quality checks without changing files
[group('linting')]
[parallel]
check: (isort "--check" py_src) (black "--check" py_src) flake8 eslint && check-done

[private]
check-done:
    echo '{{ GREEN }}All checks passed{{ NORMAL }}'
