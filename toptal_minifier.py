import json
import urllib.error
import urllib.parse
import urllib.request

import sublime
import sublime_plugin


CSS_ENDPOINT = "https://www.toptal.com/developers/cssminifier/api/raw"
JS_ENDPOINT = "https://www.toptal.com/developers/javascript-minifier/api/raw"
SETTINGS_FILE = "ToptalMinifier.sublime-settings"

TARGETS = {
    "css": {
        "kind": "css",
        "endpoint": CSS_ENDPOINT,
        "syntaxes": ("css", "scss", "sass", "less"),
    },
    "js": {
        "kind": "js",
        "endpoint": JS_ENDPOINT,
        "syntaxes": ("javascript", "js", "jsx", "typescript", "tsx"),
    },
}


class ToptalMinifierError(Exception):
    pass


def plugin_settings():
    return sublime.load_settings(SETTINGS_FILE)


def setting(name, default=None):
    return plugin_settings().get(name, default)


def status(message):
    sublime.set_timeout(lambda: sublime.status_message("Toptal Minifier: " + message), 0)


def panel(window, message):
    if not window:
        return

    def show():
        output = window.create_output_panel("toptal_minifier")
        output.run_command("append", {"characters": message})
        window.run_command("show_panel", {"panel": "output.toptal_minifier"})

    sublime.set_timeout(show, 0)


def syntax_name(view):
    try:
        syntax = view.syntax()
        if syntax and syntax.name:
            return syntax.name.lower()
    except Exception:
        pass

    path = view.settings().get("syntax", "") or ""
    return path.lower()


def get_target(view, explicit_kind=None):
    if explicit_kind:
        if explicit_kind not in TARGETS:
            raise ToptalMinifierError("Unsupported minifier kind: " + str(explicit_kind))
        return TARGETS[explicit_kind]

    syntax = syntax_name(view)
    file_name = (view.file_name() or "").lower()

    for target in TARGETS.values():
        for token in target["syntaxes"]:
            if token in syntax:
                return target

    if file_name.endswith((".css", ".scss", ".sass", ".less")):
        return TARGETS["css"]

    if file_name.endswith((".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx")):
        return TARGETS["js"]

    raise ToptalMinifierError("Could not detect CSS or JavaScript. Use the explicit CSS/JS commands.")


def selected_or_full_region(view):
    selected = [region for region in view.sel() if not region.empty()]
    if selected:
        start = min(region.begin() for region in selected)
        end = max(region.end() for region in selected)
        return sublime.Region(start, end)

    return sublime.Region(0, view.size())


def selected_or_full_text(view):
    region = selected_or_full_region(view)
    return region, view.substr(region)


def parse_error_body(body):
    try:
        payload = json.loads(body)
    except ValueError:
        return body.strip() or "Unknown API error."

    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            title = str(first.get("title") or "API error")
            detail = str(first.get("detail") or "").strip()
            if detail:
                return title + ": " + detail
            return title

    return body.strip() or "Unknown API error."


def minify_with_toptal(target, source):
    timeout = int(setting("timeout_seconds", 30))
    user_agent = str(setting("user_agent", "Sublime Text Toptal Minifier"))

    form = {"input": source}

    if target["kind"] == "js":
        config = setting("javascript_config", None)
        if config:
            if isinstance(config, dict):
                form["config"] = json.dumps(config)
            else:
                form["config"] = str(config)

    data = urllib.parse.urlencode(form).encode("utf-8")
    request = urllib.request.Request(
        target["endpoint"],
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": user_agent,
        },
    )

    try:
        response = urllib.request.urlopen(request, timeout=timeout)
        try:
            return response.read().decode("utf-8")
        finally:
            response.close()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ToptalMinifierError("HTTP " + str(exc.code) + ": " + parse_error_body(body))
    except urllib.error.URLError as exc:
        raise ToptalMinifierError("Network error: " + str(exc.reason))
    except Exception as exc:
        if exc.__class__.__name__ == "TimeoutError":
            raise ToptalMinifierError("Request timed out.")
        raise


