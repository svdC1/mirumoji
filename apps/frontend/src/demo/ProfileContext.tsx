/**
 * @packageDocumentation Demo variant of the profile context, aliased in only for
 * `--mode demo`. It pins the single fixed demo profile in localStorage before
 * anything reads it (both the context initializer and the fetch layer read
 * localStorage directly), then re-exports the real provider unchanged.
 */

if (typeof localStorage !== "undefined") {
    localStorage.setItem("currentProfileId", "demo");
}

export * from "@real/contexts/ProfileContext";
