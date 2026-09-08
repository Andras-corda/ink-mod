#!/usr/bin/env python3
"""configure_mod.py — Generateur de projet MDK Forge (Minecraft 1.16.5 -> 1.21.1).

USAGE 1 — creer un nouveau projet a partir d'un template de version :

    python configure_mod.py --list-versions
    python configure_mod.py --new ../MonMod --mc 1.20.1 --interactive
    python configure_mod.py --new ../MonMod --mc 1.19.2 --set mod_id=coolmod --set mod_name="Cool Mod"

USAGE 2 — (re)configurer un projet deja genere (script lance depuis sa racine) :

    python configure_mod.py --set mod_name="Ma Super Map"
    python configure_mod.py --interactive
    python configure_mod.py --show

Ce qui est configure :
  * gradle.properties (versions Forge/MC issues de versions.json + infos du mod)
  * package Java + classe principale @Mod + constante MODID
  * dossiers de ressources assets/<id> et data/<id>
  * rootProject.name dans settings.gradle

mods.toml et pack.mcmeta ne sont pas modifies : ils utilisent des jetons ${...}
remplis au build depuis gradle.properties.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
VERSIONS_FILE = SCRIPT_DIR / "versions.json"

# Ordre / liste des cles gerees dans gradle.properties
PROP_KEYS = [
    "minecraft_version",
    "minecraft_version_range",
    "forge_version",
    "forge_version_range",
    "loader_version_range",
    "mapping_channel",
    "mapping_version",
    "mod_id",
    "mod_name",
    "mod_license",
    "mod_version",
    "mod_group_id",
    "mod_authors",
    "mod_description",
    "pack_format_resource",
    "pack_format_data",
]

# Couches de templates a empiler pour chaque famille (dans l'ordre)
FAMILY_LAYERS = {
    "fg5": ["common", "fg5"],
    "fg6": ["common", "fg6"],
    "fg6i": ["common", "fg6", "fg6i"],
}

DEFAULT_IDENTITY = {
    "mod_id": "examplemod",
    "mod_name": "Example Mod",
    "mod_license": "All Rights Reserved",
    "mod_version": "1.0.0",
    "mod_group_id": "com.example.examplemod",
    "mod_authors": "YourNameHere",
    "mod_description": "Example mod description.",
}

# Champs proposes en mode interactif : (cle, libelle)
INTERACTIVE_KEYS = [
    ("mod_id", "Identifiant du mod (minuscules, a-z0-9_)"),
    ("mod_name", "Nom affiche du mod"),
    ("mod_description", "Description"),
    ("mod_authors", "Auteur(s)"),
    ("mod_version", "Version du mod"),
    ("mod_license", "Licence"),
    ("mod_group_id", "Package Java (group id)"),
    ("main_class", "Nom de la classe principale"),
]

# Ce qui n'est PAS copie dans un nouveau projet
COPY_IGNORE = shutil.ignore_patterns(
    ".git", ".gradle", "build", "run", "run-data", "generated",
    "__pycache__", "*.pyc", ".idea", "*.iml", "bin", "out", "mcmodsrepo",
)

TOKEN_SUFFIXES = {".gradle", ".properties", ".json", ".toml", ".java", ".md",
                  ".txt", ".cfg", ".mcmeta"}

PROP_LINE_RE = re.compile(r"^(\s*)([A-Za-z0-9_.]+)(\s*=\s*)(.*)$")


class Project:
    """Chemins d'un projet MDK enracine dans `root`."""

    def __init__(self, root: Path):
        self.root = root
        self.props = root / "gradle.properties"
        self.java = root / "src" / "main" / "java"
        self.res = root / "src" / "main" / "resources"
        self.settings = root / "settings.gradle"
        self.config = root / "mod_config.json"


# --------------------------------------------------------------------------- #
# versions.json
# --------------------------------------------------------------------------- #
def load_versions() -> dict:
    if not VERSIONS_FILE.exists():
        raise SystemExit(f"ERREUR: {VERSIONS_FILE} introuvable.")
    return json.loads(VERSIONS_FILE.read_text(encoding="utf-8")).get("versions", {})


