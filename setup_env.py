import os
import platform
import subprocess
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

ENV_VARIABLES = {
    "TELEGRAM_BOT_TOKEN": {
        "env": "WIKIFEATTOKEN",
        "default": "",
        "secret": True,
    },
    "TELEGRAM_BOT_TEST_TOKEN": {
        "env": "WIKIFEATTESTTOKEN",
        "default": "",
        "secret": True,
    },
    "TELEGRAM_PROXY": {
        "env": "TELEGRAM_PROXY",
        "default": "",
        "secret": False,
    },
    "OWNER_ID": {
        "env": "TELEGRAM_ID_OWNER",
        "default": "0",
        "secret": False,
    },
    "ENSURE_BOT_RUNNING": {
        "env": "WIKIFEATENSUREBOTRUNNING",
        "default": "",
        "secret": False,
    },
    "DB_USER": {
        "env": "WIKIFEAT_DB_USER",
        "default": "postgres",
        "secret": False,
    },
    "DB_PASSWORD": {
        "env": "WIKIFEAT_DB_PASSWORD",
        "default": "",
        "secret": True,
    },
    "DB_NAME": {
        "env": "WIKIFEAT_DB_NAME",
        "default": "wikifeat",
        "secret": False,
    },
    "DB_TEST_NAME": {
        "env": "WIKIFEAT_DB_TEST_NAME",
        "default": "wikifeattest",
        "secret": False,
    },
    "DB_HOST": {
        "env": "WIKIFEAT_DB_HOST",
        "default": "127.0.0.1",
        "secret": False,
    },
    "DB_MIN_SIZE": {
        "env": "WIKIFEAT_DB_MIN_SIZE",
        "default": "1",
        "secret": False,
    },
    "DB_MAX_SIZE": {
        "env": "WIKIFEAT_DB_MAX_SIZE",
        "default": "10",
        "secret": False,
    },
}


# ============================================================
# ENVIRONMENT
# ============================================================

def set_env_variable(key: str, value: str) -> bool:
    """Permanently sets an environment variable for the current user."""

    os_name = platform.system().lower()

    if os_name == "windows":
        try:
            subprocess.run(
                ["setx", key, value],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to set {key} using setx: {e}")
            return False

    elif os_name == "linux":
        env_dir = Path.home() / ".config" / "environment.d"
        env_dir.mkdir(parents=True, exist_ok=True)

        config_file = env_dir / "user_vars.conf"

        content = []

        if config_file.exists():
            content = config_file.read_text().splitlines()

        content = [
            line
            for line in content
            if not line.startswith(f"{key}=")
        ]

        content.append(f"{key}={value}")

        config_file.write_text("\n".join(content) + "\n")

    elif os_name == "darwin":
        shell_files = (
            Path.home() / ".zshrc",
            Path.home() / ".bash_profile",
            Path.home() / ".profile",
        )

        export_line = f'export {key}="{value}"'

        for file_path in shell_files:
            content = []

            if file_path.exists():
                content = file_path.read_text().splitlines()

            content = [
                line
                for line in content
                if not (
                        line.startswith(f"export {key}=")
                        or line.strip() == f"export {key}"
                )
            ]

            content.append(export_line)
            file_path.write_text("\n".join(content) + "\n")

    else:
        print(
            f"Operating system {platform.system()} is not supported."
        )
        return False

    return True


def apply_variable(env_name: str, value: str) -> bool:
    """Sets a variable permanently and in the current process."""

    os.environ[env_name] = value
    return set_env_variable(env_name, value)


# ============================================================
# HELPERS
# ============================================================

def get_current_value(env_name: str, default: str = "") -> str:
    return os.getenv(env_name, default)


def display_value(value: str, secret: bool) -> str:
    if not value:
        return "<not set>"

    if secret:
        return "*" * min(len(value), 12)

    return value


def is_secret(env_name: str) -> bool:
    return any(
        variable["env"] == env_name and variable["secret"]
        for variable in ENV_VARIABLES.values()
    )


def ask_value(
        name: str,
        env_name: str,
        default: str,
        secret: bool,
) -> str:
    current = get_current_value(env_name, default)

    value = input(
        f"{name} [{display_value(current, secret)}]: "
    )

    return value if value else current


def get_env_names():
    return {
        variable["env"]
        for variable in ENV_VARIABLES.values()
    }


# ============================================================
# ENV FILE
# ============================================================

def parse_env_file(file_path: Path) -> dict[str, str]:
    """Reads KEY=VALUE pairs from an .env file."""

    values = {}

    for line in file_path.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)

        values[key] = value

    return values


