# Code Standards

This document outlines the coding standards and linting rules for the Amazon Q Business Agentic Connectors project.

## Python Code Standards

### Tools Used

- **Black**: Code formatter that enforces a consistent style
- **isort**: Import sorter that organizes imports according to PEP8
- **flake8**: Linter that checks for style and potential errors
- **pylint**: Static code analyzer that looks for errors and enforces a coding standard

### Setting Up the Development Environment

To avoid conflicts with system Python packages, we recommend using a virtual environment:

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install the required linting tools
pip install black isort flake8 pylint
```

### Configuration Files

- `.pylintrc`: Configuration for pylint
- `.flake8`: Configuration for flake8
- `pyproject.toml`: Configuration for black and isort

### Running Linting Tools

```bash
# Activate the virtual environment first
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Format code with black
black .

# Sort imports with isort
isort .

# Check for style issues with flake8
flake8 .

# Check for code issues with pylint
pylint --recursive=y .
```

### Automatic Linting

A pre-commit hook is set up to automatically run these tools on staged Python files before committing. To enable it:

```bash
chmod +x .git/hooks/pre-commit
```

Note: The pre-commit hook requires the linting tools to be installed in your environment. If you're using a virtual environment, make sure it's activated before committing.

### Linting Script

A script is provided to automatically fix common linting issues:

```bash
# Activate the virtual environment first
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Run the linting script
python lint_fix.py
```

## TypeScript Code Standards

For TypeScript code in the CDK infrastructure, we use ESLint and Prettier to ensure consistent code style and quality.

### Tools Used

- **ESLint**: Linter that checks for code quality issues and enforces coding standards
- **Prettier**: Code formatter that ensures consistent code style
- **TypeScript**: Strongly typed programming language that builds on JavaScript

### Setting Up the TypeScript Development Environment

```bash
# Navigate to the CDK infrastructure directory
cd connector-plugin-infra-setup

# Install the required linting tools
npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin eslint-plugin-import eslint-config-prettier eslint-plugin-prettier prettier
```

### Configuration Files

- `.eslintrc.js`: Configuration for ESLint
- `.prettierrc`: Configuration for Prettier

### Running TypeScript Linting Tools

```bash
# Navigate to the CDK infrastructure directory
cd connector-plugin-infra-setup

# Format code with Prettier
npx prettier --write "**/*.ts"

# Check for style issues with ESLint
npx eslint "**/*.ts"

# Fix auto-fixable issues with ESLint
npx eslint --fix "**/*.ts"
```

### TypeScript Coding Guidelines

1. **Use `unknown` instead of `any`**: When the type is not known, use `unknown` instead of `any` for better type safety
2. **Avoid unused variables**: Remove or prefix unused variables with underscore (_)
3. **Organize imports**: Group imports by standard library, third-party, and local
4. **Use proper naming conventions**: 
   - Use PascalCase for classes, interfaces, types, and enums
   - Use camelCase for variables, functions, and methods
   - Use UPPER_CASE for constants
5. **Add proper JSDoc comments**: Document functions, classes, and complex code blocks

## General Guidelines

1. **Docstrings**: All functions and classes should have docstrings
2. **Line Length**: Maximum line length is 120 characters
3. **Imports**: Imports should be organized in groups (standard library, third-party, local)
4. **Naming Conventions**: 
   - Use snake_case for variables and functions in Python
   - Use PascalCase for classes
   - Use UPPER_CASE for constants
5. **Error Handling**: Always use specific exception types when possible
6. **Comments**: Add comments for complex logic
7. **Type Hints**: Use type hints where appropriate

## Security Best Practices

1. **Input Validation**: Always validate and sanitize user input
2. **Secure Coding**: Follow secure coding practices
3. **Dependency Management**: Use exact versions for dependencies
4. **Credentials**: Never hardcode credentials
5. **Error Messages**: Avoid exposing sensitive information in error messages

## Troubleshooting

### Common Issues

1. **"Command not found" errors**: Make sure your virtual environment is activated.

2. **"externally-managed-environment" error**: If you see this error when trying to install packages:
   ```
   error: externally-managed-environment
   ```
   This means you're trying to install packages in a system Python environment. Use a virtual environment as described above.

3. **Pre-commit hook failures**: If the pre-commit hook fails, you can:
   - Fix the issues manually and try again
   - Use `CODE_DEFENDER_SKIP_LOCAL_HOOKS=true git commit -m "your message"` to skip the hooks temporarily
   - Make sure your virtual environment is activated before committing

4. **ESLint version compatibility issues**: If you see warnings about unsupported engines:
   ```
   npm WARN EBADENGINE Unsupported engine
   ```
   You may need to update your Node.js version or use a specific version of ESLint that's compatible with your Node.js version.
