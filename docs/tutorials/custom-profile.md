# Creating a Custom Profile

This tutorial guides you through creating a custom profile for your specific needs.

## Steps

1.  **Navigate to the profiles directory:**
    ```bash
    cd configurator/profiles
    ```

2.  **Create a new YAML file:**
    Create a file named `my-custom-profile.yaml`.

3.  **Define your settings:**
    ```yaml
    name: "My Custom Profile"
    description: "Personalized setup for Python dev"
    extends: "intermediate"
    modules:
      python:
        version: "3.12"
        poetry: true
      docker:
        enabled: true
    ```

4.  **Use your profile:**
    ```bash
    vps-configurator install --profile my-custom-profile
    ```
