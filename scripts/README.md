# Rebuilding the profile animation

The banner is a visualization of a real, deterministic training run on a **synthetic two-moons dataset**. It is an educational illustration, not a benchmark or a claim about a deployed model.

- 64 labeled points; two inputs, eight tanh hidden units, one sigmoid output.
- Binary cross-entropy, full-batch gradient descent, 2,500 updates.
- Each displayed prediction field uses a saved training snapshot. No hand-animated decision boundary or interpolated weights.
- The lower diagram shows learned connection weights and activations for the highlighted sample. Bias parameters are part of the model but omitted from the diagram.
- The 18-second GIF repeats the same recorded training sequence. Playback uses a nonlinear time scale to make early learning visible; it does not represent training wall-clock speed.
- Colors, line widths and the sampled probability contour are presentation choices. The underlying predictions come from the model.

The model is intentionally small and follows the same educational idea as [TensorFlow Playground](https://playground.tensorflow.org/). It uses no TensorFlow dependency or copied implementation.

## Reproduce

Install Node.js and Python 3.10+, then:

```sh
python -m pip install -r scripts/requirements.txt
node scripts/verify_intro.cjs
python scripts/render_intro.py
```

Outputs: `assets/intro-light.gif`, `assets/intro-dark.gif`, their `-mobile` variants, and corresponding PNG stills. The README selects a mobile composition below 600px, a static image when the viewer requests reduced motion, and a palette matching their system color preference. Use `--layout desktop` or `--layout mobile` to rebuild one layout.

`verify_intro.cjs` checks the analytical gradient against finite differences, numerical stability, and convergence on the synthetic training points. Training-set accuracy does not imply generalization.

## Fonts

Space Grotesk, DM Sans and IBM Plex Mono are included under their SIL Open Font Licenses, alongside each font in `scripts/fonts/`. Originals: [Space Grotesk](https://github.com/google/fonts/tree/main/ofl/spacegrotesk), [DM Sans](https://github.com/google/fonts/tree/main/ofl/dmsans), [IBM Plex Mono](https://github.com/google/fonts/tree/main/ofl/ibmplexmono).

The GIF and PNG files are generated locally; the public profile does not depend on an external image-generation service or scheduled workflow.
