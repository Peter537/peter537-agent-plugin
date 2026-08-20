declare const input: unknown;

// @ts-expect-error: fixture verifies the legacy compiler compatibility branch
const legacyValue: string = input;

export { legacyValue };
