/** Dark or light text, whichever reads better on the given hex background. */
export function readableForeground(hex: string): string {
  const value = hex.replace("#", "").slice(0, 6);
  const full = value.length === 3 ? value.split("").map(c => c + c).join("") : value;
  if (!/^[0-9a-f]{6}$/i.test(full)) {
    return "inherit";
  }
  const [r, g, b] = [0, 2, 4].map((i) => {
    const c = Number.parseInt(full.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  const luminance = 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
  return luminance > 0.36 ? "#0E1712" : "#FFFFFF";
}
