# Hacking OpenCobolIDE

If you are using **OpenCobolIDE** on a Debian-based Linux distribution (like Ubuntu or Linux Mint) and your graphical interface loses its menu bar or windows stretch out of proportion, you can reset the layout by deleting its configuration file.

# 🔍 Locate the Configuration File
Run the following command in your terminal to see the configuration file with its full path:

```bash
ls -d ~/.config/OpenCobolIDE/*
```

# 🗑️ Delete the Configuration File
Run the `rm` command followed by the file path to delete it:

```bash
rm ~/.config/OpenCobolIDE/OpenCobolIDE.conf
```

> ⚠️ *Use code with caution.*

---

# 💡 What This Does
* **Resets the layout:** The next time you open the IDE, it will automatically generate a fresh configuration file with default window dimensions and menu settings.
* **Preserves your code:** This action only resets the editor's appearance and preferences; it **will not delete** your COBOL source files (`.cbl`, `.cob`).