def save_env_file(
        values: dict[str, str],
        file_path: Path,
):
    """Writes environment variables to an .env file."""

    lines = []

    for key, value in values.items():
        if "\n" in value:
            raise ValueError(
                f"Environment variable {key} contains a newline."
            )

        if any(char in value for char in " #"):
            value = f'"{value}"'

        lines.append(f"{key}={value}")

    file_path.write_text("\n".join(lines) + "\n")


def get_config_files():
    return sorted(SCRIPT_DIR.glob("*.env"))


# ============================================================
# INTERACTIVE SETUP
# ============================================================

def configure_general():
    print()
    print("=== General variables ===")
    print()

    for name, config in ENV_VARIABLES.items():
        if name.startswith("DB_") or name == "TELEGRAM_PROXY":
            continue

        value = ask_value(
            name,
            config["env"],
            config["default"],
            config["secret"],
        )

        apply_variable(config["env"], value)

    configure_proxy()

    print()
    print("General variables configured.")


def configure_proxy():
    env_name = "TELEGRAM_PROXY"
    current = os.getenv(env_name, "")

    print()
    print("=== Telegram proxy ===")
    print()

    if current:
        print(f"Current proxy: {current}")
        print()
        print("1. Keep current proxy")
        print("2. Change proxy")
        print("3. Disable proxy")
        print("0. Skip")

        choice = input("> ").strip()

        if choice == "1":
            return

        if choice == "2":
            value = input("Proxy URL: ").strip()

            if value:
                apply_variable(env_name, value)
                print("Telegram proxy updated.")
            return

        if choice == "3":
            apply_variable(env_name, "")
            print("Telegram proxy disabled.")
            return

        return

    print("No Telegram proxy is currently configured.")
    print()
    print("1. Configure proxy")
    print("2. Do not use proxy")
    print("0. Skip")

    choice = input("> ").strip()

    if choice == "1":
        value = input("Proxy URL: ").strip()

        if value:
            apply_variable(env_name, value)
            print("Telegram proxy configured.")

    elif choice == "2":
        apply_variable(env_name, "")
        print("Telegram proxy disabled.")


def configure_postgres(only_password: bool = False):
    print()
    print("=== PostgreSQL ===")
    print()

    if only_password:
        name = "DB_PASSWORD"
        config = ENV_VARIABLES[name]

        value = ask_value(
            name,
            config["env"],
            config["default"],
            config["secret"],
        )

        apply_variable(config["env"], value)

        print()
        print("PostgreSQL password updated.")
        return

    for name in (
            "DB_USER",
            "DB_PASSWORD",
            "DB_NAME",
            "DB_TEST_NAME",
            "DB_HOST",
            "DB_MIN_SIZE",
            "DB_MAX_SIZE",
    ):
        config = ENV_VARIABLES[name]

        value = ask_value(
            name,
            config["env"],
            config["default"],
            config["secret"],
        )

        apply_variable(config["env"], value)

    print()
    print("PostgreSQL parameters configured.")


def interactive_setup():
    print()
    print("========================================")
    print("        WIKIFEAT ENVIRONMENT SETUP")
    print("========================================")
    print()

    configure_general()

    print()
    print("PostgreSQL configuration:")
    print("1. Password only")
    print("2. All parameters")
    print("0. Skip")

    choice = input("> ").strip()

    if choice == "1":
        configure_postgres(only_password=True)
    elif choice == "2":
        configure_postgres(only_password=False)

    print()
    print("Setup completed.")