def gradle_props_for(mc: str, v: dict) -> dict:
    major = str(v["forge_major"])
    props = dict(DEFAULT_IDENTITY)
    props.update({
        "minecraft_version": mc,
        "minecraft_version_range": v["minecraft_version_range"],
        "forge_version": str(v["forge_version"]),
        "forge_version_range": f"[{major},)",
        "loader_version_range": f"[{major},)",
        "mapping_channel": v["mapping_channel"],
        "mapping_version": str(v["mapping_version"]),
        "pack_format_resource": str(v["pack_format_resource"]),
        "pack_format_data": str(v["pack_format_data"]),
    })
    return props


def render_gradle_properties(props: dict) -> str:
    out = [
        "# Options Gradle",
        "org.gradle.jvmargs=-Xmx1G",
        "org.gradle.daemon=false",
        "",
        "#### Environnement (genere depuis versions.json) ####",
    ]
    for k in ("minecraft_version", "minecraft_version_range", "forge_version",
              "forge_version_range", "loader_version_range", "mapping_channel",
              "mapping_version"):
        out.append(f"{k}={props[k]}")
    out += ["", "#### Infos du mod (modifiables via configure_mod.py) ####"]
    for k in ("mod_id", "mod_name", "mod_license", "mod_version", "mod_group_id",
              "mod_authors", "mod_description"):
        out.append(f"{k}={props[k]}")
    out += ["", "#### Format des packs (resource / data) ####"]
    for k in ("pack_format_resource", "pack_format_data"):
        out.append(f"{k}={props[k]}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# gradle.properties (lecture / ecriture ciblee)
# --------------------------------------------------------------------------- #
def read_properties(path: Path) -> dict[str, str]:
    props: dict[str, str] = {}
    if not path.exists():
        return props
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = PROP_LINE_RE.match(line)
        if m:
            props[m.group(2)] = m.group(4).strip()
    return props


def write_properties(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        m = PROP_LINE_RE.match(line)
        if m and m.group(2) in updates:
            key = m.group(2)
            out.append(f"{m.group(1)}{key}{m.group(3)}{updates[key]}")
            seen.add(key)
        else:
            out.append(line)
    missing = [k for k in updates if k not in seen]
    if missing:
        out.append("")
        out.extend(f"{k}={updates[k]}" for k in missing)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Java
# --------------------------------------------------------------------------- #
def find_main_mod_class(java_root: Path) -> tuple[Path, str, str]:
    mod_anno = re.compile(r"@Mod\s*\(")
    pkg_re = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M)
    cls_re = re.compile(r"\bclass\s+(\w+)")
    for path in sorted(java_root.rglob("*.java")):
        text = path.read_text(encoding="utf-8")
        if mod_anno.search(text):
            pkg = pkg_re.search(text)
            cls = cls_re.search(text)
            if pkg and cls:
                return path, pkg.group(1), cls.group(1)
    raise SystemExit("ERREUR: aucune classe annotee @Mod trouvee dans src/main/java")


def to_class_name(name: str) -> str:
    parts = re.split(r"[^0-9A-Za-z]+", name)
    cls = "".join(p[:1].upper() + p[1:] for p in parts if p)
    if not cls:
        return "ExampleMod"
    if cls[0].isdigit():
        cls = "Mod" + cls
    return cls


def slugify_mod_id(value: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", value.lower()) or "examplemod"


def _prune_empty_dirs(root: Path, pkg: str) -> None:
    parts = pkg.split(".")
    for i in range(len(parts), 0, -1):
        d = root.joinpath(*parts[:i])
        try:
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        except OSError:
            break


def _update_settings_name(settings: Path, mod_id: str) -> None:
    if not settings.exists():
        return
    text = settings.read_text(encoding="utf-8")
    line = f"rootProject.name = '{mod_id}'"
    if re.search(r"(?m)^\s*//?\s*rootProject\.name\s*=", text):
        text = re.sub(r"(?m)^\s*//?\s*rootProject\.name\s*=.*$", line, text)
    else:
        text = text.rstrip() + "\n" + line + "\n"
    settings.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Configuration d'un projet existant
# --------------------------------------------------------------------------- #
def apply(proj: Project, config: dict) -> None:
    old = read_properties(proj.props)
    if not old:
        raise SystemExit(f"ERREUR: {proj.props} introuvable ou vide.")

    new = dict(old)
    for k, val in config.items():
        if k in PROP_KEYS:
            new[k] = str(val).strip()

    old_mod_id = old.get("mod_id", "examplemod")
    new_mod_id = slugify_mod_id(new.get("mod_id", old_mod_id))
    new["mod_id"] = new_mod_id

    _, old_pkg, old_cls = find_main_mod_class(proj.java)
    new_pkg = (new.get("mod_group_id") or old_pkg).strip() or old_pkg
    new["mod_group_id"] = new_pkg
    new_cls = to_class_name(str(config["main_class"])) if config.get("main_class") else old_cls

    print("Changements :")
    print(f"  mod_id   : {old_mod_id}  ->  {new_mod_id}")
    print(f"  package  : {old_pkg}  ->  {new_pkg}")
    print(f"  classe   : {old_cls}  ->  {new_cls}")
    for k in ("mod_name", "mod_version", "mod_authors", "mod_description", "mod_license"):
        if old.get(k) != new.get(k):
            print(f"  {k} : {old.get(k)!r}  ->  {new.get(k)!r}")

    write_properties(proj.props, {k: new[k] for k in PROP_KEYS if k in new})

    for path in list(proj.java.rglob("*.java")):
        text = path.read_text(encoding="utf-8")
        updated = text
        if old_pkg != new_pkg:
            updated = updated.replace(old_pkg, new_pkg)
        if old_cls != new_cls:
            updated = re.sub(rf"\b{re.escape(old_cls)}\b", new_cls, updated)
        updated = re.sub(r'(String\s+MODID\s*=\s*")[^"]*(")', rf"\g<1>{new_mod_id}\g<2>", updated)
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    old_dir = proj.java.joinpath(*old_pkg.split("."))
    new_dir = proj.java.joinpath(*new_pkg.split("."))
    if old_dir.resolve() != new_dir.resolve():
        new_dir.mkdir(parents=True, exist_ok=True)
        for item in list(old_dir.rglob("*")):
            if item.is_file():
                dest = new_dir / item.relative_to(old_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(dest))
        _prune_empty_dirs(proj.java, old_pkg)

    cur = new_dir / f"{old_cls}.java"
    if old_cls != new_cls and cur.exists():
        shutil.move(str(cur), str(new_dir / f"{new_cls}.java"))

    if old_mod_id != new_mod_id:
        for kind in ("assets", "data"):
            src = proj.res / kind / old_mod_id
            dst = proj.res / kind / new_mod_id
            if src.is_dir():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))

    _update_settings_name(proj.settings, new_mod_id)
    print("OK - projet configure.")


