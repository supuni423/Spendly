// Resizes the real icon artwork (extension/design/source-icon.png) down to
// the sizes Chrome needs, replacing the gradient placeholders.
//
// The source has a wide transparent margin, and even the illustration
// itself has the subject spread across a fairly wide composition (hat,
// shopping bags, coffee cup) — at 16-48px that reads as a blur, so this
// trims the margin, then crops in further on the top/center (face + hat,
// the part that actually reads at small sizes) before resizing.
//
// Run with: npm run generate:icons

import sharp from "sharp";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const extensionRoot = join(__dirname, "..");
const sourcePath = join(extensionRoot, "design", "source-icon.png");
const iconsDir = join(extensionRoot, "public", "icons");

const SIZES = [16, 48, 128];

const trimmed = await sharp(sourcePath).trim().toBuffer();
const { width, height } = await sharp(trimmed).metadata();

// A square crop anchored at the top, sized to most of the trimmed height —
// keeps the hat brim and face centered, crops out the widest reach of the
// bags/cup at the bottom corners.
const cropSide = Math.round(height * 0.9);
const cropLeft = Math.round((width - cropSide) / 2);

for (const size of SIZES) {
  const outPath = join(iconsDir, `icon${size}.png`);
  await sharp(trimmed)
    .extract({ left: cropLeft, top: 0, width: cropSide, height: cropSide })
    .resize(size, size, { fit: "cover" })
    .png()
    .toFile(outPath);
  console.log(`Wrote ${outPath}`);
}
