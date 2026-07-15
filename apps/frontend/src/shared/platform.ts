/**
 * @packageDocumentation Platform detection for the few places that must branch
 * on the host OS rather than the viewport. The viewport-based checks live in
 * shared/hooks/useMediaQuery.
 */

/**
 * Detects iOS (iPhone, iPad, iPod), including iPadOS 13+, which reports a
 * desktop Safari user agent and is only distinguishable by touch support.
 *
 * @returns {boolean} True on an iOS or iPadOS device.
 */
export function isIOS(): boolean {
    if (typeof navigator === "undefined") return false;
    const legacy = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const iPadOS13 = navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1;
    return legacy || iPadOS13;
}