def snapshot_config(proj: Project) -> dict:
    props = read_properties(proj.props)
    data = {k: props[k] for k in PROP_KEYS if k in props}
    try:
        _, pkg, cls = find_main_mod_class(proj.java)
        data["mod_group_id"] = pkg
        data["main_class"] = cls
    except SystemExit:
        pass
    return data


# --------------------------------------------------------------------------- #
# Generation d'un nouveau projet
# --------------------------------------------------------------------------- #
def scaffold(dest: Path, mc: str, force: bool) -> tuple[Project, dict]:
    versions = load_versions()
    if mc not in versions:
        raise SystemExit(
            f"ERREUR: version '{mc}' inconnue. Disponibles : {', '.join(versions)}"
        )
    v = versions[mc]
    family = v["family"]
    if family not in FAMILY_LAYERS:
        raise SystemExit(f"ERREUR: famille '{family}' inconnue dans le script.")
    if not TEMPLATES_DIR.is_dir():
        raise SystemExit(f"ERREUR: dossier templates/ introuvable ({TEMPLATES_DIR}).")
    if dest.exists() and any(dest.iterdir()) and not force:
        raise SystemExit(f"ERREUR: {dest} existe et n'est pas vide (utilise --force).")

    dest.mkdir(parents=True, exist_ok=True)
    for layer in FAMILY_LAYERS[family]:
        shutil.copytree(TEMPLATES_DIR / layer, dest,
                        ignore=COPY_IGNORE, dirs_exist_ok=True)

    tokens = {
        "@@JAVA_VERSION@@": str(v["java_version"]),
        "@@GRADLE_VERSION@@": str(v["gradle_version"]),
        "@@FORGEGRADLE_VERSION@@": str(v["forgegradle_version"]),
    }
    for path in dest.rglob("*"):
        if path.is_file() and path.suffix.lower() in TOKEN_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            new = text
            for a, b in tokens.items():
                new = new.replace(a, b)
            if new != text:
                path.write_text(new, encoding="utf-8")

    proj = Project(dest)
    proj.props.write_text(render_gradle_properties(gradle_props_for(mc, v)),
                          encoding="utf-8")

    # Copie l'outil pour permettre une reconfiguration ulterieure
    shutil.copy2(Path(__file__).resolve(), dest / "configure_mod.py")
    shutil.copy2(VERSIONS_FILE, dest / "versions.json")

    print(f"Template '{family}' (MC {mc}, Forge {v['forge_version']}, "
          f"Java {v['java_version']}) copie -> {dest}")
    return proj, v


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def collect_config(proj: Project, args) -> dict:
    config: dict[str, str] = {}
    cfg_file = Path(args.config) if args.config else proj.config
    if cfg_file.exists():
        config.update(json.loads(cfg_file.read_text(encoding="utf-8")))
        config.pop("minecraft_version", None)  # pilote par --mc, jamais ecrase ici

    if args.interactive:
        current = {**config, **snapshot_config(proj)}
        for key, label in INTERACTIVE_KEYS:
            default = current.get(key, "")
            answer = input(f"{label} [{default}]: ").strip()
            config[key] = answer or default

    for item in args.set:
        if "=" not in item:
            raise SystemExit(f"ERREUR: --set attend CLE=VALEUR (recu: {item!r})")
        key, _, val = item.partition("=")
        config[key.strip()] = val.strip()
    return config


