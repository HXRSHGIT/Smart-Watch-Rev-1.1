# Stealth Dead-Front Window

Brief §2: "Basic Stealth: a small OLED hidden behind a matte dead-front window. The front appears dark when the display is off."
Brief §4.4: "The Stealth cover must be evaluated for off-state appearance, brightness loss, contrast, viewing angle and outdoor readability."

---

## 1. The trade

A dead-front hides the display by **absorbing most of the light that goes through it**:

- Room light has to pass through the cover **twice** (in, bounce off the panel, out) before you see the panel underneath.
- The display's own light passes through **once**.

With cover transmission **T**:

- light from the display reaching the eye ∝ **T**
- light from a hidden panel or PCB reaching the eye ∝ **T² × panel reflectance**

So halving T halves the display's brightness but cuts the visibility of the hidden parts by four. That's why dead-fronts work, and also why they cost brightness.

| T | Display seen at | Hidden panel visible at (relative) | Look when off |
|---|---|---|---|
| 90 % (clear, "Basic OLED") | 90 % | 81 % | panel and its frame visible |
| 40 % | 40 % | 16 % | grey, faint outline in bright light |
| 25 % | 25 % | 6 % | dark, outline only at grazing angles |
| 15 % | 15 % | 2 % | black |

**Starting point:** T ≈ **20–30 %** in the visible band (estimate; sample and judge by eye). That puts a 180 cd/m² panel at **≈ 36–54 cd/m²** through the cover.

## 2. How to build it

| Method | How | Pros | Cons |
|---|---|---|---|
| **Tinted (smoked) PMMA or PC window** | dyed resin, 0.5–1.0 mm | cheap, mouldable, uniform | PMMA scratches. PC needs a hard coat |
| **Clear cover + semi-transparent "dead-front" ink** printed on the back | screen-print or in-mould decoration | matches a painted housing, crisp border | ink uniformity and haze drive quality |
| **Clear glass + neutral-density film** | optically clear adhesive lamination | glass is scratch-proof | stack thickness, delamination with sweat |
| **Matte / anti-glare top surface** | etched or textured | reduces glare, looks "matte" (brief says matte) | haze blurs 0.153 mm pixels if the texture is too coarse |
| **AR coating** (top) | thin-film | cuts front reflection from ≈ 4 % to < 1 % | cost, durability on a wrist |

**Also needed:** black mask or ink around the active area, an opaque gasket between the panel and the cover, and a black OLED frame/FPC so no edge light leaks.

## 3. Outdoor readability — numbers

Reflected luminance from a surface: L ≈ E × R / π (Lambertian approximation).

| Ambient | Illuminance E | Front reflection R | Glare L | Display through T = 25 % | Display through T = 90 % |
|---|---|---|---|---|---|
| Office | 500 lx | 4 % (bare plastic) | 6 cd/m² | 45 cd/m² → readable | 160 → easy |
| Shade outdoors | 10,000 lx | 4 % | 127 cd/m² | 45 → **unreadable** | 160 → marginal |
| Shade + AR coat | 10,000 lx | 1 % | 32 cd/m² | 45 → marginal | 160 → readable |
| Direct sun + AR | 70,000 lx | 1 % | 223 cd/m² | 45 → unreadable | 160 → poor |

Rough rule: legible text needs display luminance ≥ the glare luminance.

**Conclusions:**

- **Stealth can't be read in direct sun** with any dead-front. The user has to shade the band, the same as many fitness bands. **Tell the client** and write it in the spec.
- **An AR coating is the biggest single improvement** (≈ 4× less glare), more than any brightness tweak.
- A **matte** top cuts specular glare but adds diffuse scatter, which hurts contrast in bright light. Choose a fine texture and test it.
- For outdoor use, the Basic OLED (clear window) variant is the one to recommend.

## 4. Off-state appearance and viewing angle

- **Off-state:** measure L\* (CIELAB lightness) of the window over the panel, and next to it over the black frame. A ΔE below ~1–2 means the outline is invisible in normal light. That threshold is a common rule of thumb; agree it with the industrial designer.
- **Viewing angle:** a tinted window's path length grows with angle (1/cos θ). At 45° the effective T drops from 25 % to ≈ 14 % (T^(1/cos θ)), so the display dims off-axis. **The OLED itself is wide-angle; the cover sets the limit.**
- **Haze:** keep it below about 5–10 % (target, verify) or pixel edges smear. At 0.153 mm pixels that's visible.

## 5. Measurement plan (§13 "Display readability, dead-front behavior")

1. Get 5–8 window samples:
   - tinted PMMA at T ≈ 15 / 25 / 40 %;
   - ink-printed PC at two densities;
   - each with and without AR, and matte and gloss.
2. Measure on each:
   - **T(λ)** with a spectrophotometer (380–780 nm), and check it's neutral (no colour cast on white OLED);
   - **haze** (haze meter, or ASTM D1003 style);
   - **luminance** of a full-white 64×32 frame through the window (luminance meter at 0° and 45°);
   - **off-state L\* and ΔE** over panel vs frame, under a D65 booth;
   - **readability panel:** 5 people read 5 icons at 500 / 10,000 lx and in sun, then score it.
3. Pick one window for Stealth and one for Basic OLED. The PCB stays identical, as the brief requires.

## 6. Pairing digits through the Stealth window

Passkey pairing (mcu-ble BLE_SECURITY_DFU §1.2) shows 6 digits. Indoors, at T = 25 % and 45 cd/m², that's readable.

Keep the NFCT tap-to-pair as a backup in case the industrial design pushes T lower.
