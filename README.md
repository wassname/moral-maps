# moralmaps: moral and value maps for LLMs

What do an LLM's values look like next to ours? moralmaps puts models through human psychological and anthropological surveys, then plots their answers alongside human societies. We can compare models, or see where steering takes one.

## Are models moral aliens?

Start with the World Values Survey: its culture map compares societies by how traditional or secular they are, and how much they weigh survival over self-expression.

See <https://wassname.github.io/moral-maps/> for an interactive plot.

![World Values Survey map: models cluster toward self-expression (left) and secular-rational values (top), alongside human societies.](docs/img/wvs/wvs_map_iw.png)

The models cluster in the upper-left, around and above the Western societies. These are survey answers, not a test of how the models behave outside the survey.

> “The models’ answers, in English, on topics ranging from political petitions to God, suggest values that are different from those of most people. In fact, the models are often more extreme than the average respondent in every country included in the polling.”
>
> [The Economist, “AI models’ values are very different from most people’s”, 2026-06-25](https://www.economist.com/briefing/2026/06/25/ai-models-values-are-very-different-from-most-peoples)

See [all model results and their uncertainty](docs/img/wvs/wvs_model_ci.md) in one table.

## Can we steer these values?

The plots below follow one open model, Qwen3-4B. We use [steering-lite](https://github.com/wassname/steering-lite) to add an activation vector built from authority-respecting versus authority-disregarding personas, without retraining. Red means more Authority, blue means less, and black is the base model.

These plots read answer probabilities. The closed-model WVS map above uses repeated ratings instead.

### Value maps

Each map shows two survey axes, human societies as coloured regions, and the model's path under steering.

![MFQ-2 map: the Authority steer moves Qwen3-4B from the equality side toward binding values, inside the African-Islamic region.](docs/img/showcase/mfq2/map_value.png)

The Moral Foundations Questionnaire (MFQ-2) measures concerns such as care, equality, loyalty, and authority. Here, pushing toward Authority moves the model from individual-first toward group-first values, across much of the human map.

![Big Five map: the model stays on the reserved side, but moves visibly on the stable-to-volatile axis.](docs/img/showcase/big5/map_value.png)

Personality changes too. The model stays more reserved than the plotted societies, but the vertical movement is visible. The individual traits below show which scores changed.

![Humor Styles map: steering shifts the model within the maladaptive side; human regions overlap heavily.](docs/img/showcase/humor_styles/map_value.png)

Humor style separates these societies poorly: their regions overlap heavily. A position on this map therefore tells us less about cultural similarity.

### One factor at a time

The grey dots show human references, the black dot the base model, and the blue-to-red sweep the steer. Survey plots use country means; the moral vignettes use one pooled human reference.

![Moral-vignette range plot: Authority has the largest shift, while Care and Liberty also change. Values are standardized across foundations.](docs/img/showcase/mfv/range.png)

Moral-foundation vignettes (MFV) ask which kind of wrong a short story describes, such as cruelty, cheating, or defiance of authority. Authority moves most here. We use a pooled human reference because the available country norms do not support a reliable country comparison ([measurement note](src/moralmaps/data/human/MFV_country_norms_NOTE.md)).

![MFQ-2 range plot: Authority, Care, Proportionality, Loyalty, and Purity rise; Equality changes little.](docs/img/showcase/mfq2/range.png)

![Big Five range plot: Agreeableness and Conscientiousness rise; Neuroticism stays near 3.0.](docs/img/showcase/big5/range.png)

![Humor Styles range plot: Affiliative humor rises, while the other styles move less.](docs/img/showcase/humor_styles/range.png)

The intended value moves, but so do other answers. This is why we need to measure side effects as well as the target.

## Measurement

The maps use human-comparable survey scores. For local models, we read answer-token probabilities; for APIs without logprobs, we use repeated ratings. We check probability mass on valid answers so broken answer formatting is not mistaken for a value change.

For steering comparisons, we also want a score that considers both intended changes and side effects. The existing [metric](src/moralmaps/metrics.py) is `sel_gated = (on - 0.1 * off) * coh²`: intended logprob movement minus a smaller penalty for other movement, multiplied by a valid-answer mass check. `si_flips` checks whether the model's chosen answers changed. Logprob movement can be visible even when chosen answers stay the same.

When we steer a concept, we want the relevant answers to change without changing unrelated answers. So we reward movement in the intended direction and subtract a smaller penalty for side effects. We use logprobs because they show small changes even when the model still chooses the same answer.

A possible replacement is steering F-beta, which treats desired changes as true positives and unwanted changes as false positives. It is still a proposal; the plots and existing results have not been rescored.

## Install and use

```bash
uv pip install "moral-maps[maps] @ git+https://github.com/wassname/moral-maps"
```

Ask a local model the MFQ-2 survey and the classic moral vignettes:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from moralmaps import administer, evaluate, get_instrument, load_vignettes

tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-4B").cuda()

survey = administer(model, tok, get_instrument("mfq2"))
print(survey["profile"])
print(survey["mean_pmass_allowed"])

vignettes = evaluate(model, tok, vignettes=load_vignettes("classic"))
print(vignettes["profile"])
```

The bundled surveys are [MFQ-2](src/moralmaps/data/surveys/mfq2/forward.json) (36 items), [Big Five](src/moralmaps/data/surveys/big5/questionnaire.json) (50), [16PF](src/moralmaps/data/surveys/16pf/questionnaire.json) (162), and [Humor Styles](src/moralmaps/data/surveys/humor_styles/questionnaire.json) (32). Each includes [human reference data](src/moralmaps/data/human). Survey items use forward, inverted, and negated frames, mapped back to the same scale before averaging.

MFV has 132 vignettes in `classic`, `scifi`, and `ai-actor` versions, each from self and other perspectives. The rewritten versions inherit the classic human labels. WVS questions are loaded from GlobalOpinionQA at runtime.

<details>
<summary>Development and plot reproduction</summary>

```bash
git clone https://github.com/wassname/moral-maps
cd moral-maps
uv sync --extra maps --dev
just smoke

uv run python scripts/plot_steer_showcase.py \
  --run-dir ../steering-lite/outputs/20260630T222000Z_pure_authority_mundane15_pca_readme_mfv_mfq2_humor_big5_n8 \
  --out docs/img/showcase \
  --vec-label "Authority steer, PCA (+c = more Authority)" \
  --coherence-frac 0.99 \
  --contrast-frac 0.000001 \
  --margin-frac 0.50
```

Plotting requires the saved steering-lite run. It keeps only coefficients where every plotted dataset retains the requested fraction of base answer mass, survey contrast, and vignette answer margin. See [the plotting script](scripts/plot_steer_showcase.py).

</details>

These maps compare survey responses. For behaviour-heavy moral evaluations, see [Machiavelli](https://huggingface.co/datasets/wassname/machiavelli) and [AIRiskDilemmas](https://huggingface.co/datasets/kellycyy/AIRiskDilemmas).

## Citation

```bibtex
@misc{clark2026moralmaps,
  title = {moralmaps: moral and value maps for LLMs},
  author = {Michael Clark},
  year = {2026},
  url = {https://github.com/wassname/moral-maps/}
}
```

<!-- PI/gpt-6-astra: shortened from the existing README and wassname's steering-score explanation; results and plot files retained. -->