def print_versions() -> None:
    versions = load_versions()
    print(f"{'MC':10} {'Forge (latest)':16} {'Java':5} {'Gradle':8} Famille")
    print("-" * 55)
    for mc, v in versions.items():
        print(f"{mc:10} {str(v['forge_version']):16} {str(v['java_version']):5} "
              f"{str(v['gradle_version']):8} {v['family']}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generateur de projet MDK Forge 1.16.5 -> 1.21.1.")
    p.add_argument("--new", metavar="DIR", type=Path,
                   help="Cree un nouveau projet dans DIR (necessite --mc).")
    p.add_argument("--mc", metavar="VERSION",
                   help="Version Minecraft cible (voir --list-versions).")
    p.add_argument("--list-versions", action="store_true",
                   help="Liste les versions supportees et quitte.")
    p.add_argument("--force", action="store_true",
                   help="Autorise --new vers un dossier non vide.")
    p.add_argument("--config", metavar="FICHIER",
                   help="Fichier JSON de valeurs de depart (defaut: mod_config.json du projet).")
    p.add_argument("--set", action="append", default=[], metavar="CLE=VALEUR",
                   help="Surcharge une valeur (repetable).")
    p.add_argument("--interactive", action="store_true",
                   help="Pose les questions une par une.")
    p.add_argument("--show", action="store_true",
                   help="Affiche la config du projet courant et quitte.")
    p.add_argument("--no-save", action="store_true",
                   help="Ne pas (re)ecrire mod_config.json a la fin.")
    args = p.parse_args(argv)

    if args.list_versions:
        print_versions()
        return 0

    if args.show:
        proj = Project(SCRIPT_DIR)
        if not proj.props.exists():
            raise SystemExit("Aucun projet ici. Cf. --new DIR --mc VERSION.")
        for k, val in snapshot_config(proj).items():
            print(f"{k:24} = {val}")
        return 0

    if args.new:
        if not args.mc:
            raise SystemExit("ERREUR: --new necessite --mc VERSION (voir --list-versions).")
        proj, v = scaffold(args.new, args.mc, args.force)
        config = collect_config(proj, args)
        if config:
            apply(proj, config)
        else:
            print("Aucune info fournie : le projet garde l'identite 'examplemod'.")
        if not args.no_save:
            proj.config.write_text(
                json.dumps(snapshot_config(proj), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8")
        print(f"\nProjet pret : {proj.root}")
        print("Etapes suivantes :")
        print(f"  cd {proj.root}")
        print(f"  # JDK {v['java_version']} requis. Recupere le wrapper Gradle (voir README), puis :")
        print("  gradlew build")
        return 0

    # (Re)configuration en place
    proj = Project(SCRIPT_DIR)
    if not proj.props.exists():
        raise SystemExit(
            "Aucun projet dans ce dossier.\n"
            "  - Pour creer un projet : python configure_mod.py --new ../MonMod --mc 1.20.1\n"
            "  - Versions disponibles : python configure_mod.py --list-versions"
        )
    config = collect_config(proj, args)
    if not config:
        raise SystemExit("ERREUR: rien a faire. Utilise --set, --interactive ou mod_config.json.")
    apply(proj, config)
    if not args.no_save:
        proj.config.write_text(
            json.dumps(snapshot_config(proj), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
