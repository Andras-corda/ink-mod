# Template MDK — Minecraft Forge 1.20.1

Template de Mod Development Kit pour **Minecraft 1.20.1 / Forge 47.3.0**, avec un
initialiseur de projet en Python (`configure_mod.py`).

## Contenu

```
build.gradle                  Configuration ForgeGradle 6
gradle.properties             Toutes les infos du mod (source unique de verite)
settings.gradle
gradle/wrapper/               Config du wrapper Gradle (voir note plus bas)
src/main/java/…/ExampleMod.java   Classe principale annotee @Mod
src/main/java/…/Config.java       Exemple de config ForgeConfigSpec
src/main/resources/META-INF/mods.toml   Metadonnees (jetons ${...} remplis au build)
src/main/resources/pack.mcmeta
src/main/resources/assets/examplemod/lang/en_us.json
mod_config.json               Valeurs lues par l'initialiseur
configure_mod.py              L'initialiseur de projet
```

`mods.toml` et `pack.mcmeta` **ne contiennent aucune valeur en dur** : elles sont
injectees au build par `processResources` depuis `gradle.properties`.

## Creer un nouveau projet (recommande)

Le template n'est pas touche : il est copie puis configure dans le dossier cible.

```bash
python configure_mod.py --new ../CoolMod --interactive
```

ou sans questions :

```bash
python configure_mod.py --new ../CoolMod --set mod_id=coolmod --set mod_name="Cool Mod" --set mod_authors="Andra" --set mod_group_id=com.andra.coolmod --set main_class=CoolMod
```

Options : `--force` (dossier cible non vide autorise), `--config fichier.json`
(valeurs de depart). Le nouveau projet contient sa propre copie de
`configure_mod.py` et de `mod_config.json` pour etre reconfigure ensuite.

## Configurer le projet courant

1. Modifie `mod_config.json` :

```json
{
  "mod_id": "coolmod",
  "mod_name": "Cool Mod",
  "mod_description": "Un mod tres cool.",
  "mod_authors": "Andra",
  "mod_version": "1.0.0",
  "mod_group_id": "com.andra.coolmod",
  "main_class": "CoolMod"
}
```

2. Lance :

```bash
python configure_mod.py
```

Le script :
- met a jour `gradle.properties`
- renomme le package Java `com.example.examplemod` -> `com.andra.coolmod`
- renomme la classe `ExampleMod` -> `CoolMod` et la constante `MODID`
- renomme `assets/examplemod` -> `assets/coolmod` (idem `data/`)
- met a jour `rootProject.name` dans `settings.gradle`

### Autres usages

```bash
python configure_mod.py --show                       # config actuelle
python configure_mod.py --interactive                # questions une par une
python configure_mod.py --set mod_name="Ma Map" --set mod_authors="Andra"
python configure_mod.py --config prod.json           # autre fichier de config
python configure_mod.py --no-save                    # ne pas reecrire mod_config.json
```

Le script est **reexecutable** : il repart de l'etat courant (lu dans
`gradle.properties` + la classe `@Mod`) a chaque lancement.

> **Accents** : Gradle lit `gradle.properties` en ISO-8859-1. Pour eviter tout
> souci d'affichage en jeu, garde `mod_description` en ASCII (sans accents), ou
> passe par une cle de traduction dans le fichier de lang.

## Compiler le mod

```bash
./gradlew build          # jar dans build/libs/
./gradlew runClient      # lance un client de dev
./gradlew runData        # generation de ressources
```

> **Note wrapper Gradle** : ce template fournit `gradle-wrapper.properties` mais
> pas le binaire `gradle-wrapper.jar` ni `gradlew`/`gradlew.bat`. Pour les obtenir :
> - ouvre le dossier dans IntelliJ IDEA (il telecharge le wrapper tout seul), ou
> - si Gradle est installe : `gradle wrapper --gradle-version 8.1.1`, ou
> - copie ces 3 fichiers depuis le MDK officiel Forge 1.20.1
>   (<https://files.minecraftforge.net>).

## Prerequis

- JDK 17
- (recommande) IntelliJ IDEA avec le plugin Minecraft Development
