# ToptalMinifier

ToptalMinifier is a Sublime Text package that minifies CSS and JavaScript using Toptal's online minifier APIs.

It can minify the current selection or the whole file, then replace the content in place, open the result in a new tab, or copy it to the clipboard.

## Privacy note

This package sends the selected code or current file content to Toptal's online minifier APIs.

Do not use this package for private, sensitive, licensed, or proprietary source code unless you are allowed to send that code to a third-party service.

## Features

- Minify CSS using Toptal CSS Minifier
- Minify JavaScript using Toptal JavaScript Minifier
- Works with selected text or the full current file
- Minify in place
- Minify to a new view
- Minify to clipboard
- Command Palette entries
- Tools menu entries
- Package settings menu

## Installation

### Package Control

Once accepted into Package Control:

1. Open the Command Palette.
2. Run `Package Control: Install Package`.
3. Search for `ToptalMinifier`.
4. Press Enter.

### Manual install

Clone this repository into your Sublime Text `Packages` directory:

```bash
git clone https://github.com/bkader/ToptalMinifier.git ToptalMinifier
```

Do not include `package-metadata.json` in a manual install. Package Control generates that file for managed packages.

## Usage

Open a CSS or JavaScript file, then run one of these commands from the Command Palette:

- `Toptal Minifier: Minify Current CSS/JS In Place`
- `Toptal Minifier: Minify Current CSS/JS To New View`
- `Toptal Minifier: Minify Current CSS/JS To Clipboard`
- `Toptal Minifier: Minify As CSS In Place`
- `Toptal Minifier: Minify As JavaScript In Place`

The same commands are also available from:

```text
Tools > Toptal Minifier
```

## Optional key binding

ToptalMinifier does not install a default key binding.

To add one, open:

```text
Preferences > Key Bindings
```

Then add this to your user key bindings:

```json
[
    {
        "keys": ["ctrl+alt+shift+m"],
        "command": "toptal_minifier_replace"
    }
]
```

On macOS, use:

```json
[
    {
        "keys": ["super+alt+shift+m"],
        "command": "toptal_minifier_replace"
    }
]
```

## Settings

Open:

```text
Preferences > Package Settings > ToptalMinifier > Settings
```

Available settings:

```json
{
    "timeout_seconds": 30,
    "user_agent": "Sublime Text Toptal Minifier",
    "javascript_config": null
}
```

### JavaScript config

The `javascript_config` setting is forwarded to Toptal's JavaScript Minifier API as the `config` field.

Example:

```json
{
    "javascript_config": {
        "minify": true,
        "jsc": {
            "target": "es2022"
        }
    }
}
```

## Requirements

- Sublime Text 4
- Internet access

## License

MIT
