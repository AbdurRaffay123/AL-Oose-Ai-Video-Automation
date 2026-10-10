# Character bible: what Jason checks first

Source of truth: Jason's official sheets in `Al-Oose-content/CONTENT/BBTB MARKETING/Character-Facials-sheet/`
(registered originals). Prompt descriptions: `official_identity` in `library/kling_prompts.yaml`.

**The two features Jason checks first. Get them right before anything else:**
1. **Billy's chin.** Nothing white under the beak.
2. **Saul's eyes.** Always enormous and round.

## Bad Billy (top-hat edition)
- **Identifiers:**
  - black top hat with one lightning-bolt crack that never overlaps the badge;
  - round silver badge with a white rim and a red script **B**;
  - monocle on his **LEFT** eye only;
  - long orange beak with **no teeth**;
  - teal moustache curls, the same spiral on both sides;
  - dark red vest, gold buckle, red-and-black striped shorts;
  - teal-and-red sneakers with pink-white soles;
  - three tail feathers.
- **Wings act as arms:** each ends in long yellow feather fingers (official turnaround, "wing / hand detail"). Never
  smooth human hands or fists.
- **Chin: white bleed.** The moustache curls enclose the sheet's white background, and an edge cleanup can't reach
  it. Every Billy cut-out must pass the **red-background test** before use (`./bbtb cutouts`; pre-flight blocks any
  cut-out that fails). Trapped white is cleared with `holes:` points in `library/cutlist.yaml`; real white details
  (eye whites, soles, badge rim, shirt) are approved with `keep_white:` points.
- **Energy:** a theatrical villain at about 65%. Wing gestures turn into hands on engines without a negative prompt,
  so keep the wings folded.

## Young Saul
- **Eyes are his defining feature.** Two ENORMOUS round pale blue-white eyes take up most of his head, with small
  black pupils. **If his eyes shrink, narrow or his head flattens, the shot is rejected.**
- **Other identifiers:**
  - a round, plump head;
  - small brown curved eyebrows;
  - a wide mouth with two buck teeth;
  - white four-finger gloves;
  - **no legs, feet or shoes**;
  - plum rings near the tapered tail.
- **The yellow ball** (with a cheeky face) appears only in the shots where he holds it. Never put it in his general
  description, or the AI adds it everywhere.
- **Every Saul shot needs:** the big-eye rule in the prompt (`{identity_young_saul}`), the `saul_eyes` negative set, and
  a large face close-up as reference 1 (`library/scene_references/saul/`). `./bbtb preprod` marks a Saul shot NO-GO
  without them.
