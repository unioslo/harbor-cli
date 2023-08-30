# TUI

The application provides the command `tui` which can be used to launch an interactive TUI (Terminal User Interface), in which you can navigate through the different commands and launch them interactively. This is useful for users who prefer a more visual interface than the CLI and users who are looking to learn more about the available commands.

The TUI is powered by [Trogon](https://github.com/Textualize/trogon) by [Textualize](https://github.com/Textualize), and is automatically generated from the CLI commands. It can be navigated with both mouse and keyboard.

## Basic Usage

To start the TUI, run:

```
harbor tui
```

This opens a TUI session that looks like this:

![TUI](../assets/tui/tui1.png)

By selecting a command, you can see its description and usage information.

![TUI](../assets/tui/tui2.png)

After adding the required argument and toggling the options you want, pressing `CTRL+R` will close the TUI and run the command in your terminal.

![TUI](../assets/tui/tui3.png)


## Demo

<script async id="asciicast-sTIjEW30Qzh2oXcMm9CqAV0Dy" src="https://asciinema.org/a/sTIjEW30Qzh2oXcMm9CqAV0Dy.js"></script>
