"""PyInstaller entry point - spec files need a script, not a module:function."""

from huectl.webapp import main

if __name__ == "__main__":
    main()
