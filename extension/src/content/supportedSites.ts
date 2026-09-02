/**
 * Central registry of hostnames Spendly actively injects into.
 *
 * Per Section 8/13 of the project spec: a hostname is added here only once
 * its site-specific adapter exists AND (for external price sources) its
 * data-access permission status is upgraded to a confirmed state. Adding a
 * hostname here also requires adding a matching pattern to
 * manifest.json -> content_scripts[0].matches (or requesting it at runtime
 * via optional_host_permissions) — the manifest is intentionally not
 * wildcarded to <all_urls>.
 */
export const SUPPORTED_HOSTNAMES: readonly string[] = [
  // "store-a.example.com" — placeholder, see adapters/supported-site/StoreAAdapter.ts
];

export function isSupportedHostname(hostname: string): boolean {
  return SUPPORTED_HOSTNAMES.some((h) => hostname === h || hostname.endsWith(`.${h}`));
}
