/**
 * @packageDocumentation Clears the installed service worker and its caches, the
 * escape hatch for a client stuck on a stale cached build.
 */

/**
 * Unregisters every service worker for this origin, deletes every Cache Storage
 * bucket, then reloads so the next load fetches a fresh index and assets.
 * Leaves localStorage intact so the profile and preferences survive.
 *
 * @returns {Promise<void>} Resolves after the caches are cleared, just before
 *   the reload.
 */
export async function resetAppData(): Promise<void> {
    if ("serviceWorker" in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        await Promise.all(registrations.map((r) => r.unregister()));
    }
    if ("caches" in window) {
        const keys = await caches.keys();
        await Promise.all(keys.map((k) => caches.delete(k)));
    }
    window.location.reload();
}