# ============================================================
# SAVE CONFIGURATION
# ============================================================

def collect_current_values():
    values = {}

    for config in ENV_VARIABLES.values():
        env_name = config["env"]

        values[env_name] = get_current_value(
            env_name,
            config["default"],
        )

    return values


def save_config_interactive():
    print()
    print("=== Save configuration ===")
    print()

    print("1. Save all variables")
    print("2. Save Telegram/Bot variables only")
    print("3. Save PostgreSQL variables only")
    print("0. Cancel")

    choice = input("> ").strip()

    if choice == "0":
        return

    values = collect_current_values()

    if choice == "2":
        values = {
            key: value
            for key, value in values.items()
            if not key.startswith("WIKIFEAT_DB_")
        }

    elif choice == "3":
        values = {
            key: value
            for key, value in values.items()
            if key.startswith("WIKIFEAT_DB_")
        }

    elif choice != "1":
        print("Unknown option.")
        return

    filename = input(
        "Configuration file name [wikifeat.env]: "
    ).strip()

    if not filename:
        filename = "wikifeat.env"

    if not filename.endswith(".env"):
        filename += ".env"

    file_path = SCRIPT_DIR / filename

    if file_path.exists():
        overwrite = input(
            f"{file_path.name} already exists. Overwrite? [y/N]: "
        ).strip().lower()

        if overwrite not in ("y", "yes"):
            print("Save cancelled.")
            return

    try:
        save_env_file(values, file_path)
    except ValueError as e:
        print(f"Failed to save configuration: {e}")
        return

    print()
    print(f"Configuration saved to: {file_path}")


# ============================================================
# LOAD CONFIGURATION
# ============================================================

def load_config_interactive():
    files = get_config_files()

    if not files:
        print()
        print("No .env configuration files found in this folder.")
        return

    print()
    print("=== Configuration files ===")
    print()

    for i, file_path in enumerate(files, 1):
        print(f"{i}. {file_path.name}")

    print("0. Cancel")

    choice = input("> ").strip()

    if choice == "0":
        return

    try:
        index = int(choice) - 1
        file_path = files[index]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    try:
        values = parse_env_file(file_path)
    except OSError as e:
        print(f"Failed to read configuration: {e}")
        return

    valid_variables = get_env_names()

    print()
    print(f"Loading: {file_path.name}")
    print()

    for env_name, value in values.items():
        if env_name not in valid_variables:
            print(f"Skipping unknown variable: {env_name}")
            continue

        print(
            f"{env_name} = "
            f"{display_value(value, is_secret(env_name))}"
        )

        apply_variable(env_name, value)

    print()
    print("Configuration loaded successfully.")


# ============================================================
# SHOW VARIABLES
# ============================================================

def show_current_variables():
    print()
    print("=== Current values ===")
    print()

    for name, config in ENV_VARIABLES.items():
        value = get_current_value(
            config["env"],
            config["default"],
        )

        print(
            f"{name:25} "
            f"{display_value(value, config['secret'])}"
        )


# ============================================================
# MAIN MENU
# ============================================================

def main():
    print(
        f"Operating system: {platform.system()}"
    )

    while True:
        print()
        print("========================================")
        print("              WIKIFEAT SETUP")
        print("========================================")
        print()
        print("1. Configure variables interactively")
        print("2. Load configuration from file")
        print("3. Save current variables to file")
        print("4. Show current variables")
        print("0. Exit")
        print()

        choice = input("> ").strip()

        if choice == "1":
            interactive_setup()

        elif choice == "2":
            load_config_interactive()

        elif choice == "3":
            save_config_interactive()

        elif choice == "4":
            show_current_variables()

        elif choice == "0":
            print("Exit.")
            break

        else:
            print("Unknown option.")


if __name__ == "__main__":
    main()
