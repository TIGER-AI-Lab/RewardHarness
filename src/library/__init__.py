"""RewardHarness Library: manages Skills (evaluation instructions) and Tools (VLM wrappers).

Both are stored as SKILL.md files with YAML frontmatter.
- Skills: library/skills/<name>/SKILL.md
- Tools:  library/tools/<name>/SKILL.md
- Registry: library/registry.json maps name -> {type, description, path}
"""

import copy
import fcntl
import json
import os
import re
import shutil
import tempfile

import openai
import yaml

# Regex to match YAML frontmatter: file must start with '---' on its own line,
# followed by YAML content, then a closing '---' on its own line.
# Uses re.DOTALL so '.' matches newlines within the YAML block.
_FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\n(.*?\n)---[ \t]*\n(.*)\Z", re.DOTALL
)


class Library:
    def __init__(self, base_dir: str):
        """Initialize the Library.

        Args:
            base_dir: Path to the library/ directory containing skills/, tools/,
                      and registry.json.
        """
        self.base_dir = base_dir
        self.skills_dir = os.path.join(base_dir, "skills")
        self.tools_dir = os.path.join(base_dir, "tools")
        self.registry_path = os.path.join(base_dir, "registry.json")
        self.registry = {}
        self.load_registry()

    def load_registry(self):
        """Load the registry from registry.json if it exists."""
        if os.path.exists(self.registry_path):
            with open(self.registry_path) as f:
                self.registry = json.load(f)

    def save_registry(self, merge: bool = True):
        """Persist the registry to registry.json atomically with file locking.

        Uses an exclusive lock on a .lock file to prevent concurrent writes
        from corrupting the registry, and writes to a temp file first to
        ensure atomicity.

        Args:
            merge: If True (default), merge in-memory registry with the
                   on-disk registry before writing, so that entries added by
                   other processes are preserved.  Set to False during
                   restore/rollback so the on-disk state is replaced exactly.
        """
        lock_path = self.registry_path + ".lock"
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        with open(lock_path, "w") as lock_f:
            fcntl.flock(lock_f, fcntl.LOCK_EX)
            try:
                if merge:
                    # Re-read the on-disk registry so we merge rather than overwrite
                    # entries added by other processes since we last loaded.
                    if os.path.exists(self.registry_path):
                        with open(self.registry_path) as f:
                            disk_registry = json.load(f)
                    else:
                        disk_registry = {}
                    disk_registry.update(self.registry)
                    self.registry = disk_registry

                # Atomic write: temp file then rename
                fd, tmp_path = tempfile.mkstemp(
                    dir=os.path.dirname(self.registry_path), suffix=".tmp"
                )
                try:
                    with os.fdopen(fd, "w") as f:
                        json.dump(self.registry, f, indent=2)
                    os.replace(tmp_path, self.registry_path)
                except BaseException:
                    os.unlink(tmp_path)
                    raise
            finally:
                fcntl.flock(lock_f, fcntl.LOCK_UN)

    # ------------------------------------------------------------------ #
    #  SKILL.md parsing / writing                                         #
    # ------------------------------------------------------------------ #

    def _parse_skill_md(self, path: str) -> dict:
        """Parse a SKILL.md file into frontmatter dict + body string.

        Expected format::

            ---
            key: value
            ---

            Body content here.

        Frontmatter is only recognised when the file starts with ``---`` on its
        own line, followed by a closing ``---`` on its own line.  This avoids
        false positives from ``---`` appearing inside YAML-quoted values or in
        the Markdown body.

        Returns:
            {"frontmatter": dict, "body": str}
        """
        with open(path) as f:
            content = f.read()
        m = _FRONTMATTER_RE.match(content)
        if m:
            frontmatter = yaml.safe_load(m.group(1))
            body = m.group(2).strip()
        else:
            frontmatter = {}
            body = content.strip()
        return {"frontmatter": frontmatter or {}, "body": body}

    def _write_skill_md(self, path: str, frontmatter: dict, body: str):
        """Write a SKILL.md file with YAML frontmatter and a Markdown body."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fm_str = yaml.dump(
            frontmatter, default_flow_style=False, allow_unicode=True
        ).strip()
        with open(path, "w") as f:
            f.write(f"---\n{fm_str}\n---\n\n{body}\n")

    # ------------------------------------------------------------------ #
    #  Skills                                                             #
    # ------------------------------------------------------------------ #

    def add_skill(self, name: str, description: str, content_md: str):
        """Register a new Skill and write its SKILL.md.

        Args:
            name: Unique skill identifier (also used as subdirectory name).
            description: Short human-readable description.
            content_md: Markdown body containing the evaluation instruction.
        """
        path = os.path.join(self.skills_dir, name, "SKILL.md")
        frontmatter = {"name": name, "type": "skill", "description": description}
        self._write_skill_md(path, frontmatter, content_md)
        self.registry[name] = {
            "type": "skill",
            "description": description,
            "path": f"skills/{name}/SKILL.md",
        }
        self.save_registry()

    def update_skill(self, name: str, new_content_md: str, new_description: str = None):
        """Update an existing Skill's body (and optionally its description).

        Args:
            name: Skill identifier that must already exist in the registry.
            new_content_md: Replacement Markdown body.
            new_description: If provided, also update the description.

        Raises:
            KeyError: If *name* is not in the registry.
        """
        if name not in self.registry:
            raise KeyError(f"Skill '{name}' not found in registry")
        path = os.path.join(self.base_dir, self.registry[name]["path"])
        parsed = self._parse_skill_md(path)
        fm = parsed["frontmatter"]
        if new_description:
            fm["description"] = new_description
            self.registry[name]["description"] = new_description
        self._write_skill_md(path, fm, new_content_md)
        self.save_registry()

    def get_skill(self, name: str) -> dict:
        """Return a Skill's metadata and body content.

        Returns:
            {"name": str, "description": str, "content": str}

        Raises:
            KeyError: If *name* is not a registered skill.
        """
        if name not in self.registry or self.registry[name]["type"] != "skill":
            raise KeyError(f"Skill '{name}' not found")
        path = os.path.join(self.base_dir, self.registry[name]["path"])
        parsed = self._parse_skill_md(path)
        return {
            "name": name,
            "description": parsed["frontmatter"].get("description", ""),
            "content": parsed["body"],
        }

    def delete_skill(self, name: str):
        """Remove a Skill from the library.

        Deletes the SKILL.md file, its parent directory, and the registry entry.

        Raises:
            KeyError: If *name* is not a registered skill.
        """
        if name not in self.registry or self.registry[name]["type"] != "skill":
            raise KeyError(f"Skill '{name}' not found")
        path = os.path.join(self.base_dir, self.registry[name]["path"])
        if os.path.exists(path):
            os.remove(path)
        skill_dir = os.path.dirname(path)
        if os.path.isdir(skill_dir) and not os.listdir(skill_dir):
            os.rmdir(skill_dir)
        del self.registry[name]
        self.save_registry(merge=False)

    # ------------------------------------------------------------------ #
    #  Tools                                                              #
    # ------------------------------------------------------------------ #

    def add_tool(
        self,
        name: str,
        description: str,
        system_prompt: str,
        input_schema: dict,
        output_schema: dict,
        content_md: str,
    ):
        """Register a new Tool and write its SKILL.md.

        Args:
            name: Unique tool identifier (also used as subdirectory name).
            description: Short human-readable description.
            system_prompt: VLM system prompt sent with every call.
            input_schema: JSON Schema dict describing expected input.
            output_schema: JSON Schema dict describing expected output.
            content_md: Markdown body documenting the call format.
        """
        path = os.path.join(self.tools_dir, name, "SKILL.md")
        frontmatter = {
            "name": name,
            "type": "tool",
            "description": description,
            "system_prompt": system_prompt,
            "input_schema": input_schema,
            "output_schema": output_schema,
        }
        self._write_skill_md(path, frontmatter, content_md)
        self.registry[name] = {
            "type": "tool",
            "description": description,
            "path": f"tools/{name}/SKILL.md",
        }
        self.save_registry()

    def update_tool(self, name: str, new_system_prompt: str):
        """Update an existing Tool's system_prompt; the body is left unchanged.

        Args:
            name: Tool identifier that must already exist in the registry.
            new_system_prompt: Replacement system prompt string.

        Raises:
            KeyError: If *name* is not in the registry.
        """
        if name not in self.registry:
            raise KeyError(f"Tool '{name}' not found in registry")
        path = os.path.join(self.base_dir, self.registry[name]["path"])
        parsed = self._parse_skill_md(path)
        fm = parsed["frontmatter"]
        fm["system_prompt"] = new_system_prompt
        self._write_skill_md(path, fm, parsed["body"])

    def get_tool(self, name: str) -> dict:
        """Return a Tool's metadata (excluding the Markdown body).

        Returns:
            {"name", "description", "system_prompt", "input_schema", "output_schema"}

        Raises:
            KeyError: If *name* is not a registered tool.
        """
        if name not in self.registry or self.registry[name]["type"] != "tool":
            raise KeyError(f"Tool '{name}' not found")
        path = os.path.join(self.base_dir, self.registry[name]["path"])
        parsed = self._parse_skill_md(path)
        fm = parsed["frontmatter"]
        return {
            "name": name,
            "description": fm.get("description", ""),
            "system_prompt": fm.get("system_prompt", ""),
            "input_schema": fm.get("input_schema", {}),
            "output_schema": fm.get("output_schema", {}),
        }

    def delete_tool(self, name: str):
        """Remove a Tool from the library.

        Deletes the SKILL.md file, its parent directory, and the registry entry.

        Raises:
            KeyError: If *name* is not a registered tool.
        """
        if name not in self.registry or self.registry[name]["type"] != "tool":
            raise KeyError(f"Tool '{name}' not found")
        path = os.path.join(self.base_dir, self.registry[name]["path"])
        if os.path.exists(path):
            os.remove(path)
        tool_dir = os.path.dirname(path)
        if os.path.isdir(tool_dir) and not os.listdir(tool_dir):
            os.rmdir(tool_dir)
        del self.registry[name]
        self.save_registry(merge=False)

    def call_tool(self, name: str, args: dict, endpoint_pool) -> dict:
        """Call a Tool via a vLLM OpenAI-compatible endpoint.

        Args:
            name: Registered tool name.
            args: Must contain ``images`` (list of base64 strings) and/or
                  ``query`` (str).  Falls back to a generic prompt if
                  ``query`` is absent.
            endpoint_pool: Object whose ``.next()`` returns the base URL of
                           the next available vLLM endpoint.

        Returns:
            Parsed JSON dict on success, or
            ``{"raw": <str>, "error": "json_parse_failed"}`` if the model
            response is not valid JSON.
        """
        tool = self.get_tool(name)
        system_prompt = tool["system_prompt"]
        images = args.get("images", [])
        query = args.get("query", "Analyze as instructed. Return JSON only.")

        content = []
        for b64 in images:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                }
            )
        content.append({"type": "text", "text": query})

        client = openai.OpenAI(base_url=endpoint_pool.next(), api_key="token")
        resp = client.chat.completions.create(
            model="Qwen2.5-VL-7B-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            max_tokens=512,
        )
        try:
            return json.loads(resp.choices[0].message.content)
        except json.JSONDecodeError:
            return {"raw": resp.choices[0].message.content, "error": "json_parse_failed"}

    # ------------------------------------------------------------------ #
    #  Snapshot / Restore                                                 #
    # ------------------------------------------------------------------ #

    def snapshot(self) -> dict:
        """Capture the full library state: registry + all SKILL.md files.

        Returns:
            A dict with 'registry' (deep copy) and 'files' mapping each
            relative path to its file content.
        """
        files = {}
        for name, info in self.registry.items():
            rel_path = info["path"]
            abs_path = os.path.join(self.base_dir, rel_path)
            if os.path.exists(abs_path):
                with open(abs_path) as f:
                    files[rel_path] = f.read()
        return {
            "registry": copy.deepcopy(self.registry),
            "files": files,
        }

    def restore(self, snap: dict):
        """Restore the library to a previous snapshot state.

        This removes any SKILL.md files and registry entries that were added
        after the snapshot was taken, and restores file contents to their
        snapshotted versions.

        Args:
            snap: A snapshot dict as returned by ``snapshot()``.
        """
        snap_registry = snap["registry"]
        snap_files = snap["files"]

        # Remove files/dirs for entries not present in the snapshot
        for name, info in list(self.registry.items()):
            if name not in snap_registry:
                rel_path = info["path"]
                abs_path = os.path.join(self.base_dir, rel_path)
                # Remove the SKILL.md file
                if os.path.exists(abs_path):
                    os.unlink(abs_path)
                # Remove the parent directory if now empty
                parent = os.path.dirname(abs_path)
                if os.path.isdir(parent) and not os.listdir(parent):
                    os.rmdir(parent)

        # Restore registry
        self.registry = copy.deepcopy(snap_registry)

        # Restore file contents
        for rel_path, content in snap_files.items():
            abs_path = os.path.join(self.base_dir, rel_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w") as f:
                f.write(content)

        self.save_registry(merge=False)

    # ------------------------------------------------------------------ #
    #  Shared helpers                                                     #
    # ------------------------------------------------------------------ #

    def get_all_summaries(self) -> dict:
        """Return L1 summaries for every registered entry.

        Returns:
            {"skills": [{"name", "description"}, ...],
             "tools":  [{"name", "description"}, ...]}
        """
        skills = []
        tools = []
        for name, info in self.registry.items():
            entry = {"name": name, "description": info["description"]}
            if info["type"] == "skill":
                skills.append(entry)
            else:
                tools.append(entry)
        return {"skills": skills, "tools": tools}

    def get_full_content(self, name: str) -> str:
        """Return the Markdown body only (L2 content).

        The system_prompt (for tools) stays in frontmatter and is not
        returned here; use ``get_tool()`` to retrieve it.

        Raises:
            KeyError: If *name* is not in the registry.
        """
        if name not in self.registry:
            raise KeyError(f"'{name}' not found in registry")
        path = os.path.join(self.base_dir, self.registry[name]["path"])
        parsed = self._parse_skill_md(path)
        return parsed["body"]
