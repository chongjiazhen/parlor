# Prior work on this exact setting - read before publishing

**AvalonBench: Evaluating LLMs Playing the Game of Avalon** - Light, Cai, Shen, Hu,
arXiv:2310.05036 (Oct 2023). A game environment for Avalon, rule-based baseline
bots, and ReAct-style LLM agents with per-role prompts. Reports ChatGPT in a good
role winning 22.2% against rule-based evil, versus 38.2% for the rule-based good
bot - i.e. LLMs UNDER-performing scripted baselines.

This is the nearest neighbour to parlor itself, not to any one of its notes, and a
public repo doing LLM-Avalon that does not mention it reads as either unaware or
evasive. Position honestly before flipping public: the overlap is the setting, and
the difference is what is being claimed. AvalonBench asks how well agents PLAY and
scores win rate against bots. parlor asks whether the harness is HONEST first -
information isolation as a machine-checked property (gate #1), a fallback rate
shipped beside every number and voiding above 10%, and criteria pre-committed
before the run. Those are complementary, and the win-rate comparison is not the
axis this repo competes on. Read the paper before writing the positioning line -
this summary is from its abstract and search results, not a full read.

Also surfaced and unread, plausibly relevant to `moral-framing.md`: **HARBOR:
Exploring Persona Dynamics in Multi-Agent Competition**, arXiv:2502.12149.

The deception/framing literature that bears on the theme experiment specifically -
Hagendorff, Park et al., Apollo, MACHIAVELLI, all verified with exact identifiers -
lives in `moral-framing.md` rather than here, because those constrain that
experiment's design rather than this repo's positioning.