def minified_name(view, kind):
    file_name = view.file_name()
    if not file_name:
        return "untitled.min." + kind

    base = file_name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if "." not in base:
        return base + ".min." + kind

    stem, ext = base.rsplit(".", 1)
    return stem + ".min." + ext


def assign_syntax(view, kind):
    if kind == "css":
        syntax = "Packages/CSS/CSS.sublime-syntax"
    else:
        syntax = "Packages/JavaScript/JavaScript.sublime-syntax"

    try:
        view.assign_syntax(syntax)
    except AttributeError:
        view.set_syntax_file(syntax)


class ToptalMinifierApplyReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, start, end, text):
        region = sublime.Region(start, min(end, self.view.size()))
        self.view.replace(edit, region, text)


class ToptalMinifierReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, kind=None):
        window = self.view.window()

        try:
            target = get_target(self.view, kind)
            region, source = selected_or_full_text(self.view)
            start = region.begin()
            end = region.end()

            if not source.strip():
                raise ToptalMinifierError("Nothing to minify.")

            status("minifying " + target["kind"].upper() + "...")

            def worker():
                try:
                    minified = minify_with_toptal(target, source)

                    def apply_result():
                        self.view.run_command(
                            "toptal_minifier_apply_replace",
                            {"start": start, "end": end, "text": minified},
                        )

                    sublime.set_timeout(apply_result, 0)
                    status(target["kind"].upper() + " minified in place.")
                except ToptalMinifierError as exc:
                    message = str(exc)
                    status(message)
                    panel(window, message)

            sublime.set_timeout_async(worker, 0)
        except ToptalMinifierError as exc:
            message = str(exc)
            status(message)
            panel(window, message)

    def is_enabled(self, kind=None):
        return not self.view.is_read_only() and self.view.size() > 0


class ToptalMinifierNewViewCommand(sublime_plugin.TextCommand):
    def run(self, edit, kind=None):
        window = self.view.window()

        try:
            target = get_target(self.view, kind)
            _region, source = selected_or_full_text(self.view)
            name = minified_name(self.view, target["kind"])

            if not source.strip():
                raise ToptalMinifierError("Nothing to minify.")

            if not window:
                raise ToptalMinifierError("No active Sublime window.")

            status("minifying " + target["kind"].upper() + "...")

            def worker():
                try:
                    minified = minify_with_toptal(target, source)

                    def create_view():
                        new_view = window.new_file()
                        new_view.set_name(name)
                        new_view.set_scratch(True)
                        new_view.run_command("append", {"characters": minified})
                        assign_syntax(new_view, target["kind"])

                    sublime.set_timeout(create_view, 0)
                    status(target["kind"].upper() + " minified into a new view.")
                except ToptalMinifierError as exc:
                    message = str(exc)
                    status(message)
                    panel(window, message)

            sublime.set_timeout_async(worker, 0)
        except ToptalMinifierError as exc:
            message = str(exc)
            status(message)
            panel(window, message)

    def is_enabled(self, kind=None):
        return self.view.size() > 0


class ToptalMinifierCopyCommand(sublime_plugin.TextCommand):
    def run(self, edit, kind=None):
        window = self.view.window()

        try:
            target = get_target(self.view, kind)
            _region, source = selected_or_full_text(self.view)

            if not source.strip():
                raise ToptalMinifierError("Nothing to minify.")

            status("minifying " + target["kind"].upper() + "...")

            def worker():
                try:
                    minified = minify_with_toptal(target, source)
                    sublime.set_timeout(lambda: sublime.set_clipboard(minified), 0)
                    status(target["kind"].upper() + " minified and copied to clipboard.")
                except ToptalMinifierError as exc:
                    message = str(exc)
                    status(message)
                    panel(window, message)

            sublime.set_timeout_async(worker, 0)
        except ToptalMinifierError as exc:
            message = str(exc)
            status(message)
            panel(window, message)

    def is_enabled(self, kind=None):
        return self.view.size() > 0
