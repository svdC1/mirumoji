/**
 * @packageDocumentation
 * Tiny classNames joiner — filters out falsy values and joins with spaces.
 * Avoids pulling in a dependency for the common conditional-class pattern.
 */
export type ClassValue = string | number | false | null | undefined;

export function cn(...parts: ClassValue[]): string {
    return parts.filter(Boolean).join(" ");
}
