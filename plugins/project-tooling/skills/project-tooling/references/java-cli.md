# Java native CLI (GraalVM)

Adds to the baseline in `SKILL.md`.

## Choices

| Concern         | Choice                                                                |
|-----------------|-----------------------------------------------------------------------|
| JDK             | Newest LTS that GraalVM Native Image supports, a GraalVM distribution via mise; `options.release` set to it |
| Build           | Gradle (pinned in mise, **no wrapper**), Kotlin DSL, version catalog `gradle/libs.versions.toml` |
| Native image    | `org.graalvm.buildtools.native`                                       |
| Arg parsing     | Picocli + `picocli-codegen` annotation processor (`-Aproject=group/name`) generates reflection config |
| Commands        | one class per subcommand, `Callable<Integer>`, `mixinStandardHelpOptions = true`; print via `spec.commandLine().getOut()` |
| Null safety     | JSpecify `@NullMarked` in every `package-info.java`, enforced by NullAway (JSpecify mode, `OnlyNullMarked`) |
| Static analysis | Error Prone + Picnic error-prone-support (+ Refaster runner) + NullAway, `allSuggestionsAsWarnings`, `-Werror`, `-Xlint:all` |
| Formatting      | Spotless + **google-java-format 2.x** (not Palantir), version from the catalog; `removeUnusedImports`, `trimTrailingWhitespace`, `endWithNewline`; target `src/**/*.java` |
| Tests           | JUnit (latest major, BOM) + AssertJ; Hegel (`@HegelTest`) for property tests; `network`-tagged tests excluded from `test`, run by a `networkTest` task |
| Terminal        | JLine terminal with the FFM provider (no JNI); `--enable-native-access=ALL-UNNAMED` for run and tests |
| Version         | `version = providers.gradleProperty("releaseVersion").getOrElse("dev")`; a generated `BuildInfo.java` (works the same on JVM and native) |
| Data formats    | Jackson when needed; trim unused handlers with native-image substitutions if size matters |

## justfile additions

- `test` = `gradle test`; `network-test` = `gradle networkTest`
- `native` = `gradle nativeCompile`
- `run *args` = `gradle -q run --args="{{ args }}"`
- `fmt` = `gradle spotlessApply` + `just --fmt`; `fmt-check` = `gradle spotlessCheck` + `just --fmt --check`
- `ep-fix` = `gradle compileJava compileTestJava -Perrorprone.patch` then `gradle spotlessApply`
  (the build applies Error Prone's suggested fixes in place and turns `-Werror` off when the
  property is set)

## CI deviations from the baseline

- Native build/release jobs get the JDK from `graalvm/setup-graalvm` and use `mise-action`
  with `install_args: gradle` for Gradle only.
- `gradle/actions/setup-gradle` with `cache-provider: basic` (the MIT cache; the default is
  proprietary).
- Release passes `-PreleaseVersion="${VERSION#v}"` to `nativeCompile`.

## Gotchas

- Pin Error Prone to the version Picnic's release is built against; bump them together.
- Disable Refaster rules that introduce Guava when the project doesn't use it
  (`Refaster:NamePattern`), and the `StringSplitter` check.
- NullAway: `ExcludedFieldAnnotations` = `picocli.CommandLine.Spec,picocli.CommandLine.ParentCommand`;
  `HandleTestAssertionLibraries` for AssertJ.
- Anything reached by reflection or loaded as a resource outside picocli's generated config
  needs `src/main/resources/META-INF/native-image/...`. JVM tests won't catch it; check with
  `just native` and a run of the binary.
